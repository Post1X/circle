import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { Inject } from '@nestjs/common';
import { Redis } from 'ioredis';
import { AppConfigService } from '../../config/config.service';

@Injectable()
export class TokenService implements OnModuleInit, OnModuleDestroy {
  private redis: Redis;

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

  async addToBlacklist(token: string, expiresIn: number = 24 * 60 * 60): Promise<void> {
    await this.redis.setex(`blacklist:${token}`, expiresIn, '1');
  }

  async isBlacklisted(token: string): Promise<boolean> {
    const result = await this.redis.exists(`blacklist:${token}`);
    return result === 1;
  }

  async removeFromBlacklist(token: string): Promise<void> {
    await this.redis.del(`blacklist:${token}`);
  }
}


