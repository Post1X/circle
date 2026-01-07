import { Controller, Get, Param, UseGuards } from '@nestjs/common';
import { SkillsService } from './skills.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { User } from '../../entities/user.entity';

@Controller('api/skills')
export class SkillsController {
  constructor(private skillsService: SkillsService) {}

  @Get('info')
  getSkillsInfo() {
    return this.skillsService.getSkillsInfo();
  }

  @Get('cost/:skill_type')
  @UseGuards(JwtAuthGuard)
  async getSkillCost(
    @Param('skill_type') skillType: string,
    @CurrentUser() user: User,
  ) {
    return this.skillsService.getSkillCost(user.user_id, skillType);
  }
}
