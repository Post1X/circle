import { Injectable } from '@nestjs/common';
import { CacheService } from '../cache/cache.service';

@Injectable()
export class SkillStatsService {
  private readonly STATS_KEY_PREFIX = 'skill_stats:';
  private readonly STATS_BATCH_KEY = 'skill_stats:batch';

  constructor(private cacheService: CacheService) {}

  async recordSkillUsage(
    userId: string,
    sessionId: string,
    skillType: string,
    cost: number,
    balanceBefore: number,
    balanceAfter: number,
    isFree: boolean,
  ): Promise<void> {
    const statsKey = `${this.STATS_KEY_PREFIX}${sessionId}:${userId}`;
    const usage = {
      user_id: userId,
      session_id: sessionId,
      skill_type: skillType,
      cost,
      balance_before: balanceBefore,
      balance_after: balanceAfter,
      is_free: isFree,
      created_at: new Date().toISOString(),
    };

    const existing = await this.cacheService.get<any[]>(statsKey) || [];
    existing.push(usage);
    await this.cacheService.set(statsKey, existing, 86400);

    const keysKey = `${this.STATS_KEY_PREFIX}${sessionId}:keys`;
    const keys = await this.cacheService.get<string[]>(keysKey) || [];
    if (!keys.includes(statsKey)) {
      keys.push(statsKey);
      await this.cacheService.set(keysKey, keys, 86400);
    }

    await this.cacheService.set(
      `${this.STATS_BATCH_KEY}:${sessionId}`,
      sessionId,
      86400,
    );
  }

  async getSkillStatsForSession(sessionId: string): Promise<any[]> {
    const pattern = `${this.STATS_KEY_PREFIX}${sessionId}:*`;
    const keys = await this.cacheService.get<string[]>(`${this.STATS_KEY_PREFIX}${sessionId}:keys`) || [];
    const allStats: any[] = [];
    
    for (const key of keys) {
      const stats = await this.cacheService.get<any[]>(key);
      if (stats) {
        allStats.push(...stats);
      }
    }
    
    return allStats;
  }

  async getPlayerSkillStatsForSession(sessionId: string, userId: string): Promise<any[]> {
    const statsKey = `${this.STATS_KEY_PREFIX}${sessionId}:${userId}`;
    return await this.cacheService.get<any[]>(statsKey) || [];
  }

  async clearSessionStats(sessionId: string): Promise<void> {
    const pattern = `${this.STATS_KEY_PREFIX}${sessionId}:*`;
  }
}

