import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class AppConfigService {
  constructor(private configService: ConfigService) {}

  get dbName(): string {
    return this.configService.get<string>('DB_NAME');
  }

  get dbPass(): string {
    return this.configService.get<string>('DB_PASS');
  }

  get dbHost(): string {
    return this.configService.get<string>('DB_HOST');
  }

  get dbPort(): number {
    return this.configService.get<number>('DB_PORT');
  }

  get dbUser(): string {
    return this.configService.get<string>('DB_USER');
  }

  get mode(): 'test' | 'prod' {
    return (this.configService.get<string>('MODE') || 'prod') as 'test' | 'prod';
  }

  get algorithm(): string {
    return this.configService.get<string>('ALGORITHM');
  }

  get secretKey(): string {
    return this.configService.get<string>('SECRET_KEY');
  }

  get redisHost(): string {
    return this.configService.get<string>('REDIS_HOST');
  }

  get redisPort(): number {
    return this.configService.get<number>('REDIS_PORT');
  }

  get mnemonic(): string {
    return this.configService.get<string>('MNEMONIC');
  }

  get tronApiKey(): string {
    return this.configService.get<string>('TRON_API_KEY');
  }

  get encryptionKey(): string {
    return this.configService.get<string>('ENCRYPTION_KEY');
  }

  get databaseUrl(): string {
    return `postgresql://${this.dbUser}:${this.dbPass}@${this.dbHost}:${this.dbPort}/${this.dbName}`;
  }
}


