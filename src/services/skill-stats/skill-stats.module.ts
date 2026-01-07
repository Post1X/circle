import { Module } from '@nestjs/common';
import { SkillStatsService } from './skill-stats.service';
import { CacheModule } from '../cache/cache.module';

@Module({
  imports: [CacheModule],
  providers: [SkillStatsService],
  exports: [SkillStatsService],
})
export class SkillStatsModule {}

