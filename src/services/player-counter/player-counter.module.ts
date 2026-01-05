import { Module } from '@nestjs/common';
import { PlayerCounterService } from './player-counter.service';
import { ConfigModule } from '../../config/config.module';

@Module({
  imports: [ConfigModule],
  providers: [PlayerCounterService],
  exports: [PlayerCounterService],
})
export class PlayerCounterModule {}


