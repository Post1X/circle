import { Injectable } from '@nestjs/common';
import { get_game, get_beta_game } from '../../game';

@Injectable()
export class GameService {
  async getBonusZones(gameId: string) {
    const game = await get_game(gameId);
    if (!game) {
      return { error: 'Game not found' };
    }
    return game.get_bonus_zones();
  }

  async getLeaderboard(gameId: string) {
    const game = await get_game(gameId);
    if (!game) {
      return { error: 'Game not found' };
    }

    const players_list = [];
    for (const [player_id, player] of game.players.entries()) {
      players_list.push({
        player_id,
        mass: player.get_radius(),
        x: player.x,
        y: player.y,
        r: player.color[0],
        g: player.color[1],
        b: player.color[2],
        skills_used: player.skills_used,
        bonus_zone_collected: player.bonus_zone_collected,
        outside_zone_damage: player.outside_zone_damage,
        in_bonus_zone: player.in_bonus_zone,
        bonus_multiplier: player.current_bonus_multiplier,
        rank: 0,
        username: player.username,
      });
    }

    players_list.sort((a, b) => b.mass - a.mass);
    players_list.forEach((p, i) => {
      p.rank = i + 1;
    });

    const phase = game.get_game_phase_info();

    return {
      success: true,
      leaderboard: {
        current_players: players_list,
        total_players: players_list.length,
        game_phase: phase,
        game_time: game.get_game_time(),
        safe_zone_scale: game.safe_zone_scale,
        zone_fund: game.zone_fund,
        bonus_fund: game.bonus_fund,
        early_exits: game.early_exits.size > 0 ? Object.fromEntries(game.early_exits) : null,
        super_exits: game.super_exits.size > 0 ? Object.fromEntries(game.super_exits) : null,
        finalists: game.finalists.length > 0 ? game.finalists.map((pid) => ({
          player_id: pid,
          final_winnings: game.players.get(pid)?.final_winnings || 0,
          final_mass: game.players.get(pid)?.get_radius() || 0,
        })) : null,
      },
    };
  }

  async getGamePhase(gameId: string) {
    const game = await get_game(gameId);
    if (!game) {
      return { error: 'Game not found' };
    }
    return game.game_phase;
  }

  async removePlayer(gameId: string, userId: string) {
    const game = await get_game(gameId);
    if (game) {
      game.remove_player(userId);
    }
  }
}
