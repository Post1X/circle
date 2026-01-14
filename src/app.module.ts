import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ServeStaticModule } from '@nestjs/serve-static';
import { WinstonModule } from 'nest-winston';
import { join } from 'path';

import { AppConfigService } from './config/config.service';
import { ConfigModule as AppConfigModule } from './config/config.module';
import { DatabaseModule } from './database/database.module';
import { getDatabaseConfig } from './database/database.config';
import { getWinstonConfig } from './config/winston.config';
import { TokenModule } from './services/token/token.module';
import { AuthModule } from './modules/auth/auth.module';
import { UsersModule } from './modules/users/users.module';
import { RoomsModule } from './modules/rooms/rooms.module';
import { GameModule } from './modules/game/game.module';
import { AdminModule } from './modules/admin/admin.module';
import { WithdrawalModule } from './modules/withdrawal/withdrawal.module';
import { PublicModule } from './modules/public/public.module';
import { BetaGameModule } from './modules/beta-game/beta-game.module';
import { SkillsModule } from './modules/skills/skills.module';
import { TronMonitorModule } from './services/tron-monitor/tron-monitor.module';
import { WithdrawalProcessorModule } from './services/withdrawal-processor/withdrawal-processor.module';
import { HotWalletInitModule } from './services/hot-wallet-init/hot-wallet-init.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    AppConfigModule,
    WinstonModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: AppConfigService) =>
        getWinstonConfig(configService),
      inject: [AppConfigService],
    }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: AppConfigService) =>
        getDatabaseConfig(configService),
      inject: [AppConfigService],
    }),
    ServeStaticModule.forRoot({
      rootPath: join(process.cwd(), 'static'),
      serveRoot: '/static',
    }),
    DatabaseModule,
    TokenModule,
    AuthModule,
    UsersModule,
    RoomsModule,
    GameModule,
    AdminModule,
    WithdrawalModule,
    PublicModule,
    BetaGameModule,
    SkillsModule,
    TronMonitorModule,
    WithdrawalProcessorModule,
    HotWalletInitModule,
  ],
})
export class AppModule {}

