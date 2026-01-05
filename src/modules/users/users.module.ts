import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { User } from '../../entities/user.entity';
import { Wallet } from '../../entities/wallet.entity';
import { Nonce } from '../../entities/nonce.entity';
import { Transaction } from '../../entities/transaction.entity';
import { AuthModule } from '../auth/auth.module';
import { ConfigModule } from '../../config/config.module';
import { WalletVerificationModule } from '../../services/wallet-verification/wallet-verification.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([User, Wallet, Nonce, Transaction]),
    AuthModule,
    ConfigModule,
    WalletVerificationModule,
  ],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService],
})
export class UsersModule {}


