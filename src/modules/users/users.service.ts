import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Not } from 'typeorm';
import { User } from '../../entities/user.entity';
import { Wallet } from '../../entities/wallet.entity';
import { Nonce } from '../../entities/nonce.entity';
import { AuthService } from '../auth/auth.service';
import { AppConfigService } from '../../config/config.service';
import { WalletVerificationService } from '../../services/wallet-verification/wallet-verification.service';
import { WalletType, BlockchainNetwork } from './dto/wallet.dto';
import * as crypto from 'crypto';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
    @InjectRepository(Wallet)
    private walletRepository: Repository<Wallet>,
    @InjectRepository(Nonce)
    private nonceRepository: Repository<Nonce>,
    private authService: AuthService,
    private configService: AppConfigService,
    private walletVerificationService: WalletVerificationService,
  ) {}

  async createUser(username: string, password: string): Promise<User> {
    const existingUser = await this.userRepository.findOne({
      where: { username },
    });

    if (existingUser) {
      throw new ConflictException('User already exists');
    }

    const hashedPassword = await this.authService.hashPassword(password);
    const user = this.userRepository.create({
      username,
      hashed_password: hashedPassword,
      balance: 0,
      games_played: 0,
      total_winnings: 0,
      leaderboard_rank: 0,
      is_admin: false,
    });

    return await this.userRepository.save(user);
  }

  async getUserById(userId: string): Promise<User> {
    const user = await this.userRepository.findOne({
      where: { user_id: userId },
    });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    return user;
  }

  async getUserByUsername(username: string): Promise<User | null> {
    return await this.userRepository.findOne({
      where: { username },
    });
  }

  async getUserByWalletAddress(address: string): Promise<User | null> {
    const wallet = await this.walletRepository.findOne({
      where: { address },
      relations: ['user'],
    });

    return wallet?.user || null;
  }

  async updateUsername(userId: string, newUsername: string): Promise<User> {
    const user = await this.getUserById(userId);
    user.username = newUsername;
    return await this.userRepository.save(user);
  }

  async createNonce(address: string): Promise<string> {
    const nonceValue = crypto.randomBytes(32).toString('hex');
    
    await this.nonceRepository.update(
      { address, used: false },
      { used: true },
    );

    const nonce = this.nonceRepository.create({
      address,
      nonce: nonceValue,
      used: false,
    });

    await this.nonceRepository.save(nonce);
    return nonceValue;
  }

  async getNonce(address: string, nonceValue: string): Promise<Nonce | null> {
    return await this.nonceRepository.findOne({
      where: { address, nonce: nonceValue, used: false },
    });
  }

  async markNonceAsUsed(nonce: Nonce): Promise<void> {
    nonce.used = true;
    await this.nonceRepository.save(nonce);
  }

  async bindWalletToUser(
    userId: string,
    address: string,
    walletType: WalletType,
    verifySignature: boolean = true,
    message?: string,
    signature?: string,
  ): Promise<Wallet> {
    const existingWallet = await this.walletRepository.findOne({
      where: { address },
    });

    if (existingWallet) {
      if (existingWallet.user_id === userId) {
        return existingWallet;
      }
      throw new ConflictException('Wallet already bound to another user');
    }

    const network = this.walletVerificationService.getNetworkFromWalletType(
      walletType,
    );

    if (!this.walletVerificationService.validateAddress(address, network)) {
      throw new ConflictException('Invalid wallet address');
    }

    if (verifySignature && message && signature) {
      const isValid = await this.walletVerificationService.verifySignature(
        walletType,
        address,
        message,
        signature,
      );

      if (!isValid) {
        throw new ConflictException('Invalid signature');
      }
    }

    const userWallets = await this.walletRepository.find({
      where: { user_id: userId },
    });

    const isPrimary = userWallets.length === 0;

    const wallet = this.walletRepository.create({
      user_id: userId,
      address,
      network,
      wallet_type: walletType,
      is_primary: isPrimary,
    });

    return await this.walletRepository.save(wallet);
  }

  async getUserWallets(userId: string): Promise<Wallet[]> {
    return await this.walletRepository.find({
      where: { user_id: userId },
      order: { is_primary: 'DESC', created_at: 'DESC' },
    });
  }

  async unbindWallet(userId: string, walletId: number): Promise<void> {
    const wallet = await this.walletRepository.findOne({
      where: { id: walletId, user_id: userId },
    });

    if (!wallet) {
      throw new NotFoundException('Wallet not found');
    }

    if (wallet.is_primary) {
      const otherWallets = await this.walletRepository.find({
        where: { user_id: userId, id: Not(walletId) },
      });

      if (otherWallets.length > 0) {
        otherWallets[0].is_primary = true;
        await this.walletRepository.save(otherWallets[0]);
      }
    }

    await this.walletRepository.remove(wallet);
  }

  async setPrimaryWallet(userId: string, walletId: number): Promise<Wallet> {
    const wallet = await this.walletRepository.findOne({
      where: { id: walletId, user_id: userId },
    });

    if (!wallet) {
      throw new NotFoundException('Wallet not found');
    }

    await this.walletRepository.update(
      { user_id: userId },
      { is_primary: false },
    );

    wallet.is_primary = true;
    return await this.walletRepository.save(wallet);
  }

  async verifyWalletSignature(
    walletType: WalletType,
    address: string,
    message: string,
    signature: string,
  ): Promise<boolean> {
    return await this.walletVerificationService.verifySignature(
      walletType,
      address,
      message,
      signature,
    );
  }

  async getDepositAddress(userId: string): Promise<string> {
    const existingWallet = await this.walletRepository.findOne({
      where: { user_id: userId, is_primary: false },
      order: { created_at: 'DESC' },
    });

    if (existingWallet) {
      const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
      if (existingWallet.created_at > tenMinutesAgo) {
        return existingWallet.address;
      }
    }

    const walletCount = await this.walletRepository.count();
    const newAddress = await this.generateTronAddress(walletCount + 1);

    const wallet = this.walletRepository.create({
      user_id: userId,
      address: newAddress,
      network: 'tron',
      is_primary: false,
    });

    await this.walletRepository.save(wallet);
    return newAddress;
  }

  private async generateTronAddress(index: number): Promise<string> {
    const mnemonic = this.configService.mnemonic;

    if (!mnemonic) {
      throw new Error('MNEMONIC not configured');
    }

    try {
      const bip39 = require('bip39');
      const hdkey = require('hdkey');
      const TronWeb = require('tronweb');

      const seed = await bip39.mnemonicToSeed(mnemonic);
      const root = hdkey.fromMasterSeed(seed);

      const tronPath = `m/44'/195'/0'/0/${index}`;
      const child = root.derive(tronPath);

      const privateKey = child.privateKey.toString('hex');

      const tronWeb = new TronWeb({
        fullHost: 'https://api.trongrid.io',
      });

      return tronWeb.address.fromPrivateKey(privateKey);
    } catch (error) {
      const TronWeb = require('tronweb');
      const tronWeb = new TronWeb({
        fullHost: 'https://api.trongrid.io',
      });
      const account = tronWeb.createAccount();
      return account.address.base58;
    }
  }
}

