import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { WithdrawalProcessorService } from './withdrawal-processor.service';
import { WithdrawalRequest } from '../../entities/withdrawal-request.entity';
import { HotWallet } from '../../entities/hot-wallet.entity';
import { User } from '../../entities/user.entity';
import { WithdrawalModule } from '../../modules/withdrawal/withdrawal.module';
import { ConfigModule } from '../../config/config.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([WithdrawalRequest, HotWallet, User]),
    WithdrawalModule,
    ConfigModule,
  ],
  providers: [WithdrawalProcessorService],
  exports: [WithdrawalProcessorService],
})
export class WithdrawalProcessorModule {}


