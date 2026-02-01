## Схема комнат и матчмейкинга (Python Socket.IO + NestJS)

Этот документ описывает, как сейчас работает система игровых комнат и запуск игры.

- **Python / Socket.IO** — реальный игровой сервер и матчмейкинг.
- **NestJS** — админ/REST-слой, который читает/показывает данные из той же таблицы `game_room`.

---

## Хранение данных о комнате

### В базе данных

Таблица `game_room` описана сразу в двух моделях:

- **Python (SQLAlchemy)** — основная логика матчмейкинга и старта игры:

```71:105:bd/models.py
class GameRoom(Base):
    __tablename__ = "game_room"

    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    entry_fee: Mapped[int] = mapped_column(Integer)

    players: Mapped[int] = mapped_column(Integer, default=0)
    min_players: Mapped[int] = mapped_column(Integer, default=20)
    max_players: Mapped[int] = mapped_column(Integer, default=100)

    status: Mapped[str] = mapped_column(String, default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

- **NestJS (TypeORM)** — читает те же данные:

```9:31:src/entities/game-room.entity.ts
@Entity('game_room')
export class GameRoom {
  @PrimaryGeneratedColumn('uuid')
  @Index()
  room_id: string;

  @Column({ type: 'int' })
  entry_fee: number;

  @Column({ type: 'int', default: 0 })
  players: number;

  @Column({ type: 'int', default: 20 })
  min_players: number;

  @Column({ type: 'int', default: 100 })
  max_players: number;

  @Column({ type: 'varchar', default: 'waiting' })
  status: string;

  @CreateDateColumn()
  created_at: Date;
}
```

### В оперативной памяти (во время игры)

В `handlers/rooms.py` поддерживаются структуры:

- `active_connections`: по каждому `sid` хранится `user_id`, `room_id`, `authenticated`, `username`.
- `players_in_room`: для каждого `room_id` — список игроков с `user_id` и `username`.
- Игровое состояние (`Game` и игроки) живёт в модуле `game` и привязано к `room_id`.

---

## Логика матчмейкинга: `join_game`

### Цель

Сделать **один сокет-ивент** для входа в игру, без явной передачи `room_id` с фронта:

- Если есть подходящая свободная комната — подключаем в неё.
- Если нет — создаём новую и подключаем.
- После подключения фронт получает `room_id` из события `joined_room`.

### Сценарий на фронте

Фронт эмитит:

```json
{
  "event": "join_game",
  "data": {
    "entry_fee": 0,
    "min_players": 1,
    "max_players": 100
  }
}
```

> `min_players` сейчас по умолчанию временно установлен в `1`, чтобы игра могла стартовать сразу.

### Обработчик `join_game` на бэке

На стороне Python / Socket.IO (`handlers/rooms.py`) добавлен новый ивент:

```188:222:handlers/rooms.py
@sio.event
async def join_game(sid: str, data: Dict[str, Any]) -> None:
    """
    Автоматическое подключение к игре:
    - ищем подходящую комнату в статусе waiting;
    - если нет — создаем новую;
    - затем подключаем игрока через _join_room_socket.
    """
    try:
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

            await _join_room_socket(sid, str(room.room_id))

    except Exception as e:
        await sio.emit("error", {"message": str(e) + " join_game"}, room=sid)
```

---

## Поиск свободной комнаты: `RoomActions.get_free_room`

Логика поиска реализована в `bd/actions/room.py`:

```32:60:bd/actions/room.py
async def get_free_room(
    self,
    entry_fee: int,
    min_players: int,
    max_players: int,
) -> Optional[GameRoom]:
    """
    Возвращает первую попавшуюся комнату в статусе "waiting",
    которая еще не заполнена и соответствует параметрам.
    """
    query = (
        select(GameRoom)
        .where(
            and_(
                GameRoom.status == "waiting",
                GameRoom.players < GameRoom.max_players,
                GameRoom.entry_fee == entry_fee,
                GameRoom.min_players == min_players,
                GameRoom.max_players == max_players,
            )
        )
        .order_by(GameRoom.created_at)
    )
    result = await self.session.execute(query)
    return result.scalars().first()
```

Если такой комнаты нет — `join_game` создаёт новую через:

```1:30:bd/actions/room.py
async def create_room(
    self,
    entry_fee: int,
    min_players: int,
    max_players: int,
    status: str = "waiting",
) -> GameRoom:
    room = GameRoom(
        entry_fee=entry_fee,
        min_players=min_players,
        max_players=max_players,
        status=status,
    )
    self.session.add(room)
    await self.session.commit()
    await self.session.refresh(room)
    return room
```

---

## Подключение к комнате и старт игры

После выбора/создания комнаты `join_game` вызывает:

```292:362:handlers/rooms.py
async def _join_room_socket(sid: str, room_id: str) -> None:
    ...
    await sio.enter_room(sid, room_id)
    await actions.add_player(room_id)
    active_connections[sid]["room_id"] = room_id
    await sio.emit(
        "player_joined",
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
```

Ключевые моменты:

- **`joined_room`**:
  - Отправляется только текущему игроку (`room=sid`).
  - Содержит `room_id`, список игроков и `time_to_start`, если игра скоро начнётся.
  - Именно отсюда фронт должен сохранять `room_id` для реконнектов и дальнейших запросов.

- **`player_joined`**:
  - Шлётся во всю комнату (`room=room_id`) с обновлённым списком игроков.

- **Старт игры**:
  - `need_start_game` определяется через `RoomActions.check_start_game`.
  - При `True` всем в комнате приходит `game_started`, через 30 секунд запускается `game_loop(room_id)`.

---

## Условие старта игры: `check_start_game`

```33:38:bd/actions/room.py
async def check_start_game(self, room_id) -> bool:
    room = await self.get_room_by_id(room_id)
    if room and room.min_players <= room.players:
        return True
    return False
```

Сейчас (временно) `min_players` по умолчанию устанавливается в `1` в `join_game`, поэтому игра может стартовать уже с одним игроком. В будущем это поведение можно легко поменять, просто вернув дефолты `min_players` на более высокое значение и/или управляя им с фронта.

---

## Что важно знать фронту

- Чтобы **подключиться к игре**, фронт шлёт **один** ивент `join_game` без `room_id`.
- Реальный `room_id` фронт всегда получает:
  - в payload события `joined_room` (`data.room_id`);
  - его нужно сохранить (стейт/LocalStorage) для реконнектов и дальнейших запросов.
- Игровое состояние (`game_state`, лидерборд, фазы и т.д.) привязано к `room_id`, поэтому наличие корректного `room_id` критично для:
  - восстановления сессии;
  - подписки на нужные обновления;
  - корректного выхода/завершения игры.






