import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { HotWalletInitService } from './hot-wallet-init.service';
import { HotWallet } from '../../entities/hot-wallet.entity';
import { ConfigModule } from '../../config/config.module';

@Module({
  imports: [TypeOrmModule.forFeature([HotWallet]), ConfigModule],
  providers: [HotWalletInitService],
  exports: [HotWalletInitService],
})
export class HotWalletInitModule {}


