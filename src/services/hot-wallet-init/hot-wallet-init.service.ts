import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { HotWallet } from '../../entities/hot-wallet.entity';
import { AppConfigService } from '../../config/config.service';

@Injectable()
export class HotWalletInitService implements OnModuleInit {
  private readonly logger = new Logger(HotWalletInitService.name);

  constructor(
    @InjectRepository(HotWallet)
    private hotWalletRepository: Repository<HotWallet>,
    private configService: AppConfigService,
  ) {}

  async onModuleInit() {
    await this.initHotWallet();
  }

  async initHotWallet(): Promise<void> {
    try {
      const existingWallet = await this.hotWalletRepository.findOne({
        where: { is_active: true },
      });

      if (existingWallet) {
        this.logger.log(`Hot wallet already exists: ${existingWallet.address}`);
        return;
      }

      const mnemonic = this.configService.mnemonic;
      const encryptionKey = this.configService.encryptionKey;

      if (!mnemonic || !encryptionKey) {
        this.logger.warn(
          'MNEMONIC or ENCRYPTION_KEY not configured. Hot wallet initialization skipped.',
        );
        return;
      }

      const { address, privateKey } = await this.generateTronWallet(mnemonic);
      const encryptedPrivateKey = this.encryptPrivateKey(
        privateKey,
        encryptionKey,
      );

      const hotWallet = this.hotWalletRepository.create({
        address,
        encrypted_private_key: encryptedPrivateKey,
        balance: 0,
        is_active: true,
      });

      await this.hotWalletRepository.save(hotWallet);

      this.logger.log('Hot wallet created successfully!');
      this.logger.log(`Address: ${hotWallet.address}`);
      this.logger.warn(
        'Please fund this wallet with USDT for withdrawals to work',
      );
      this.logger.warn('Without funding, withdrawals will fail!');
    } catch (error) {
      this.logger.error(`Hot wallet initialization failed: ${error.message}`);
      this.logger.warn(
        'System will work for deposits only. Withdrawals will be disabled.',
      );
    }
  }

  private async generateTronWallet(mnemonic: string): Promise<{
    address: string;
    privateKey: string;
  }> {
    try {
      const bip39 = require('bip39');
      const hdkey = require('hdkey');
      const TronWeb = require('tronweb');

      const seed = await bip39.mnemonicToSeed(mnemonic);
      const root = hdkey.fromMasterSeed(seed);

      const tronPath = "m/44'/195'/0'/0/999999";
      const child = root.derive(tronPath);

      const privateKey = child.privateKey.toString('hex');

      const tronWeb = new TronWeb({
        fullHost: 'https://api.trongrid.io',
      });

      const address = tronWeb.address.fromPrivateKey(privateKey);

      return {
        address,
        privateKey,
      };
    } catch (error) {
      this.logger.error(`Error generating Tron wallet: ${error.message}`);
      const TronWeb = require('tronweb');
      const tronWeb = new TronWeb({
        fullHost: 'https://api.trongrid.io',
      });
      const account = tronWeb.createAccount();
      return {
        address: account.address.base58,
        privateKey: account.privateKey,
      };
    }
  }

  private encryptPrivateKey(privateKey: string, encryptionKey: string): string {
    const Fernet = require('fernet');
    const secret = new Fernet.Secret(encryptionKey);
    const token = new Fernet.Token({
      secret: secret,
    });
    return token.encode(privateKey);
  }
}


