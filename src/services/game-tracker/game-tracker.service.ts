import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { Redis } from 'ioredis';
import { AppConfigService } from '../../config/config.service';

@Injectable()
export class GameTrackerService implements OnModuleInit, OnModuleDestroy {
  private redis: Redis;
  private readonly PLAYER_ROOM_KEY_PREFIX = 'player:room:';
  private readonly ROOM_PLAYERS_KEY_PREFIX = 'room:players:';

  constructor(private configService: AppConfigService) {}

  async onModuleInit() {
    const Redis = require('ioredis');
    this.redis = new Redis({
      host: this.configService.redisHost,
      port: this.configService.redisPort,
    });
  }

  async onModuleDestroy() {
    if (this.redis) {
      await this.redis.quit();
    }
  }

  async setPlayerInRoom(userId: string, roomId: string): Promise<void> {
    await this.redis.setex(
      `${this.PLAYER_ROOM_KEY_PREFIX}${userId}`,
      3600,
      roomId,
    );
    await this.redis.sadd(`${this.ROOM_PLAYERS_KEY_PREFIX}${roomId}`, userId);
    await this.redis.expire(`${this.ROOM_PLAYERS_KEY_PREFIX}${roomId}`, 3600);
  }

  async removePlayerFromRoom(userId: string, roomId?: string): Promise<void> {
    if (!roomId) {
      roomId = await this.redis.get(`${this.PLAYER_ROOM_KEY_PREFIX}${userId}`);
    }
    await this.redis.del(`${this.PLAYER_ROOM_KEY_PREFIX}${userId}`);
    if (roomId) {
      await this.redis.srem(`${this.ROOM_PLAYERS_KEY_PREFIX}${roomId}`, userId);
    }
  }

  async getPlayerRoom(userId: string): Promise<string | null> {
    return await this.redis.get(`${this.PLAYER_ROOM_KEY_PREFIX}${userId}`);
  }

  async isPlayerInGame(userId: string): Promise<boolean> {
    const roomId = await this.getPlayerRoom(userId);
    if (!roomId) {
      return false;
    }
    const { get_game } = await import('../../game');
    const game = await get_game(roomId);
    return game ? game.players.has(userId) : false;
  }
}

