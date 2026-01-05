import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { Redis } from 'ioredis';
import { AppConfigService } from '../../config/config.service';

@Injectable()
export class PlayerCounterService
  implements OnModuleInit, OnModuleDestroy
{
  private redis: Redis;
  private realCountKey = 'active_players:real';
  private fakeCountKey = 'active_players:fake';
  private targetFakeCount = 9000;
  private fakeCountVariance = 1000;

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

  async incrementRealCount(userId: string): Promise<number> {
    const pipe = this.redis.pipeline();
    pipe.hincrby(this.realCountKey, userId, 1);
    pipe.expire(this.realCountKey, 300);
    const results = await pipe.exec();
    return results[0][1] as number;
  }

  async decrementRealCount(userId: string): Promise<number> {
    const pipe = this.redis.pipeline();
    pipe.hincrby(this.realCountKey, userId, -1);
    pipe.expire(this.realCountKey, 300);
    const results = await pipe.exec();
    return results[0][1] as number;
  }

  async getRealCount(): Promise<number> {
    const count = await this.redis.hlen(this.realCountKey);
    return count;
  }

  async getFakeCount(): Promise<number> {
    const count = await this.redis.get(this.fakeCountKey);
    if (!count) {
      await this.updateFakeCount();
      const newCount = await this.redis.get(this.fakeCountKey);
      return newCount ? parseInt(newCount) : this.targetFakeCount;
    }
    return parseInt(count);
  }

  async updateFakeCount(): Promise<void> {
    const currentFake = await this.redis.get(this.fakeCountKey);
    const current = currentFake ? parseInt(currentFake) : this.targetFakeCount;

    let newCount: number;
    if (current < this.targetFakeCount) {
      const change = Math.floor(Math.random() * 150) + 50;
      newCount = Math.min(current + change, this.targetFakeCount);
    } else if (current > this.targetFakeCount) {
      const change = Math.floor(Math.random() * 150) + 50;
      newCount = Math.max(current - change, this.targetFakeCount);
    } else {
      const variance =
        Math.floor(Math.random() * (this.fakeCountVariance * 2 + 1)) -
        this.fakeCountVariance;
      newCount = this.targetFakeCount + variance;
    }

    await this.redis.setex(this.fakeCountKey, 3600, newCount.toString());
  }
}


