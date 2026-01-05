import { Controller, Get } from '@nestjs/common';
import { PlayerCounterService } from '../../services/player-counter/player-counter.service';

@Controller('api')
export class PublicController {
  constructor(private playerCounterService: PlayerCounterService) {}

  @Get('health')
  health() {
    return { status: 'all good' };
  }

  @Get('active-players')
  async getActivePlayers() {
    const count = await this.playerCounterService.getFakeCount();
    return {
      active_players: count,
      timestamp: 'display_value',
    };
  }
}


