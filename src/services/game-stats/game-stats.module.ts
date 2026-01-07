import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { GamePlayerStats } from '../../entities/game-player-stats.entity';
import { User } from '../../entities/user.entity';
import { GameStatsService } from './game-stats.service';
import { SkillStatsModule } from '../skill-stats/skill-stats.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([GamePlayerStats, User]),
    SkillStatsModule,
  ],
  providers: [GameStatsService],
  exports: [GameStatsService],
})
export class GameStatsModule {}

