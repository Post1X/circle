import { Controller, Get, Param } from '@nestjs/common';
import { SkillsService } from './skills.service';

@Controller('api/skills')
export class SkillsController {
  constructor(private skillsService: SkillsService) {}

  @Get('info')
  getSkillsInfo() {
    return this.skillsService.getSkillsInfo();
  }

  @Get('cost/:skill_type')
  async getSkillCost(
    @Param('skill_type') skillType: string,
    @Param('user_id') userId: string,
  ) {
    return this.skillsService.getSkillCost(userId, skillType);
  }
}
