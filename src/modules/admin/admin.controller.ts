import { Controller, Get, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { AdminGuard } from '../auth/guards/admin.guard';
import { PlayerCounterService } from '../../services/player-counter/player-counter.service';

@Controller('admin')
export class AdminController {
  constructor(private playerCounterService: PlayerCounterService) {}

  @Get('active-players/real')
  @UseGuards(JwtAuthGuard, AdminGuard)
  async getRealActivePlayers() {
    const count = await this.playerCounterService.getRealCount();
    return {
      active_players: count,
      timestamp: 'real_time',
    };
  }
}


