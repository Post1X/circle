from fastapi import APIRouter, Depends

from game import get_game

from sqlalchemy.ext.asyncio import AsyncSession

from bd.database import get_session
from bd.actions.user import UserActions

from uuid import UUID

from schemas.leaderboard import (
    LeaderboardResponse, 
    LeaderboardErrorResponse, 
    LeaderboardData, 
    CurrentPlayer, 
    GamePhaseInfo,
    EarlyExit,
    SuperExit,
    Finalist
)


router = APIRouter(
    prefix="/api/game",
    tags=["Game"],
)


@router.get(
    "/bonus-zones-info",
    description="Получить информацию о бонусных зонах"
)
async def get_bonus_zones_info(game_id: str):
    """Возвращает информацию о бонусных зонах"""
    game = await get_game(game_id)
    return game.get_bonus_zones()


@router.get(
    "/leaderboard",
    description="Получить текущий лидерборд игры",
    response_model=LeaderboardResponse
)
async def get_game_leaderboard(game_id: str, session: AsyncSession = Depends(get_session)):
    """Возвращает текущий лидерборд игры"""
    try:
        game = await get_game(game_id)
        players_list = []
        user_actions = UserActions(session)
        
        for player_id, player in game.players.items():
            color_tuple = player.color if isinstance(player.color, tuple) else (0, 255, 0)
            
            try:
                user = await user_actions.get_user_by_id(UUID(player_id))
                username = user.username if user else str(player_id)
            except (ValueError, Exception):
                username = str(player_id)
            
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
                username=username
            )
            players_list.append(current_player)
        
        players_list.sort(key=lambda x: x.mass, reverse=True)
        
        for i, player in enumerate(players_list):
            player.rank = i + 1
        
        phase = game.get_game_phase_info()
        
        phase_info = GamePhaseInfo(
            phase=str(phase.phase),
            players_count=len(game.players),
            bonus_fund=game.bonus_fund,
            zone_fund=game.zone_fund,
            voting_time_remaining=phase.voting_time_remaining,
            votes_submitted=phase.votes_submitted,
            votes_exit=phase.votes_exit,
            votes_super=phase.votes_super,
            super_game_time_remaining=phase.super_game_time_remaining,
            skill_costs_increased=phase.skill_costs_increased
        )
        
        leaderboard_data = LeaderboardData(
            current_players=players_list,
            total_players=len(players_list),
            game_phase=phase_info,
            game_time=game.get_game_time(),
            safe_zone_scale=game.safe_zone_scale,
            zone_fund=game.zone_fund,
            bonus_fund=game.bonus_fund,
            early_exits=None
        )
        
        if game.early_exits:
            early_exits_list = [
                EarlyExit(
                    player_id=str(pid),
                    winnings=amount,
                    exit_type="early",
                    percentage=50
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
                    percentage=25
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
                    final_mass=game.players[pid].get_radius()
                )
                for pid in game.finalists
                if pid in game.players
            ]
            finalists_list.sort(key=lambda x: x.final_winnings, reverse=True)
            leaderboard_data.finalists = finalists_list
        
        return LeaderboardResponse(
            success=True,
            leaderboard=leaderboard_data
        )
        
    except Exception as e:
        return LeaderboardErrorResponse(
            error=str(e),
            message="Failed to get leaderboard"
        )


@router.get(
    "/game-phase",
    description="Получить текущую фазу игры"
)
async def get_game_phase(game_id: str):
    """Возвращает текущую фазу игры"""
    game = await get_game(game_id)
    return game.game_phase


@router.post(
        "/{game_id}/exit",
        description="Эндпоинт для досрочного выхода из игры",
)
async def exit_game(game_id: str, user_id: int):
    """Удаляет игрока из игры БЕЗ изменения размера карты"""
    # Удаляем игрока из игры (размер карты НЕ изменяется автоматически)
    game = await get_game(game_id)
    game.remove_player(str(user_id))
