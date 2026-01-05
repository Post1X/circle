import { Controller, Get, Post, Param, Body } from '@nestjs/common';
import { GameService } from './game.service';

@Controller('api/game')
export class GameController {
  constructor(private gameService: GameService) {}

  @Get('bonus-zones-info')
  async getBonusZonesInfo(@Param('game_id') gameId: string) {
    return this.gameService.getBonusZones(gameId);
  }

  @Get('leaderboard')
  async getGameLeaderboard(@Param('game_id') gameId: string) {
    return this.gameService.getLeaderboard(gameId);
  }

  @Get('game-phase')
  async getGamePhase(@Param('game_id') gameId: string) {
    return this.gameService.getGamePhase(gameId);
  }

  @Post(':game_id/exit')
  async exitGame(
    @Param('game_id') gameId: string,
    @Body('user_id') userId: number,
  ) {
    this.gameService.removePlayer(gameId, userId.toString());
  }
}
