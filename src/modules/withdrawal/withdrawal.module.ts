import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { WithdrawalController } from './withdrawal.controller';
import { WithdrawalService } from './withdrawal.service';
import { WithdrawalRequest } from '../../entities/withdrawal-request.entity';
import { HotWallet } from '../../entities/hot-wallet.entity';
import { User } from '../../entities/user.entity';
import { WalletVerificationModule } from '../../services/wallet-verification/wallet-verification.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([WithdrawalRequest, HotWallet, User]),
    WalletVerificationModule,
  ],
  controllers: [WithdrawalController],
  providers: [WithdrawalService],
  exports: [WithdrawalService],
})
export class WithdrawalModule {}

