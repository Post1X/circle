import { Injectable } from '@nestjs/common';
import { randomUUID } from 'crypto';
import {
  create_beta_game,
  get_beta_game,
  set_beta_changes,
  close_beta_game,
  BetaGame,
} from '../../game';

@Injectable()
export class BetaGameService {
  private gameLoops: Map<string, NodeJS.Timeout> = new Map();

  async createGame(
    playerId: string,
    expectedPlayers: number,
    fund: number,
  ): Promise<{ gameId: string }> {
    const gameId = randomUUID();
    const game = await create_beta_game(gameId, expectedPlayers, fund);
    game.add_player(playerId);
    this.startGameLoop(gameId);
    return { gameId };
  }

  async getGameState(gameId: string) {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }
    return game.get_state();
  }

  async movePlayer(
    gameId: string,
    playerId: string,
    dx: number,
    dy: number,
  ) {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }
    game.move_player(playerId, dx, dy);
    await set_beta_changes(gameId, game);
  }

  async activateSkill(
    gameId: string,
    playerId: string,
    skillType: string,
  ): Promise<{ success: boolean; message: string; data?: any }> {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }

    if (!game.players.has(playerId)) {
      return {
        success: false,
        message: 'Player not found in game',
      };
    }

    const [success, message] = game.activate_skill(playerId, skillType);
    await set_beta_changes(gameId, game);

    if (success) {
      const player = game.players.get(playerId);
      return {
        success: true,
        message,
        data: {
          skill_type: skillType,
          skill_costs_increased: game.skill_costs_increased,
          cooldowns: player
            ? {
                teleport: Math.round(Math.max(0, player.teleport_cooldown) * 10) / 10,
                shield: Math.round(Math.max(0, player.shield_cooldown) * 10) / 10,
                boost: Math.round(Math.max(0, player.boost_cooldown) * 10) / 10,
              }
            : null,
        },
      };
    }

    return { success: false, message };
  }

  async submitVote(
    gameId: string,
    playerId: string,
    vote: string,
  ): Promise<{ success: boolean; message: string; data?: any }> {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }

    const success = game.submit_vote(playerId, vote);
    await set_beta_changes(gameId, game);

    if (success) {
      return {
        success: true,
        message: 'Vote submitted successfully',
        data: {
          vote,
          voting_time_remaining: game.get_voting_time_remaining(),
        },
      };
    }

    return {
      success: false,
      message: 'Cannot submit vote - check game phase and voting status',
    };
  }

  async exitGame(
    gameId: string,
    playerId: string,
    exitType: string,
  ): Promise<{ winnings: number; exit_type: string }> {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }

    if (exitType === 'early' && game.game_phase === 'start') {
      game.process_early_exit(playerId);
      const winnings = game.early_exits.get(playerId) || 0;
      await set_beta_changes(gameId, game);
      return { winnings, exit_type: exitType };
    } else if (exitType === 'super' && game.game_phase === 'super') {
      game.process_super_exit(playerId);
      const winnings = game.super_exits.get(playerId) || 0;
      await set_beta_changes(gameId, game);
      return { winnings, exit_type: exitType };
    }

    throw new Error('Invalid exit type or phase');
  }

  async getGamePhaseInfo(gameId: string) {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }
    return game.get_game_phase_info();
  }

  async getBonusZones(gameId: string) {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }
    return game.get_bonus_zones();
  }

  async getLeaderboard(gameId: string) {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }

    const players = Array.from(game.players.entries())
      .map(([id, player]) => ({
        player_id: id,
        mass: player.get_radius(),
        money: player.money,
        x: player.x,
        y: player.y,
        skills_used: player.skills_used,
        in_bonus_zone: player.in_bonus_zone,
        bonus_multiplier: player.current_bonus_multiplier,
        shield_active: player.shield_active,
        speed_boost_active: player.speed_boost_active,
        rank: 0,
      }))
      .sort((a, b) => b.mass - a.mass);

    players.forEach((p, i) => {
      p.rank = i + 1;
    });

    return {
      players,
      game_phase: game.game_phase,
      bonus_fund: game.bonus_fund,
      zone_fund: game.zone_fund,
      safe_zone_scale: game.safe_zone_scale,
    };
  }

  async getGameResults(gameId: string) {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }

    return {
      early_exits: Object.fromEntries(game.early_exits),
      super_exits: Object.fromEntries(game.super_exits),
      finalists: game.finalists,
      bonus_fund: game.bonus_fund,
      zone_fund: game.zone_fund,
      final_winnings: Object.fromEntries(
        game.finalists.map((pid) => [
          pid,
          game.players.get(pid)?.final_winnings || 0,
        ]),
      ),
    };
  }

  async closeGame(gameId: string) {
    const game = await get_beta_game(gameId);
    if (!game) {
      throw new Error('Game not found');
    }

    const loop = this.gameLoops.get(gameId);
    if (loop) {
      clearInterval(loop);
      this.gameLoops.delete(gameId);
    }

    await close_beta_game(gameId);
  }

  private startGameLoop(gameId: string) {
    const loop = setInterval(async () => {
      const game = await get_beta_game(gameId);
      if (!game) {
        clearInterval(loop);
        this.gameLoops.delete(gameId);
        return;
      }

      game.update();
      await set_beta_changes(gameId, game);

      if (game.game_phase === 'finished') {
        game.finalize_game();
        await set_beta_changes(gameId, game);
        clearInterval(loop);
        this.gameLoops.delete(gameId);
      }
    }, 50);

    this.gameLoops.set(gameId, loop);
  }
}
