import { Module } from '@nestjs/common';
import { WalletVerificationService } from './wallet-verification.service';

@Module({
  providers: [WalletVerificationService],
  exports: [WalletVerificationService],
})
export class WalletVerificationModule {}

