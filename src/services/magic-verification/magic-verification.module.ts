import { Module } from '@nestjs/common';
import { MagicVerificationService } from './magic-verification.service';
import { ConfigModule } from '../../config/config.module';

@Module({
  imports: [ConfigModule],
  providers: [MagicVerificationService],
  exports: [MagicVerificationService],
})
export class MagicVerificationModule {}

