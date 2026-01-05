import { Module } from '@nestjs/common';
import { BetaGameController } from './beta-game.controller';
import { BetaGameService } from './beta-game.service';

@Module({
  controllers: [BetaGameController],
  providers: [BetaGameService],
})
export class BetaGameModule {}


