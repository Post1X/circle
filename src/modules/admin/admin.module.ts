import { Global, Module } from '@nestjs/common';
import { AdminController } from './admin.controller';
import { PlayerCounterService } from '../../services/player-counter/player-counter.service';

@Global()
@Module({
  controllers: [AdminController],
  providers: [PlayerCounterService],
  exports: [PlayerCounterService],
})
export class AdminModule {}

