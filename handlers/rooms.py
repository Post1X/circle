import traceback
import socketio
from typing import Any, Dict, Optional
from decimal import Decimal
from sqlalchemy import select
from uuid import UUID
from game import Game, get_game, close_game, create_game, set_changes
import asyncio
from decimal import Decimal

# from bd.database import get_session
from bd.database import async_session_maker as get_session
from bd.models import GameRoom
from bd.models import User
from bd.actions.user import UserActions
from bd.actions.balance import BalanceActions

from schemas.rooms import (
    AuthenticateRequest,
    CreateRoomRequest,
    JoinRoomRequest,
    LeaveRoomRequest,
)
from schemas.leaderboard import (
    LeaderboardData, 
    CurrentPlayer, 
    # PlayerPosition,
    # PlayerColor,
    GamePhaseInfo,
    EarlyExit,
    SuperExit,
    Finalist,
)
from bd.actions.room import RoomActions
from servises.player_counter import player_counter_service


sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", logger=True, engineio_logger=True
)


active_connections: Dict[str, Dict[str, Any]] = {}
players_in_room: Dict[str, list] = {} # room_id: [{"username": "", "user_id": ""}]


@sio.event
async def get_players(sid: str, room_id) -> None:
    game = await get_game(room_id)
    if game:
        await sio.emit("all_players", game.players)


@sio.event
async def connect(
    sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]]
) -> None:
    """
    Обработчик подключения клиента к Socket.IO серверу.

    Args:
        sid: Session ID клиента
        environ: Переменные окружения запроса
        auth: Данные аутентификации (опционально)

    Emits:
        connected: Отправляет данные с session ID клиента
    """
    print(f"Клиент подключился: {sid}")
    active_connections[sid] = {"user_id": None, "room_id": None, "authenticated": False}

    await sio.emit("connected", {"sid": sid}, room=sid)


@sio.event
async def disconnect(sid: str) -> None:
    """
    Обработчик отключения клиента от Socket.IO сервера.

    Args:
        sid: Session ID клиента

    Side Effects:
        - Удаляет клиента из активных подключений
        - Если клиент был в комнате, уведомляет других участников
        - Уменьшает счетчик активных игроков
    """
    print(f"Клиент отключился: {sid}")
    if sid in active_connections:
        user_id = active_connections[sid].get("user_id")
        if user_id:
            await player_counter_service.decrement_real_count(str(user_id))

        room_id = str(active_connections[sid].get("room_id"))
        if room_id:
            await leave_room_socket(sid, room_id)
        del active_connections[sid]


@sio.event
async def authenticate(sid: str, data: Dict[str, Any]) -> None:
    """
    Аутентификация пользователя по user_id.

    Args:
        sid: Session ID клиента
        data: Словарь с данными аутентификации (AuthenticateRequest)
            - user_id: UUID пользователя

    Emits:
        authenticated: Данные пользователя при успешной аутентификации
        auth_error: Данные ошибки при ошибке аутентификации
    """
    try:
        # Валидация входных данных
        request = AuthenticateRequest(**data)
        user_id = request.user_id

        async with get_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                await sio.emit("auth_error", {"message": "User not found"}, room=sid)
                return

            # Обновляем информацию о подключении
            active_connections[sid]["user_id"] = user_id
            active_connections[sid]["authenticated"] = True
            active_connections[sid]["username"] = user.username


            # Увеличиваем счетчик активных игроков
            await player_counter_service.increment_real_count(str(user_id))

            await sio.emit(
                "authenticated",
                {"user_id": user_id, "wallet_address": user.wallet_address, "username": user.username},
                room=sid,
            )

    except Exception as e:
        await sio.emit("auth_error", {"message": str(e)}, room=sid)


@sio.event
async def create_room(sid: str, data: Dict[str, Any]) -> None:
    """
    Создание новой игровой комнаты (требует аутентификации).

    Args:
        sid: Session ID клиента
        data: Словарь с параметрами комнаты (CreateRoomRequest)
            - entry_fee: Вступительный взнос (по умолчанию 0)
            - min_players: Минимальное количество игроков (по умолчанию 20)
            - max_players: Максимальное количество игроков (по умолчанию 100)

    Emits:
        room_created: Данные созданной комнаты при успешном создании
        error: Данные ошибки при ошибке
    """
    try:
        if not active_connections[sid]["authenticated"]:
            await sio.emit("error", {"message": "Authentication required"}, room=sid)
            return
        request = CreateRoomRequest(**data)
        async with get_session() as session:
            actions = RoomActions(session)
            new_room = await actions.create_room(
                entry_fee=request.entry_fee,
                min_players=request.min_players,
                max_players=request.max_players,
            )
            await sio.emit(
                "room_created",
                {
                    "room_id": str(new_room.room_id),
                    "entry_fee": new_room.entry_fee,
                    "min_players": new_room.min_players,
                    "max_players": new_room.max_players,
                    "status": new_room.status,
                    "created_at": new_room.created_at.isoformat(),
                },
            )
    except Exception as e:
        await sio.emit("error", {"message": str(e) + "createroom"}, room=sid)


@sio.event
async def join_game(sid: str, data: Dict[str, Any]) -> None:
    """
    Автоматическое подключение к игре:
    - ищем подходящую комнату в статусе waiting;
    - если нет — создаем новую;
    - затем подключаем игрока через _join_room_socket.

    Args:
        sid: Session ID клиента
        data: Параметры матчинга (опционально):
            - entry_fee: вступительный взнос (по умолчанию 0)
            - min_players: минимальное число игроков (по умолчанию 20)
            - max_players: максимальное число игроков (по умолчанию 100)
    """
    try:
        # Debug-событие, чтобы на клиенте было видно, что join_game реально дошёл до сервера
        await sio.emit("join_game_received", {"sid": sid, "data": data}, room=sid)
        if not active_connections[sid]["authenticated"]:
            await sio.emit("error", {"message": "Authentication required"}, room=sid)
            return

        entry_fee = int(data.get("entry_fee", 0))
        # Временно ставим минимальное количество игроков равным 1,
        # чтобы игра могла стартовать сразу.
        min_players = int(data.get("min_players", 1))
        max_players = int(data.get("max_players", 100))

        async with get_session() as session:
            actions = RoomActions(session)

            # Пытаемся найти уже существующую подходящую комнату
            room = await actions.get_free_room(
                entry_fee=entry_fee,
                min_players=min_players,
                max_players=max_players,
            )

            # Если подходящей комнаты нет — создаем новую
            if not room:
                room = await actions.create_room(
                    entry_fee=entry_fee,
                    min_players=min_players,
                    max_players=max_players,
                )

            # Дополнительное debug-сообщение, какую именно комнату выбрали/создали
            await sio.emit(
                "join_game_room",
                {
                    "room_id": str(room.room_id),
                    "entry_fee": room.entry_fee,
                    "min_players": room.min_players,
                    "max_players": room.max_players,
                    "players": room.players,
                    "status": room.status,
                },
                room=sid,
            )

            await _join_room_socket(sid, str(room.room_id))

    except Exception as e:
        await sio.emit("error", {"message": str(e) + " join_game"}, room=sid)


@sio.event
async def join_room(sid: str, data: Dict[str, Any]) -> None:
    """
    Присоединение к существующей игровой комнате (требует аутентификации).

    Args:
        sid: Session ID клиента
        data: Словарь с данными для присоединения (JoinRoomRequest)
            - room_id: UUID комнаты для присоединения

    Emits:
        joined_room: Данные об успешном присоединении
        error: Данные ошибки при ошибке
    """
    try:
        if not active_connections[sid]["authenticated"]:
            await sio.emit("error", {"message": "Authentication required"}, room=sid)
            return

        # Валидация входных данных
        request = JoinRoomRequest(**data)
        room_id = request.room_id
        if players_in_room.get(str(room_id), None):
            # players_in_room[room_id] = [active_connections[sid]["user_id"], ]

            already_in_room = any(p["user_id"] == active_connections[sid]["user_id"] for p in players_in_room[str(room_id)])

            if not already_in_room:
                players_in_room[str(room_id)].append({
                    "user_id": active_connections[sid]["user_id"],
                    "username": active_connections[sid]["username"]
                })
        else:
            players_in_room[str(room_id)] = [{
                "user_id": active_connections[sid]["user_id"],
                "username": active_connections[sid]["username"]
            }, ]
            #players_in_room[room_id].append(active_connections[sid]["user_id"])


        await _join_room_socket(sid, room_id)
                
    except Exception as e:
        await sio.emit("error", {"message": str(e) + "joinroom"}, room=sid)


@sio.event
async def leave_room(sid: str, data: Dict[str, Any]) -> None:
    """
    Выход из игровой комнаты.

    Args:
        sid: Session ID клиента
        data: Словарь с данными для выхода (LeaveRoomRequest)
            - room_id: UUID комнаты для выхода

    Emits:
        left_room: Данные об успешном выходе
        error: Данные ошибки при ошибке
    """
    try:
        # Валидация входных данных
        request = LeaveRoomRequest(**data)
        room_id = request.room_id

        await leave_room_socket(sid, room_id)

    except Exception as e:
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def get_rooms(sid: str) -> None:
    """
    Получение списка всех доступных игровых комнат.

    Args:
        sid: Session ID клиента

    Emits:
        rooms_list: Список всех комнат
        error: Данные ошибки при ошибке
    """
    try:
        async with get_session() as session:
            actions = RoomActions(session)
            rooms = await actions.get_all_rooms()
            rooms_data = [
                {
                    "room_id": str(room.room_id),
                    "entry_fee": room.entry_fee,
                    "min_players": room.min_players,
                    "max_players": room.max_players,
                    "status": room.status,
                    "created_at": room.created_at.isoformat(),
                }
                for room in rooms
            ]
            await sio.emit("rooms_list", {"rooms": rooms_data}, room=sid)
    except Exception as e:
        await sio.emit("error", {"message": str(e) + "get_rooms"}, room=sid)


async def _join_room_socket(sid: str, room_id: str) -> None:
    """
    Вспомогательная функция для присоединения к Socket.IO комнате.

    Args:
        sid: Session ID клиента
        room_id: UUID комнаты для присоединения

    Emits:
        joined_room: Данные об успешном присоединении
        player_joined: Данные о присоединении игрока для других участников
        error: Данные ошибки при ошибке
    """
    try:
        async with get_session() as session:
            actions = RoomActions(session)
            room = await actions.get_room_by_id(room_id)
            if not room:
                await sio.emit("error", {"message": "Room not found"}, room=sid)
                return
            if room.status != "waiting":
                await sio.emit(
                    "error", {"message": "Room is not accepting players"}, room=sid
                )
                return

            if room.entry_fee and room.entry_fee > 0:
                balance_actions = BalanceActions(session)
                ok = await balance_actions.debit_for_entry_fee(
                    UUID(str(active_connections[sid]["user_id"])),
                    Decimal(str(room.entry_fee)),
                )
                if not ok:
                    await sio.emit(
                        "error",
                        {"message": "Insufficient balance for entry fee"},
                        room=sid,
                    )

                    return

            await sio.enter_room(sid, room_id)
            await actions.add_player(room_id)
            active_connections[sid]["room_id"] = room_id
            await sio.emit(
                "player_joined",
                # {"user_id": active_connections[sid]["user_id"], "room_id": room_id},
                {"players": players_in_room[str(room_id)], "room_id": room_id},

                room=room_id,
            )
            need_start_game = await actions.check_start_game(room_id)
            await sio.emit(
                "joined_room",
                {
                    "players": players_in_room[str(room_id)],
                    "room_id": room_id, 
                    "message": "Successfully joined room",
                    "time_to_start": 30 if need_start_game else None
                },
                room=sid,
            )
            if need_start_game:
                await sio.emit(
                    "game_started",
                    {"time_to_start": 30},
                    room=room_id,
                )
                await asyncio.sleep(30)
                await game_loop(room_id)

    except Exception as e:
        await sio.emit("error", {"message": str(e) + "join from socket"}, room=sid)


async def leave_room_socket(sid: str, room_id: str) -> None:
    """
    Вспомогательная функция для выхода из Socket.IO комнаты.

    Args:
        sid: Session ID клиента
        room_id: UUID комнаты для выхода

    Emits:
        left_room: Данные об успешном выходе
        player_left: Данные о выходе игрока для других участников
        error: Данные ошибки при ошибке
    """
    try:
        # Покидаем Socket.IO комнату
        await sio.leave_room(sid, room_id)

        # Уведомляем всех в комнате о выходе участника
        await sio.emit(
            "player_left",
            {"user_id": active_connections[sid]["user_id"], "room_id": room_id},
            room=room_id,
        )

        # Очищаем информацию о комнате
        active_connections[sid]["room_id"] = None

        # Отправляем подтверждение клиенту
        await sio.emit(
            "left_room",
            {"room_id": room_id, "message": "Successfully left room"},
            room=sid,
        )

    except Exception as e:
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.event
async def move(sid: str, data: Dict[str, Any]) -> None:
    """
    Игрок отправляет своё движение (dx, dy).
    """
    room_id = str(active_connections[sid].get("room_id"))
    user_id = active_connections[sid].get("user_id")
    game = await get_game(room_id)

    if not room_id or not user_id or not game:
        return
    dx = data.get("dx", 0)
    dy = data.get("dy", 0)
    game.move_player(str(user_id), dx, dy)


@sio.event
async def activate_skill(sid: str, data: Dict[str, Any]) -> None:
    """
    Игрок активирует навык.

    Args:
        sid: Session ID клиента
        data: Данные навыка
            - skill_type: тип навыка ("teleport", "shield", "boost")

    Emits:
        skill_activated: Подтверждение активации навыка
        skill_error: Ошибка активации навыка
        balance_updated: Обновленный баланс игрока
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))
        user_id = active_connections[sid].get("user_id")
        game = await get_game(room_id)

        if not room_id or not user_id or not game:
            await sio.emit("skill_error", {"message": "Not in game"}, room=sid)
            return

        skill_type = data.get("skill_type")
        if skill_type not in ["teleport", "shield", "boost"]:
            await sio.emit("skill_error", {"message": "Invalid skill type"}, room=sid)
            return

        # Проверяем "последний шанс" для игроков с низким балансом в супер игре
        if game.game_phase == "super":
            player = game.players.get(str(user_id))
            # if player and player.mass * 0.01 < 5:  # Меньше $5
            if player and player.get_radius() <= 5:  # Меньше $5
                last_chance_success = game.check_last_chance(str(user_id))
                if last_chance_success:
                    await sio.emit(
                        "last_chance_activated",
                        {
                            "player_id": str(user_id),
                            "skill_type": skill_type,
                            "skill_costs_increased": game.skill_costs_increased,
                        },
                        room=room_id,
                    )
                    return

        # Обычная активация навыка
        success, message = game.activate_skill(str(user_id), skill_type)

        if success:
            # Получаем стоимость навыка
            skill_cost = game.get_skill_cost(str(user_id), skill_type)

            # Получаем игрока для отправки актуальных cooldowns
            player = game.players.get(str(user_id))
            cooldowns = None
            if player:
                from game.models import Cooldowns
                cooldowns = Cooldowns(
                    teleport=float(round(max(0.0, player.teleport_cooldown), 1)),
                    shield=float(round(max(0.0, player.shield_cooldown), 1)),
                    boost=float(round(max(0.0, player.boost_cooldown), 1)),
                )

            await sio.emit(
                "skill_activated",
                {
                    "player_id": str(user_id),
                    "skill_type": skill_type,
                    "skill_cost": skill_cost,
                    "skill_costs_increased": game.skill_costs_increased,
                    "cooldowns": cooldowns.model_dump() if cooldowns else None,
                },
                room=sid,
            )

            # Отправляем обновленное состояние игры сразу после активации скилла
            # чтобы клиент получил актуальные cooldowns без задержки
            game_state = game.get_state().model_dump()
            await sio.emit("game_state", game_state, room=sid)

            # Уведомляем других игроков
            await sio.emit(
                "player_used_skill",
                {"player_id": str(user_id), "skill_type": skill_type},
                room=room_id,
            )
        else:
            await sio.emit("skill_error", {"message": message}, room=sid)
        await set_changes(room_id, game)

    except Exception as e:
        await sio.emit("skill_error", {"message": str(e)}, room=sid)


@sio.event
async def get_bonus_zones_info(sid: str) -> None:
    """
    Получить информацию о бонусных зонах.

    Args:
        sid: Session ID клиента

    Emits:
        bonus_zones_info: Информация о бонусных зонах
        error: Данные ошибки при ошибке
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))
        game = await get_game(room_id)

        if not room_id or not game:
            await sio.emit("error", {"message": "Not in game"}, room=sid)
            return

        bonus_zones_info = {
            "active_zones": [
                {
                    "x": zone.x,
                    "y": zone.y,
                    "radius": zone.radius,
                    "multiplier": zone.multiplier,
                    "remaining_time": zone.get_remaining_time(),
                    "funds_collected": zone.funds_collected,
                    "max_funds": zone.funds_generated * zone.multiplier,
                    "is_active": zone.is_active,
                }
                for zone in game.bonus_zones
            ],
            "zone_fund": game.zone_fund,
            "bonus_fund": game.bonus_fund,
            "time_to_next_zone": game.get_time_to_next_bonus_zone(),
            "zone_settings": {
                "spawn_interval_seconds": game.bonus_zone_interval,
                "zone_duration_seconds": 30.0,
                "funds_per_zone": 20,
            },
        }

        await sio.emit("bonus_zones_info", bonus_zones_info, room=sid)

    except Exception as e:
        await sio.emit(
            "error", {"message": f"Error getting bonus zones info: {str(e)}"}, room=sid
        )


# TODO:
@sio.event
async def get_game_phase(sid: str) -> None:
    """
    Получает информацию о текущей фазе игры.

    Args:
        sid: Session ID клиента

    Emits:
        game_phase_info: Информация о текущей фазе игры
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))
        user_id = active_connections[sid].get("user_id")
        game = await get_game(room_id)

        if not room_id or not user_id or not game:
            await sio.emit("game_phase_error", {"message": "Not in game"}, room=sid)
            return

        phase_info = game.get_game_phase_info()

        await sio.emit("game_phase_info", phase_info, room=sid)

    except Exception as e:
        await sio.emit("game_phase_error", {"message": str(e)}, room=sid)


# TODO:
@sio.event
async def submit_vote(sid: str, data: Dict[str, Any]) -> None:
    """
    Отправляет голос в топ-10.

    Args:
        sid: Session ID клиента
        data: Данные голоса
            - vote: "exit" или "super"

    Emits:
        vote_submitted: Подтверждение отправки голоса
        vote_error: Ошибка отправки голоса
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))
        user_id = active_connections[sid].get("user_id")
        game = await get_game(room_id)

        if not room_id or not user_id or not game:
            await sio.emit("vote_error", {"message": "Not in game"}, room=sid)
            return

        vote = data.get("vote")
        if vote not in ["exit", "super"]:
            await sio.emit("vote_error", {"message": "Invalid vote"}, room=sid)
            return

        success = game.submit_vote(str(user_id), vote)

        if success:
            await sio.emit(
                "vote_submitted",
                {
                    "vote": vote,
                    "voting_time_remaining": game.get_voting_time_remaining(),
                },
                room=sid,
            )

            # Уведомляем всех игроков о новом голосе
            await sio.emit(
                "vote_update",
                {
                    "votes_submitted": len(game.votes),
                    "votes_exit": sum(1 for v in game.votes.values() if v == "exit"),
                    "votes_super": sum(1 for v in game.votes.values() if v == "super"),
                },
                room=room_id,
            )
        else:
            await sio.emit("vote_error", {"message": "Cannot submit vote"}, room=sid)

    except Exception as e:
        await sio.emit("vote_error", {"message": str(e)}, room=sid)


@sio.event
async def exit_game(sid: str, data: Dict[str, Any]) -> None:
    """
    Игрок выходит из игры.

    Args:
        sid: Session ID клиента
        data: Данные выхода
            - exit_type: "early" (до топ-10), "super" (из супер игры)

    Emits:
        player_exited: Подтверждение выхода игрока
        exit_error: Ошибка выхода
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))
        user_id = active_connections[sid].get("user_id")
        game = await get_game(room_id)

        if not room_id or not user_id or not game:
            await sio.emit("exit_error", {"message": "Not in game"}, room=sid)
            return

        exit_type = data.get("exit_type")

        if exit_type == "early" and game.game_phase == "start":
            # Ранний выход (50% от собранного)
            game.process_early_exit(str(user_id))
            amount = game.early_exits.get(str(user_id), 0)

            async with get_session() as session:
                actions = BalanceActions(session)
                try:
                    await actions.credit_winnings(UUID(str(user_id)), Decimal(str(amount)))
                except Exception:
                    pass

            await sio.emit(
                "player_exited",
                {
                    "player_id": str(user_id),
                    "exit_type": "early",
                    "winnings": game.early_exits.get(str(user_id), 0),
                },
                room=room_id,
            )

        elif exit_type == "super" and game.game_phase == "super":
            # Выход из супер игры (25% от собранного)
            game.process_super_exit(str(user_id))
            amount = game.super_exits.get(str(user_id), 0)

            async with get_session() as session:
                actions = BalanceActions(session)
                try:
                    await actions.credit_winnings(UUID(str(user_id)), Decimal(str(amount)))
                except Exception:
                    pass

            await sio.emit(
                "player_exited",
                {
                    "player_id": str(user_id),
                    "exit_type": "super",
                    "winnings": game.super_exits.get(str(user_id), 0),
                },
                room=room_id,
            )

        else:
            await sio.emit(
                "exit_error", {"message": "Invalid exit type or phase"}, room=sid
            )
            return

        # Удаляем игрока из комнаты
        await leave_room_socket(sid, room_id)

    except Exception as e:
        await sio.emit("exit_error", {"message": str(e)}, room=sid)


@sio.event
async def request_last_chance(sid: str) -> None:
    """
    Запрашивает "последний шанс" в супер игре.

    Args:
        sid: Session ID клиента

    Emits:
        last_chance_activated: Подтверждение активации "последнего шанса"
        last_chance_error: Ошибка активации
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))
        user_id = active_connections[sid].get("user_id")
        game = await get_game(room_id)

        if not room_id or not user_id or not game:
            await sio.emit("last_chance_error", {"message": "Not in game"}, room=sid)
            return

        success = game.check_last_chance(str(user_id))

        if success:
            await sio.emit(
                "last_chance_activated",
                {
                    "player_id": str(user_id),
                    "skill_costs_increased": game.skill_costs_increased,
                },
                room=room_id,
            )
        else:
            await sio.emit(
                "last_chance_error",
                {"message": "Cannot activate last chance"},
                room=sid,
            )

    except Exception as e:
        await sio.emit("last_chance_error", {"message": str(e)}, room=sid)


# TODO:
@sio.event
async def get_game_results(sid: str) -> None:
    """
    Получает результаты игры.

    Args:
        sid: Session ID клиента

    Emits:
        game_results: Результаты игры
        results_error: Ошибка получения результатов
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))
        user_id = active_connections[sid].get("user_id")
        game = await get_game(room_id)

        if not room_id or not game:
            await sio.emit("results_error", {"message": "Not in game"}, room=sid)
            return

        results = {
            "early_exits": game.early_exits,
            "super_exits": game.super_exits,
            "finalists": game.finalists,
            "bonus_fund": game.bonus_fund,
            "zone_fund": game.zone_fund,
            "final_winnings": {},
        }

        # Добавляем финальные выигрыши
        for player_id in game.finalists:
            if player_id in game.players:
                results["final_winnings"][player_id] = game.players[
                    player_id
                ].final_winnings

        await sio.emit("game_results", results, room=sid)

    except Exception as e:
        await sio.emit("results_error", {"message": str(e)}, room=sid)


@sio.event
async def get_leaderboard(sid: str) -> None:
    """
    Получает текущий лидерборд игры.

    Args:
        sid: Session ID клиента

    Emits:
        leaderboard: Текущий лидерборд игры
        leaderboard_error: Ошибка получения лидерборда
    """
    try:
        room_id = str(active_connections[sid].get("room_id"))

        game = await get_game(room_id)

        if not room_id or not game:
            await sio.emit("leaderboard_error", {"message": "Not in game"}, room=sid)
            return

        players_list = []
        for player_id, player in game.players.items():
            player_username = player_id
            for pl in players_in_room.get(room_id, None):
                if pl["user_id"] == player_id:
                    player_username = pl["username"]

            color_tuple = (
                player.color if isinstance(player.color, tuple) else (0, 255, 0)
            )
            # player_color = PlayerColor(
            #     r=color_tuple[0], g=color_tuple[1], b=color_tuple[2]
            # )

            # player_position = PlayerPosition(x=player.x, y=player.y)
            current_player = CurrentPlayer(
                player_id=str(player_id),
                mass=player.get_radius(),
                x=player.x,
                y=player.y,
                r=color_tuple[0],
                g=color_tuple[1],
                b=color_tuple[2],
                skills_used=player.skills_used,
                bonus_zone_collected=player.bonus_zone_collected,
                outside_zone_damage=player.outside_zone_damage,
                in_bonus_zone=player.in_bonus_zone,
                bonus_multiplier=player.current_bonus_multiplier,
                rank=0,
                username=player_username
            )
            players_list.append(current_player)

        players_list.sort(key=lambda x: x.mass, reverse=True)

        for i, player in enumerate(players_list):
            player.rank = i + 1

        # Получаем информацию о фазах игры
        phase = game.get_game_phase_info()

        game_phase_info = GamePhaseInfo(
            phase=str(phase.phase),
            players_count=len(game.players),
            bonus_fund=game.bonus_fund,
            zone_fund=game.zone_fund,
            voting_time_remaining=phase.voting_time_remaining,
            votes_submitted=phase.votes_submitted,
            votes_exit=phase.votes_exit,
            votes_super=phase.votes_super,
            super_game_time_remaining=phase.super_game_time_remaining,
            skill_costs_increased=phase.skill_costs_increased,
        )

        leaderboard_data = LeaderboardData(
            current_players=players_list,
            total_players=len(players_list),
            game_phase=game_phase_info,
            game_time=game.get_game_time(),
            safe_zone_scale=game.safe_zone_scale, 
            zone_fund=game.zone_fund,
            bonus_fund=game.bonus_fund,
        )

        if game.early_exits:
            early_exits_list = [
                EarlyExit(
                    player_id=str(pid),
                    winnings=amount,
                    exit_type="early",
                    percentage=50,
                )
                for pid, amount in game.early_exits.items()
            ]
            early_exits_list.sort(key=lambda x: x.winnings, reverse=True)
            leaderboard_data.early_exits = early_exits_list

        if game.super_exits:
            super_exits_list = [
                SuperExit(
                    player_id=str(pid),
                    winnings=amount,
                    exit_type="super",
                    percentage=25,
                )
                for pid, amount in game.super_exits.items()
            ]
            super_exits_list.sort(key=lambda x: x.winnings, reverse=True)
            leaderboard_data.super_exits = super_exits_list

        if game.finalists:
            finalists_list = [
                Finalist(
                    player_id=str(pid),
                    final_winnings=game.players[pid].final_winnings,
                    final_mass=game.players[pid].get_radius(),
                )
                for pid in game.finalists
                if pid in game.players
            ]
            finalists_list.sort(key=lambda x: x.final_winnings, reverse=True)
            leaderboard_data.finalists = finalists_list

        # Отправляем данные лидерборда клиенту
        await sio.emit("leaderboard", leaderboard_data.model_dump(by_alias=True), room=sid)

    except Exception as e:
        await sio.emit("leaderboard_error", {"message": str(e)}, room=sid)


async def game_loop(room_id):
    game = await create_game(room_id)
    room_players = [
        s for s, info in dict(active_connections).items()
        if info.get("room_id") == room_id
    ]
    user_ids = [
        active_connections[sid].get("user_id")
        for sid in room_players
    ]
    for user_id in user_ids:
        # Находим username для этого игрока
        username = user_id  # По умолчанию используем user_id
        for player_info in players_in_room.get(room_id, []):
            if player_info["user_id"] == user_id:
                username = player_info["username"]
                break
        
        game.add_player(user_id, username)

    last_phase = game.game_phase

    while True:
        room_players = [
            s for s, info in dict(active_connections).items()
            if info.get("room_id") == room_id
        ]

        if not room_players:
            break

        game.update()

        if game.game_phase != last_phase:
            if game.game_phase == "top10":
                await sio.emit(
                    "phase_changed",
                    {
                        "new_phase": "top10",
                        "voting_time_remaining": game.get_voting_time_remaining(),
                        "message": "Голосование в топ-10 началось!",
                    },
                    room=room_id,
                )
            elif game.game_phase == "super":
                await sio.emit(
                    "phase_changed",
                    {
                        "new_phase": "super",
                        "super_game_time_remaining": game.get_super_game_time_remaining(),
                        "message": "Супер игра началась!",
                    },
                    room=room_id,
                )
            elif game.game_phase == "finished":
                await sio.emit(
                    "phase_changed",
                    {"new_phase": "finished", "message": "Игра завершена!"},
                    room=room_id,
                )
                break

            last_phase = game.game_phase

        if game.should_shrink_zone():
            game.shrink_safe_zone()
            await sio.emit(
                "zone_shrunk",
                {
                    "new_scale": game.safe_zone_scale,
                    "damage_per_second": game.zone_damage_per_second,
                    "time_to_next_shrink": game.get_time_to_next_shrink(),
                },
                room=room_id,
            )

        if game.should_spawn_bonus_zone():
            if game.spawn_bonus_zone():
                latest_zone = game.bonus_zones[-1]
                await sio.emit(
                    "bonus_zone_spawned",
                    {
                        "x": latest_zone.x,
                        "y": latest_zone.y,
                        "radius": latest_zone.radius,
                        "multiplier": latest_zone.multiplier,
                        "duration": latest_zone.duration,
                        "zone_fund": game.zone_fund,
                    },
                    room=room_id,
                )

        expired_zones = [zone for zone in game.bonus_zones if zone.is_expired()]
        for zone in expired_zones:
            await sio.emit(
                "bonus_zone_expired",
                {
                    "x": zone.x,
                    "y": zone.y,
                    "multiplier": zone.multiplier,
                    "funds_collected": zone.funds_collected,
                },
                room=room_id,
            )

        if game.game_phase == "top10":
            voting_time = game.get_voting_time_remaining()
            if voting_time <= 10 and voting_time > 0:
                await sio.emit(
                    "voting_warning",
                    {
                        "time_remaining": voting_time,
                        "votes_submitted": len(game.votes),
                        "votes_exit": sum(
                            1 for v in game.votes.values() if v == "exit"
                        ),
                        "votes_super": sum(
                            1 for v in game.votes.values() if v == "super"
                        ),
                    },
                    room=room_id,
                )

        if game.game_phase == "super":
            super_time = game.get_super_game_time_remaining()
            if super_time <= 60 and super_time > 0:
                await sio.emit(
                    "super_game_warning",
                    {
                        "time_remaining": super_time,
                        "players_remaining": len(game.players),
                    },
                    room=room_id,
                )

        game_state = game.get_state().model_dump()
        await sio.emit("game_state", game_state, room=room_id)

        await set_changes(room_id, game)

        await asyncio.sleep(0.05)  # 20 FPS
        # await asyncio.sleep(0.016) # 60 FPS

    game.finalize_game()

    results = {
        "early_exits": game.early_exits,
        "super_exits": game.super_exits,
        "finalists": game.finalists,
        "bonus_fund": game.bonus_fund,
        "zone_fund": game.zone_fund,
        "final_winnings": {},
    }

    for player_id in game.finalists:
        if player_id in game.players:
            results["final_winnings"][player_id] = game.players[
                player_id
            ].final_winnings

    await sio.emit("game_finished", results, room=room_id)

    try:
        async with get_session() as session:
            actions = BalanceActions(session)
            payouts = {}
            for player_id in game.finalists:
                if player_id in game.players:
                    payouts[player_id] = game.players[player_id].final_winnings
            if payouts:
                await actions.credit_finalists(payouts)
    except Exception:
        pass

    await close_game(room_id)
