import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { GamePlayerStats } from '../../entities/game-player-stats.entity';
import { User } from '../../entities/user.entity';
import { SkillStatsService } from '../skill-stats/skill-stats.service';
import { Player } from '../../game/player';

@Injectable()
export class GameStatsService {
  constructor(
    @InjectRepository(GamePlayerStats)
    private gamePlayerStatsRepository: Repository<GamePlayerStats>,
    @InjectRepository(User)
    private userRepository: Repository<User>,
    private skillStatsService: SkillStatsService,
  ) {}

  async savePlayerGameStats(
    userId: string,
    sessionId: string,
    player: Player,
    exitType: string,
    gameStartTime: number,
    finalRank: number | null = null,
  ): Promise<void> {
    const gameDuration = Math.floor(Date.now() / 1000 - gameStartTime);

    const playerSkillStats = await this.skillStatsService.getPlayerSkillStatsForSession(
      sessionId,
      userId,
    );

    const teleportUses = playerSkillStats.filter(
      (s) => s.skill_type === 'teleport',
    ).length;
    const shieldUses = playerSkillStats.filter(
      (s) => s.skill_type === 'shield',
    ).length;
    const boostUses = playerSkillStats.filter(
      (s) => s.skill_type === 'boost',
    ).length;

    const skillsCostTotal = playerSkillStats.reduce(
      (sum, s) => sum + parseFloat(s.cost.toString()),
      0,
    );

    const stats = this.gamePlayerStatsRepository.create({
      user_id: userId,
      session_id: sessionId,
      skills_used_total: player.skills_used,
      skills_cost_total: skillsCostTotal,
      final_winnings: player.final_winnings,
      final_rank: finalRank,
      game_duration_seconds: gameDuration,
      exit_type: exitType,
      teleport_uses: teleportUses,
      shield_uses: shieldUses,
      boost_uses: boostUses,
      free_teleport_used: player.free_teleport_used,
      bonus_zone_collected: player.bonus_zone_collected,
      outside_zone_damage: player.outside_zone_damage,
    });

    await this.gamePlayerStatsRepository.save(stats);

    const user = await this.userRepository.findOne({
      where: { user_id: userId },
    });
    if (user) {
      user.games_played += 1;
      user.total_winnings = parseFloat(user.total_winnings.toString()) + parseFloat(player.final_winnings.toString());
      await this.userRepository.save(user);
    }
  }

  async savePlayerGameStatsFromData(
    userId: string,
    sessionId: string,
    playerData: {
      skills_used: number;
      final_winnings: number;
      free_teleport_used: boolean;
      bonus_zone_collected: number;
      outside_zone_damage: number;
      teleport_uses: number;
      shield_uses: number;
      boost_uses: number;
      skills_cost_total: number;
    },
    exitType: string,
    gameStartTime: number,
    finalRank: number | null = null,
  ): Promise<void> {
    const gameDuration = Math.floor(Date.now() / 1000 - gameStartTime);

    const stats = this.gamePlayerStatsRepository.create({
      user_id: userId,
      session_id: sessionId,
      skills_used_total: playerData.skills_used,
      skills_cost_total: playerData.skills_cost_total,
      final_winnings: playerData.final_winnings,
      final_rank: finalRank,
      game_duration_seconds: gameDuration,
      exit_type: exitType,
      teleport_uses: playerData.teleport_uses,
      shield_uses: playerData.shield_uses,
      boost_uses: playerData.boost_uses,
      free_teleport_used: playerData.free_teleport_used,
      bonus_zone_collected: playerData.bonus_zone_collected,
      outside_zone_damage: playerData.outside_zone_damage,
    });

    await this.gamePlayerStatsRepository.save(stats);

    const user = await this.userRepository.findOne({
      where: { user_id: userId },
    });
    if (user) {
      user.games_played += 1;
      user.total_winnings = parseFloat(user.total_winnings.toString()) + parseFloat(playerData.final_winnings.toString());
      await this.userRepository.save(user);
    }
  }
}

