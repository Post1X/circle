import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Wallet } from '../../entities/wallet.entity';
import {
  Transaction,
  TransactionStatus,
  TransactionType,
} from '../../entities/transaction.entity';
import { User } from '../../entities/user.entity';
import { AppConfigService } from '../../config/config.service';

@Injectable()
export class TronMonitorService implements OnModuleInit {
  private readonly logger = new Logger(TronMonitorService.name);
  private readonly tronApiUrl = 'https://api.trongrid.io';
  private readonly usdtContract = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t';
  private readonly confirmationThreshold = 3;
  private monitoring = false;

  constructor(
    @InjectRepository(Wallet)
    private walletRepository: Repository<Wallet>,
    @InjectRepository(Transaction)
    private transactionRepository: Repository<Transaction>,
    @InjectRepository(User)
    private userRepository: Repository<User>,
    private configService: AppConfigService,
  ) {
    // Constructor
  }

  async onModuleInit() {
    this.startMonitoring();
  }

  async startMonitoring() {
    if (this.monitoring) return;
    this.monitoring = true;
    this.logger.log('Starting Tron deposit monitoring...');

    while (this.monitoring) {
      try {
        await this.checkDeposits();
        await this.sleep(30000);
      } catch (error) {
        this.logger.error(`Error in monitoring: ${error.message}`);
        await this.sleep(60000);
      }
    }
  }

  stopMonitoring() {
    this.monitoring = false;
  }

  private async checkDeposits() {
    const addresses = await this.getAllUserAddresses();
    for (const address of addresses) {
      try {
        await this.checkAddressDeposits(address);
      } catch (error) {
        this.logger.error(`Error checking address ${address}: ${error.message}`);
      }
    }
  }

  private async getAllUserAddresses(): Promise<string[]> {
    const wallets = await this.walletRepository
      .createQueryBuilder('wallet')
      .where('wallet.user_id IS NOT NULL')
      .getMany();
    return wallets.map((w) => w.address);
  }

  private async checkAddressDeposits(address: string) {
    const url = `${this.tronApiUrl}/v1/accounts/${address}/transactions/trc20`;
    const params = {
      limit: 50,
      contract_address: this.usdtContract,
      only_confirmed: true,
      only_to: true,
    };
    const headers = {
      'TRON-PRO-API-KEY': this.configService.tronApiKey,
      'Content-Type': 'application/json',
    };

    try {
      const axios = require('axios');
      const response = await axios.get(url, { params, headers, timeout: 30000 });
      if (response.status === 200) {
        await this.processTransactions(address, response.data.data || []);
      } else if (response.status === 429) {
        this.logger.warn(`Rate limit exceeded for address ${address}`);
        await this.sleep(60000);
      }
    } catch (error) {
      this.logger.error(`HTTP error checking address ${address}: ${error.message}`);
    }
  }

  private async processTransactions(address: string, transactions: any[]) {
    for (const tx of transactions) {
      if (
        tx.to === address &&
        tx.token_info?.symbol === 'USDT'
      ) {
        await this.processDeposit(address, tx);
      }
    }
  }

  private async processDeposit(address: string, tx: any) {
    const txHash = tx.transaction_id;
    const amount = parseFloat(tx.value) / 1000000;
    const confirmations = tx.confirmed || 0;

    if (confirmations < this.confirmationThreshold) {
      return;
    }

    const existingTx = await this.getExistingTransaction(address, amount);
    if (existingTx) {
      return;
    }

    const wallet = await this.walletRepository.findOne({
      where: { address },
      relations: ['user'],
    });

    if (!wallet || !wallet.user) {
      return;
    }

    try {
      await this.createDepositTransaction(
        wallet.user.user_id,
        amount,
        txHash,
        address,
      );
      await this.topupBalance(wallet.user.user_id, amount);
      this.logger.log(
        `Deposit processed: ${amount} USDT for user ${wallet.user.user_id} from ${address}`,
      );
    } catch (error) {
      this.logger.error(
        `Failed to process deposit for user ${wallet.user.user_id}: ${error.message}`,
      );
    }
  }

  private async getExistingTransaction(
    address: string,
    amount: number,
  ): Promise<Transaction | null> {
    return await this.transactionRepository.findOne({
      where: {
        user_wallet_address: address,
        amount,
        type: TransactionType.INCOMING,
      },
      order: { created_at: 'DESC' },
    });
  }

  private async createDepositTransaction(
    userId: string,
    amount: number,
    txHash: string,
    address: string,
  ) {
    const transaction = this.transactionRepository.create({
      amount,
      status: TransactionStatus.CONFIRMED,
      type: TransactionType.INCOMING,
      user_wallet_address: address,
    });

    await this.transactionRepository.save(transaction);
  }

  private async topupBalance(userId: string, amount: number) {
    const user = await this.userRepository.findOne({
      where: { user_id: userId },
      lock: { mode: 'pessimistic_write' },
    });

    if (!user) {
      return;
    }

    const currentBalance = parseFloat(user.balance.toString());
    user.balance = currentBalance + amount;
    await this.userRepository.save(user);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

