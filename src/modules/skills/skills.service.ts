import { Injectable, BadRequestException, NotFoundException } from '@nestjs/common';
import { UsersService } from '../users/users.service';
import { CacheService } from '../../services/cache/cache.service';
import { GameTrackerService } from '../../services/game-tracker/game-tracker.service';

@Injectable()
export class SkillsService {
  private readonly SKILLS_INFO_CACHE_KEY = 'skills:info';
  private readonly SKILLS_INFO_CACHE_TTL = 3600;

  constructor(
    private usersService: UsersService,
    private cacheService: CacheService,
    private gameTrackerService: GameTrackerService,
  ) {}

  async getSkillsInfo() {
    const cached = await this.cacheService.get(this.SKILLS_INFO_CACHE_KEY);
    if (cached) {
      return cached;
    }

    const skillsInfo = {
      skills: [
        {
          type: 'teleport',
          name: 'Рандомный телепорт',
          description: 'Мгновенный телепорт в 100% безопасное место',
          cost_percentage: 15,
          cooldown: 60,
          duration: 0,
        },
        {
          type: 'shield',
          name: 'Защитный щит',
          description: '3 секунды неуязвимости',
          cost_percentage: 10,
          cooldown: 30,
          duration: 3,
        },
        {
          type: 'boost',
          name: 'Ускорение',
          description: '5 секунд повышенной скорости',
          cost_percentage: 5,
          cooldown: 15,
          duration: 5,
        },
      ],
      max_uses: 5,
      minimum_balance: 1.0,
      last_chance: {
        enabled: true,
        conditions: {
          phase: 'super_game',
          time_remaining: 180,
          balance_threshold: 5.0,
        },
        penalty_percentage: 5,
      },
    };

    await this.cacheService.set(
      this.SKILLS_INFO_CACHE_KEY,
      skillsInfo,
      this.SKILLS_INFO_CACHE_TTL,
    );

    return skillsInfo;
  }

  async getSkillCost(userId: string, skillType: string) {
    if (!['teleport', 'shield', 'boost'].includes(skillType)) {
      throw new BadRequestException('Invalid skill type');
    }

    const { get_game } = await import('../../game');
    let player = null;
    let game = null;
    const roomId = await this.gameTrackerService.getPlayerRoom(userId);

    if (roomId) {
      game = await get_game(roomId);
      if (game && game.players.has(userId)) {
        player = game.players.get(userId);
      }
    }

    let balance = 0;
    let skillsUsed = 0;
    let freeTeleportUsed = false;
    let cooldowns = { teleport: 0, shield: 0, boost: 0 };

    if (player) {
      balance = player.money;
      skillsUsed = player.skills_used;
      freeTeleportUsed = player.free_teleport_used;
      cooldowns = {
        teleport: Math.max(0, player.teleport_cooldown),
        shield: Math.max(0, player.shield_cooldown),
        boost: Math.max(0, player.boost_cooldown),
      };
    } else {
      const user = await this.usersService.getUserById(userId);
      if (!user) {
        throw new NotFoundException('User not found');
      }
      balance = parseFloat(user.balance.toString());
    }

    const baseCostPercentages = {
      teleport: 0.15,
      shield: 0.1,
      boost: 0.05,
    };

    let costPercentage = baseCostPercentages[skillType];
    if (freeTeleportUsed) {
      costPercentage += 0.05;
    }

    const costAmount = balance * costPercentage;
    const isFree = player && game && game.check_last_chance(userId) && skillType === 'teleport';

    return {
      skill_type: skillType,
      cost_percentage: costPercentage * 100,
      cost_amount: costAmount,
      current_balance: balance,
      can_afford: balance >= costAmount,
      minimum_balance_met: balance >= 1.0,
      skills_remaining: 5 - skillsUsed,
      is_free: isFree && !freeTeleportUsed,
      cooldown_remaining: Math.round(cooldowns[skillType as keyof typeof cooldowns] * 10) / 10,
    };
  }
}


