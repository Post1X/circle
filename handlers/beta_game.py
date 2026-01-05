from typing import Dict

from fastapi import APIRouter, HTTPException

from uuid import uuid4

from game.agar import create_beta_game, get_beta_game, set_beta_changes, close_beta_game
from game.models import GameState, GamePhases

from schemas.beta_game import (
    CreateBetaGameRequest,
    MoveRequest,
    SkillRequest,
    VoteRequest,
    ExitRequest,
    BetaGameResponse,
)

import asyncio


router = APIRouter(
    prefix="/api/beta-game",
    tags=["Beta Game"],
)

_game_loops: Dict[str, asyncio.Task] = {}
_game_locks: Dict[str, asyncio.Lock] = {}


@router.post("/create", response_model=BetaGameResponse)
async def create_beta_game_endpoint(request: CreateBetaGameRequest):
    try:
        game_id = str(uuid4())
        game = await create_beta_game(game_id, expected_players=10, fund=1000.0)
        game.add_player(request.player_id)
        
        _game_locks[game_id] = asyncio.Lock()
        _game_loops[game_id] = asyncio.create_task(_run_game_loop(game_id))
        
        return BetaGameResponse(
            success=True,
            game_id=game_id,
            message="Beta game created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{game_id}")
async def get_game_state(game_id: str) -> GameState:
    try:
        game = await get_beta_game(game_id)
        return game.get_state()
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move", response_model=BetaGameResponse)
async def move_player(request: MoveRequest):
    try:
        if request.game_id not in _game_locks:
            _game_locks[request.game_id] = asyncio.Lock()
            
        async with _game_locks[request.game_id]:
            game = await get_beta_game(request.game_id)
            if request.player_id not in game.players:
                return BetaGameResponse(
                    success=False,
                    message="Player not found in game"
                )
            game.move_player(request.player_id, request.dx, request.dy)
            await set_beta_changes(request.game_id, game)
        
        return BetaGameResponse(
            success=True,
            message="Player moved successfully"
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skill", response_model=BetaGameResponse)
async def activate_skill(request: SkillRequest):
    try:
        if request.game_id not in _game_locks:
            _game_locks[request.game_id] = asyncio.Lock()
            
        async with _game_locks[request.game_id]:
            game = await get_beta_game(request.game_id)
            
            if request.player_id not in game.players:
                return BetaGameResponse(
                    success=False,
                    message="Player not found in game"
                )
            
            if game.game_phase == GamePhases.SUPER:
                player = game.players.get(request.player_id)
                if player and player.get_radius() <= 5:
                    last_chance_success = game.check_last_chance(request.player_id)
                    if last_chance_success:
                        await set_beta_changes(request.game_id, game)
                        
                        # Получаем актуальные cooldowns после last chance
                        cooldowns = None
                        if player:
                            from game.models import Cooldowns
                            cooldowns = Cooldowns(
                                teleport=float(round(max(0.0, player.teleport_cooldown), 1)),
                                shield=float(round(max(0.0, player.shield_cooldown), 1)),
                                boost=float(round(max(0.0, player.boost_cooldown), 1)),
                            )
                        
                        return BetaGameResponse(
                            success=True,
                            message="Last chance teleport activated",
                            data={
                                "skill_type": "teleport",
                                "last_chance": True,
                                "skill_costs_increased": game.skill_costs_increased,
                                "cooldowns": cooldowns.model_dump() if cooldowns else None,
                            }
                        )
            
            success, message = game.activate_skill(request.player_id, request.skill_type)
            await set_beta_changes(request.game_id, game)
            
            if success:
                skill_cost = game.get_skill_cost(request.player_id, request.skill_type)
                
                # Получаем игрока для отправки актуальных cooldowns
                player = game.players.get(request.player_id)
                cooldowns = None
                if player:
                    from game.models import Cooldowns
                    cooldowns = Cooldowns(
                        teleport=float(round(max(0.0, player.teleport_cooldown), 1)),
                        shield=float(round(max(0.0, player.shield_cooldown), 1)),
                        boost=float(round(max(0.0, player.boost_cooldown), 1)),
                    )
                
                return BetaGameResponse(
                    success=True,
                    message=message,
                    data={
                        "skill_type": request.skill_type,
                        "skill_cost": skill_cost,
                        "skill_costs_increased": game.skill_costs_increased,
                        "cooldowns": cooldowns.model_dump() if cooldowns else None,
                    }
                )
            else:
                return BetaGameResponse(success=False, message=message)
            
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vote", response_model=BetaGameResponse)
async def submit_vote(request: VoteRequest):
    try:
        if request.game_id not in _game_locks:
            _game_locks[request.game_id] = asyncio.Lock()
            
        async with _game_locks[request.game_id]:
            game = await get_beta_game(request.game_id)
            
            if request.player_id not in game.players:
                return BetaGameResponse(
                    success=False,
                    message="Player not found in game"
                )
            
            success = game.submit_vote(request.player_id, request.vote)
            await set_beta_changes(request.game_id, game)
            
            if success:
                return BetaGameResponse(
                    success=True,
                    message="Vote submitted successfully",
                    data={
                        "vote": request.vote,
                        "voting_time_remaining": game.get_voting_time_remaining()
                    }
                )
            else:
                return BetaGameResponse(
                    success=False,
                    message="Cannot submit vote - check game phase and voting status"
                )
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exit", response_model=BetaGameResponse)
async def exit_game(request: ExitRequest):
    try:
        if request.game_id not in _game_locks:
            _game_locks[request.game_id] = asyncio.Lock()
            
        async with _game_locks[request.game_id]:
            game = await get_beta_game(request.game_id)
            
            if request.player_id not in game.players:
                return BetaGameResponse(
                    success=False,
                    message="Player not found in game"
                )
            
            if request.exit_type == "early" and game.game_phase == GamePhases.START:
                game.process_early_exit(request.player_id)
                winnings = game.early_exits.get(request.player_id, 0)
            elif request.exit_type == "super" and game.game_phase == GamePhases.SUPER:
                game.process_super_exit(request.player_id)
                winnings = game.super_exits.get(request.player_id, 0)
            else:
                raise HTTPException(status_code=400, detail="Invalid exit type or phase")
            
            await set_beta_changes(request.game_id, game)
        
        return BetaGameResponse(
            success=True,
            message="Player exited successfully",
            data={"winnings": winnings, "exit_type": request.exit_type}
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phase/{game_id}")
async def get_game_phase(game_id: str):
    try:
        game = await get_beta_game(game_id)
        return game.get_game_phase_info()
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bonus-zones/{game_id}")
async def get_bonus_zones(game_id: str):
    try:
        game = await get_beta_game(game_id)
        return game.get_bonus_zones()
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/{game_id}")
async def get_leaderboard(game_id: str):
    try:
        game = await get_beta_game(game_id)
        players_list = []
        
        for player_id, player in game.players.items():
            if player is not None:
                players_list.append({
                    "player_id": player_id,
                    "mass": player.get_radius(),
                    "money": player.money,
                    "x": player.x,
                    "y": player.y,
                    "skills_used": player.skills_used,
                    "in_bonus_zone": player.in_bonus_zone,
                    "bonus_multiplier": player.current_bonus_multiplier,
                    "shield_active": player.shield_active,
                    "speed_boost_active": player.speed_boost_active
                })
        
        players_list.sort(key=lambda x: x["mass"], reverse=True)
        for i, player in enumerate(players_list):
            player["rank"] = i + 1
            
        return {
            "players": players_list,
            "game_phase": str(game.game_phase),
            "bonus_fund": game.bonus_fund,
            "zone_fund": game.zone_fund,
            "safe_zone_scale": game.safe_zone_scale
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{game_id}")
async def get_game_results(game_id: str):
    try:
        game = await get_beta_game(game_id)
        
        results = {
            "early_exits": game.early_exits,
            "super_exits": game.super_exits,
            "finalists": game.finalists,
            "bonus_fund": game.bonus_fund,
            "zone_fund": game.zone_fund,
            "final_winnings": {}
        }
        
        for player_id in (game.finalists or []):
            if player_id in game.players and game.players[player_id] is not None:
                results["final_winnings"][player_id] = game.players[player_id].final_winnings
                
        return results
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/close/{game_id}", response_model=BetaGameResponse)
async def close_game(game_id: str):
    try:
        if game_id in _game_loops:
            _game_loops[game_id].cancel()
            del _game_loops[game_id]
        
        if game_id in _game_locks:
            del _game_locks[game_id]
        
        await close_beta_game(game_id)
        
        return BetaGameResponse(
            success=True,
            message="Game closed successfully"
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_game_loop(game_id: str):
    try:
        while True:
            try:
                if game_id not in _game_locks:
                    break
                    
                async with _game_locks[game_id]:
                    game = await get_beta_game(game_id)
                    game.update()
                    await set_beta_changes(game_id, game)
                    
                    if game.game_phase == GamePhases.FINISHED:
                        game.finalize_game()
                        await set_beta_changes(game_id, game)
                        break
                    
                await asyncio.sleep(0.05)
            except KeyError:
                break
            except Exception as e:
                print(f"Error in game loop for {game_id}: {e}")
                await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
    finally:
        if game_id in _game_loops:
            del _game_loops[game_id]
        if game_id in _game_locks:
            del _game_locks[game_id]
