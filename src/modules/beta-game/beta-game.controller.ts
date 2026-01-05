import {
  Controller,
  Get,
  Post,
  Delete,
  Param,
  Body,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { BetaGameService } from './beta-game.service';

@Controller('api/beta-game')
export class BetaGameController {
  constructor(private betaGameService: BetaGameService) {}

  @Post('create')
  async createBetaGame(@Body() request: { player_id: string }) {
    try {
      const result = await this.betaGameService.createGame(
        request.player_id,
        10,
        1000.0,
      );
      return {
        success: true,
        game_id: result.gameId,
        message: 'Beta game created successfully',
      };
    } catch (error) {
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Get('state/:game_id')
  async getGameState(@Param('game_id') gameId: string) {
    try {
      return await this.betaGameService.getGameState(gameId);
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Post('move')
  async movePlayer(
    @Body()
    request: {
      game_id: string;
      player_id: string;
      dx: number;
      dy: number;
    },
  ) {
    try {
      await this.betaGameService.movePlayer(
        request.game_id,
        request.player_id,
        request.dx,
        request.dy,
      );
      return {
        success: true,
        message: 'Player moved successfully',
      };
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Post('skill')
  async activateSkill(
    @Body()
    request: {
      game_id: string;
      player_id: string;
      skill_type: string;
    },
  ) {
    try {
      const result = await this.betaGameService.activateSkill(
        request.game_id,
        request.player_id,
        request.skill_type,
      );
      return {
        success: result.success,
        message: result.message,
        data: result.data,
      };
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Post('vote')
  async submitVote(
    @Body()
    request: {
      game_id: string;
      player_id: string;
      vote: string;
    },
  ) {
    try {
      const result = await this.betaGameService.submitVote(
        request.game_id,
        request.player_id,
        request.vote,
      );
      return {
        success: result.success,
        message: result.message,
        data: result.data,
      };
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Post('exit')
  async exitGame(
    @Body()
    request: {
      game_id: string;
      player_id: string;
      exit_type: string;
    },
  ) {
    try {
      const result = await this.betaGameService.exitGame(
        request.game_id,
        request.player_id,
        request.exit_type,
      );
      return {
        success: true,
        message: 'Player exited successfully',
        data: result,
      };
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Get('phase/:game_id')
  async getGamePhase(@Param('game_id') gameId: string) {
    try {
      return await this.betaGameService.getGamePhaseInfo(gameId);
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Get('bonus-zones/:game_id')
  async getBonusZones(@Param('game_id') gameId: string) {
    try {
      return await this.betaGameService.getBonusZones(gameId);
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Get('leaderboard/:game_id')
  async getLeaderboard(@Param('game_id') gameId: string) {
    try {
      return await this.betaGameService.getLeaderboard(gameId);
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Get('results/:game_id')
  async getGameResults(@Param('game_id') gameId: string) {
    try {
      return await this.betaGameService.getGameResults(gameId);
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Delete('close/:game_id')
  async closeGame(@Param('game_id') gameId: string) {
    try {
      await this.betaGameService.closeGame(gameId);
      return {
        success: true,
        message: 'Game closed successfully',
      };
    } catch (error) {
      if (error.message === 'Game not found') {
        throw new HttpException('Game not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }
}
