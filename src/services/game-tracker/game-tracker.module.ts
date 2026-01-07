import { Module } from '@nestjs/common';
import { GameTrackerService } from './game-tracker.service';
import { ConfigModule } from '../config/config.module';

@Module({
  imports: [ConfigModule],
  providers: [GameTrackerService],
  exports: [GameTrackerService],
})
export class GameTrackerModule {}

