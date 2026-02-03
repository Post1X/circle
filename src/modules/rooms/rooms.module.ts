import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { GameRoom } from '../../entities/game-room.entity';
import { User } from '../../entities/user.entity';
import { RoomsGateway } from './rooms.gateway';
import { RoomsService } from './rooms.service';
import { UsersModule } from '../users/users.module';
import { PlayerCounterModule } from '../../services/player-counter/player-counter.module';
import { WithdrawalModule } from '../withdrawal/withdrawal.module';
import { CacheModule } from '../../services/cache/cache.module';
import { SkillStatsModule } from '../../services/skill-stats/skill-stats.module';
import { GameTrackerModule } from '../../services/game-tracker/game-tracker.module';
import { GameStatsModule } from '../../services/game-stats/game-stats.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([GameRoom, User]),
    UsersModule,
    PlayerCounterModule,
    WithdrawalModule,
    CacheModule,
    SkillStatsModule,
    GameTrackerModule,
    GameStatsModule,
  ],
  providers: [RoomsGateway, RoomsService],
  exports: [RoomsGateway, RoomsService],
})
export class RoomsModule {}

