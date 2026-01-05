import {
  Injectable,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, LessThanOrEqual } from 'typeorm';
import { WithdrawalRequest } from '../../entities/withdrawal-request.entity';
import { HotWallet } from '../../entities/hot-wallet.entity';
import { User } from '../../entities/user.entity';
import { WalletVerificationService } from '../../services/wallet-verification/wallet-verification.service';
import { BlockchainNetwork } from '../../modules/users/dto/wallet.dto';

@Injectable()
export class WithdrawalService {
  constructor(
    @InjectRepository(WithdrawalRequest)
    private withdrawalRepository: Repository<WithdrawalRequest>,
    @InjectRepository(HotWallet)
    private hotWalletRepository: Repository<HotWallet>,
    @InjectRepository(User)
    private userRepository: Repository<User>,
    private walletVerificationService: WalletVerificationService,
  ) {}

  async createWithdrawalRequest(
    userId: string,
    amount: number,
    toAddress: string,
    fee: number = 2.5,
  ): Promise<WithdrawalRequest> {
    if (
      !this.walletVerificationService.validateAddress(
        toAddress,
        BlockchainNetwork.TRON,
      )
    ) {
      throw new BadRequestException('Invalid TRON wallet address');
    }

    const withdrawal = this.withdrawalRepository.create({
      user_id: userId,
      amount,
      to_address: toAddress,
      fee,
      status: 'pending',
    });

    return await this.withdrawalRepository.save(withdrawal);
  }

  async getWithdrawalById(
    withdrawalId: number,
  ): Promise<WithdrawalRequest | null> {
    return await this.withdrawalRepository.findOne({
      where: { id: withdrawalId },
    });
  }

  async getUserWithdrawals(
    userId: string,
    limit: number = 50,
    offset: number = 0,
  ): Promise<WithdrawalRequest[]> {
    return await this.withdrawalRepository.find({
      where: { user_id: userId },
      order: { created_at: 'DESC' },
      take: limit,
      skip: offset,
    });
  }

  async getUserWithdrawalCount(userId: string): Promise<number> {
    return await this.withdrawalRepository.count({
      where: { user_id: userId },
    });
  }

  async getPendingWithdrawals(): Promise<WithdrawalRequest[]> {
    return await this.withdrawalRepository.find({
      where: { status: 'pending' },
    });
  }

  async getProcessingWithdrawals(): Promise<WithdrawalRequest[]> {
    return await this.withdrawalRepository.find({
      where: { status: 'processing' },
    });
  }

  async updateWithdrawalStatus(
    withdrawalId: number,
    status: string,
    transactionHash?: string,
    errorMessage?: string,
  ): Promise<boolean> {
    const updateData: any = {
      status,
    };

    if (status === 'completed' || status === 'failed') {
      updateData.processed_at = new Date();
    }

    if (transactionHash) {
      updateData.transaction_hash = transactionHash;
    }

    if (errorMessage) {
      updateData.error_message = errorMessage;
    }

    const result = await this.withdrawalRepository.update(
      withdrawalId,
      updateData,
    );

    return result.affected > 0;
  }

  async getWithdrawalStats(): Promise<{
    total_withdrawals: number;
    total_amount: number;
    pending_withdrawals: number;
    failed_withdrawals: number;
  }> {
    const [
      totalWithdrawals,
      completedWithdrawals,
      pendingWithdrawals,
      failedWithdrawals,
    ] = await Promise.all([
      this.withdrawalRepository.count(),
      this.withdrawalRepository.find({
        where: { status: 'completed' },
        select: ['amount'],
      }),
      this.withdrawalRepository.count({ where: { status: 'pending' } }),
      this.withdrawalRepository.count({ where: { status: 'failed' } }),
    ]);

    const totalAmount = completedWithdrawals.reduce(
      (sum, w) => sum + parseFloat(w.amount.toString()),
      0,
    );

    return {
      total_withdrawals: totalWithdrawals,
      total_amount: totalAmount,
      pending_withdrawals: pendingWithdrawals,
      failed_withdrawals: failedWithdrawals,
    };
  }

  async getActiveHotWallet(): Promise<HotWallet | null> {
    return await this.hotWalletRepository.findOne({
      where: { is_active: true },
    });
  }

  async createHotWallet(
    address: string,
    encryptedPrivateKey: string,
  ): Promise<HotWallet> {
    const hotWallet = this.hotWalletRepository.create({
      address,
      encrypted_private_key: encryptedPrivateKey,
      balance: 0,
      is_active: true,
    });

    return await this.hotWalletRepository.save(hotWallet);
  }

  async debitUserBalance(userId: string, amount: number): Promise<boolean> {
    const user = await this.userRepository.findOne({
      where: { user_id: userId },
      lock: { mode: 'pessimistic_write' },
    });

    if (!user) {
      return false;
    }

    const currentBalance = parseFloat(user.balance.toString());
    if (currentBalance < amount) {
      return false;
    }

    user.balance = currentBalance - amount;
    await this.userRepository.save(user);

    return true;
  }

  async creditUserBalance(userId: string, amount: number): Promise<boolean> {
    const user = await this.userRepository.findOne({
      where: { user_id: userId },
      lock: { mode: 'pessimistic_write' },
    });

    if (!user) {
      return false;
    }

    const currentBalance = parseFloat(user.balance.toString());
    const currentWinnings = parseFloat(user.total_winnings.toString());

    user.balance = currentBalance + amount;
    user.total_winnings = currentWinnings + amount;
    await this.userRepository.save(user);

    return true;
  }
}
