import { Module } from '@nestjs/common';
import { SkillsController } from './skills.controller';
import { SkillsService } from './skills.service';
import { UsersModule } from '../users/users.module';
import { CacheModule } from '../../services/cache/cache.module';
import { GameTrackerModule } from '../../services/game-tracker/game-tracker.module';

@Module({
  imports: [UsersModule, CacheModule, GameTrackerModule],
  controllers: [SkillsController],
  providers: [SkillsService],
})
export class SkillsModule {}

