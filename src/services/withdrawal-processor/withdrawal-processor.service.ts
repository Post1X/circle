import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { WithdrawalRequest } from '../../entities/withdrawal-request.entity';
import { HotWallet } from '../../entities/hot-wallet.entity';
import { User } from '../../entities/user.entity';
import { AppConfigService } from '../../config/config.service';
import { WithdrawalService } from '../../modules/withdrawal/withdrawal.service';

@Injectable()
export class WithdrawalProcessorService implements OnModuleInit {
  private readonly logger = new Logger(WithdrawalProcessorService.name);
  private readonly tronApiUrl = 'https://api.trongrid.io';
  private readonly usdtContract = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t';
  private readonly confirmationThreshold = 3;
  private processing = false;

  constructor(
    @InjectRepository(WithdrawalRequest)
    private withdrawalRepository: Repository<WithdrawalRequest>,
    @InjectRepository(HotWallet)
    private hotWalletRepository: Repository<HotWallet>,
    @InjectRepository(User)
    private userRepository: Repository<User>,
    private configService: AppConfigService,
    private withdrawalService: WithdrawalService,
  ) {}

  async onModuleInit() {
    this.startProcessing();
  }

  async startProcessing() {
    if (this.processing) return;
    this.processing = true;
    this.logger.log('Starting withdrawal processing...');

    while (this.processing) {
      try {
        await this.processPendingWithdrawals();
        await this.sleep(30000);
      } catch (error) {
        this.logger.error(`Error processing withdrawals: ${error.message}`);
        await this.sleep(60000);
      }
    }
  }

  stopProcessing() {
    this.processing = false;
  }

  private async processPendingWithdrawals() {
    const pending = await this.withdrawalService.getPendingWithdrawals();
    for (const withdrawal of pending) {
      try {
        await this.processSingleWithdrawal(withdrawal);
      } catch (error) {
        this.logger.error(
          `Error processing withdrawal ${withdrawal.id}: ${error.message}`,
        );
        await this.withdrawalService.updateWithdrawalStatus(
          withdrawal.id,
          'failed',
          undefined,
          error.message,
        );
      }
    }
  }

  private async processSingleWithdrawal(withdrawal: WithdrawalRequest) {
    await this.withdrawalService.updateWithdrawalStatus(
      withdrawal.id,
      'processing',
    );

    const hotWallet = await this.withdrawalService.getActiveHotWallet();
    if (!hotWallet) {
      this.logger.warn('No active hot wallet found. Withdrawals disabled.');
      await this.withdrawalService.updateWithdrawalStatus(
        withdrawal.id,
        'failed',
        undefined,
        'Withdrawal system not configured. Please contact administrator.',
      );
      return;
    }

    const realBalance = await this.getRealUsdtBalance(hotWallet.address);
    const requiredAmount =
      parseFloat(withdrawal.amount.toString()) +
      parseFloat(withdrawal.fee.toString());

    if (realBalance < requiredAmount) {
      throw new Error(
        `Insufficient funds in hot wallet. Required: ${requiredAmount}, Available: ${realBalance}`,
      );
    }

    try {
      const txHash = await this.sendUsdtTransaction(
        hotWallet,
        withdrawal.to_address,
        parseFloat(withdrawal.amount.toString()),
      );

      await this.withdrawalService.updateWithdrawalStatus(
        withdrawal.id,
        'completed',
        txHash,
      );

      await this.withdrawalService.debitUserBalance(
        withdrawal.user_id,
        requiredAmount,
      );

      this.logger.log(`Withdrawal ${withdrawal.id} completed. TX: ${txHash}`);
    } catch (error) {
      await this.withdrawalService.updateWithdrawalStatus(
        withdrawal.id,
        'failed',
        undefined,
        error.message,
      );
      throw error;
    }
  }

  private async getRealUsdtBalance(address: string): Promise<number> {
    const url = `${this.tronApiUrl}/v1/accounts/${address}/tokens`;
    const params = {
      contract_address: this.usdtContract,
    };
    const headers = {
      'TRON-PRO-API-KEY': this.configService.tronApiKey,
      'Content-Type': 'application/json',
    };

    try {
      const axios = require('axios');
      const response = await axios.get(url, { params, headers, timeout: 30000 });
      if (response.status === 200) {
        const tokens = response.data.data || [];
        for (const token of tokens) {
          if (token.contract_address === this.usdtContract) {
            return parseFloat(token.balance) / 1000000;
          }
        }
      }
      return 0;
    } catch (error) {
      this.logger.error(`Error getting balance for ${address}: ${error.message}`);
      return 0;
    }
  }

  private async sendUsdtTransaction(
    hotWallet: HotWallet,
    toAddress: string,
    amount: number,
  ): Promise<string> {
    const privateKey = this.decryptPrivateKey(hotWallet.encrypted_private_key);
    return await this.sendUsdtWithPrivateKey(privateKey, toAddress, amount);
  }

  private decryptPrivateKey(encryptedKey: string): string {
    const Fernet = require('fernet');
    const secret = new Fernet.Secret(this.configService.encryptionKey);
    const token = new Fernet.Token({
      secret: secret,
      token: encryptedKey,
      ttl: 0,
    });
    return token.decode();
  }

  private async sendUsdtWithPrivateKey(
    privateKey: string,
    toAddress: string,
    amount: number,
  ): Promise<string> {
    const url = `${this.tronApiUrl}/wallet/createtransaction`;
    const amountSun = Math.floor(amount * 1000000);

    const data = {
      to_address: toAddress,
      owner_address: privateKey,
      amount: amountSun,
      contract_address: this.usdtContract,
    };

    const headers = {
      'TRON-PRO-API-KEY': this.configService.tronApiKey,
      'Content-Type': 'application/json',
    };

    try {
      const axios = require('axios');
      const response = await axios.post(url, data, { headers, timeout: 60000 });
      if (response.status === 200) {
        const txHash = response.data.txID;
        if (txHash) {
          return txHash;
        } else {
          throw new Error(`Transaction creation failed: ${JSON.stringify(response.data)}`);
        }
      } else {
        throw new Error(`TronGrid API error: ${response.status}`);
      }
    } catch (error) {
      throw new Error(`Error sending USDT: ${error.message}`);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}


