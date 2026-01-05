import { Injectable, BadRequestException, NotFoundException } from '@nestjs/common';
import { UsersService } from '../users/users.service';

@Injectable()
export class SkillsService {
  constructor(private usersService: UsersService) {}

  getSkillsInfo() {
    return {
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
      rules: {
        max_activations_per_game: 5,
        minimum_balance: 1.0,
        cost_taken_from_game_balance: true,
      },
    };
  }

  async getSkillCost(userId: string, skillType: string) {
    if (!['teleport', 'shield', 'boost'].includes(skillType)) {
      throw new BadRequestException('Invalid skill type');
    }

    const user = await this.usersService.getUserById(userId);
    if (!user) {
      throw new NotFoundException('User not found');
    }

    const balance = parseFloat(user.balance.toString());

    const costPercentages = {
      teleport: 0.15,
      shield: 0.1,
      boost: 0.05,
    };

    const cost = balance * costPercentages[skillType];

    return {
      skill_type: skillType,
      current_balance: balance,
      cost_percentage: costPercentages[skillType] * 100,
      cost_amount: cost,
      can_afford: balance >= 1.0,
    };
  }
}


