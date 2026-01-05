import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { GameRoom } from '../../entities/game-room.entity';
import { RoomsGateway } from './rooms.gateway';
import { RoomsService } from './rooms.service';
import { UsersModule } from '../users/users.module';
import { PlayerCounterModule } from '../../services/player-counter/player-counter.module';
import { WithdrawalModule } from '../withdrawal/withdrawal.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([GameRoom]),
    UsersModule,
    PlayerCounterModule,
    WithdrawalModule,
  ],
  providers: [RoomsGateway, RoomsService],
  exports: [RoomsGateway, RoomsService],
})
export class RoomsModule {}

