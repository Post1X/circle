import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { AppConfigService } from '../config/config.service';
import { join } from 'path';

export const getDatabaseConfig = (
  configService: AppConfigService,
): TypeOrmModuleOptions => {
  return {
    type: 'postgres',
    host: configService.dbHost || 'db',
    port: configService.dbPort || 5432,
    username: configService.dbUser,
    password: configService.dbPass,
    database: configService.dbName,
    entities: [join(__dirname, '..', '**', '*.entity{.ts,.js}')],
    migrations: [join(__dirname, '..', 'migrations', '*.{.ts,.js}')],
    extra: {
      max: 20,
      min: 5,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    },
    synchronize: false,
    logging: configService.mode === 'test',
    autoLoadEntities: true,
    keepConnectionAlive: true,
    retryAttempts: 3,
    retryDelay: 3000,
    ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false,
  };
};

