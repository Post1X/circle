import {
  Controller,
  Get,
  Post,
  Body,
  Param,
  Query,
  UseGuards,
  HttpException,
  HttpStatus,
  ParseIntPipe,
} from '@nestjs/common';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { User } from '../../entities/user.entity';
import { WithdrawalService } from './withdrawal.service';
import {
  WithdrawalCreateDto,
  WithdrawalCreateResponseDto,
  WithdrawalStatusResponseDto,
  WithdrawalHistoryResponseDto,
  HotWalletResponseDto,
  WithdrawalStatsResponseDto,
} from './dto/withdrawal.dto';

@Controller('api/withdrawals')
export class WithdrawalController {
  constructor(private withdrawalService: WithdrawalService) {}

  @Post('request')
  @UseGuards(JwtAuthGuard)
  async createWithdrawalRequest(
    @CurrentUser() user: User,
    @Body() dto: WithdrawalCreateDto,
  ): Promise<WithdrawalCreateResponseDto> {
    try {
      const totalAmount = dto.amount + (dto.fee || 2.5);
      const userBalance = parseFloat(user.balance.toString());

      if (userBalance < totalAmount) {
        return {
          success: false,
          error: 'Недостаточно средств на балансе',
        };
      }

      if (dto.amount < 1.0) {
        return {
          success: false,
          error: 'Минимальная сумма для вывода: 1 USDT',
        };
      }

      if (dto.amount > 10000.0) {
        return {
          success: false,
          error: 'Максимальная сумма для вывода: 10000 USDT',
        };
      }

      const withdrawal = await this.withdrawalService.createWithdrawalRequest(
        user.user_id,
        dto.amount,
        dto.to_address,
        dto.fee || 2.5,
      );

      return {
        success: true,
        withdrawal_id: withdrawal.id,
        message: 'Запрос на вывод создан успешно',
      };
    } catch (error) {
      return {
        success: false,
        error: 'Ошибка создания запроса на вывод',
      };
    }
  }

  @Get('status/:id')
  @UseGuards(JwtAuthGuard)
  async getWithdrawalStatus(
    @CurrentUser() user: User,
    @Param('id', ParseIntPipe) withdrawalId: number,
  ): Promise<WithdrawalStatusResponseDto> {
    const withdrawal = await this.withdrawalService.getWithdrawalById(
      withdrawalId,
    );

    if (!withdrawal) {
      throw new HttpException(
        'Запрос на вывод не найден',
        HttpStatus.NOT_FOUND,
      );
    }

    if (withdrawal.user_id !== user.user_id) {
      throw new HttpException('Доступ запрещен', HttpStatus.FORBIDDEN);
    }

    return {
      id: withdrawal.id,
      status: withdrawal.status,
      amount: parseFloat(withdrawal.amount.toString()),
      to_address: withdrawal.to_address,
      transaction_hash: withdrawal.transaction_hash,
      error_message: withdrawal.error_message,
      created_at: withdrawal.created_at,
      processed_at: withdrawal.processed_at,
    };
  }

  @Get('history')
  @UseGuards(JwtAuthGuard)
  async getWithdrawalHistory(
    @CurrentUser() user: User,
    @Query('page', new ParseIntPipe({ optional: true })) page: number = 1,
    @Query('per_page', new ParseIntPipe({ optional: true }))
    perPage: number = 20,
  ): Promise<WithdrawalHistoryResponseDto> {
    const offset = (page - 1) * perPage;
    const withdrawals = await this.withdrawalService.getUserWithdrawals(
      user.user_id,
      perPage,
      offset,
    );
    const totalCount =
      await this.withdrawalService.getUserWithdrawalCount(user.user_id);

    return {
      withdrawals: withdrawals.map((w) => ({
        id: w.id,
        amount: parseFloat(w.amount.toString()),
        to_address: w.to_address,
        fee: parseFloat(w.fee.toString()),
        status: w.status,
        created_at: w.created_at,
        transaction_hash: w.transaction_hash,
        error_message: w.error_message,
      })),
      total_count: totalCount,
      page,
      per_page: perPage,
    };
  }

  @Get('hot-wallet')
  @UseGuards(JwtAuthGuard)
  async getHotWalletInfo(): Promise<HotWalletResponseDto> {
    const hotWallet = await this.withdrawalService.getActiveHotWallet();

    if (!hotWallet) {
      throw new HttpException(
        'Горячий кошелек не найден',
        HttpStatus.NOT_FOUND,
      );
    }

    return {
      address: hotWallet.address,
      balance: parseFloat(hotWallet.balance.toString()),
      is_active: hotWallet.is_active,
      last_updated: hotWallet.last_updated,
    };
  }

  @Get('stats')
  @UseGuards(JwtAuthGuard)
  async getWithdrawalStats(): Promise<WithdrawalStatsResponseDto> {
    const stats = await this.withdrawalService.getWithdrawalStats();
    const hotWallet = await this.withdrawalService.getActiveHotWallet();

    return {
      total_withdrawals: stats.total_withdrawals,
      total_amount: stats.total_amount,
      pending_withdrawals: stats.pending_withdrawals,
      failed_withdrawals: stats.failed_withdrawals,
      hot_wallet_balance: hotWallet
        ? parseFloat(hotWallet.balance.toString())
        : 0,
    };
  }

  @Post('cancel/:id')
  @UseGuards(JwtAuthGuard)
  async cancelWithdrawal(
    @CurrentUser() user: User,
    @Param('id', ParseIntPipe) withdrawalId: number,
  ): Promise<{ success: boolean; message: string }> {
    const withdrawal = await this.withdrawalService.getWithdrawalById(
      withdrawalId,
    );

    if (!withdrawal) {
      throw new HttpException(
        'Запрос на вывод не найден',
        HttpStatus.NOT_FOUND,
      );
    }

    if (withdrawal.user_id !== user.user_id) {
      throw new HttpException('Доступ запрещен', HttpStatus.FORBIDDEN);
    }

    if (withdrawal.status !== 'pending') {
      throw new HttpException(
        'Можно отменить только ожидающие запросы',
        HttpStatus.BAD_REQUEST,
      );
    }

    await this.withdrawalService.updateWithdrawalStatus(
      withdrawalId,
      'cancelled',
    );

    const refundAmount =
      parseFloat(withdrawal.amount.toString()) +
      parseFloat(withdrawal.fee.toString());
    await this.withdrawalService.creditUserBalance(user.user_id, refundAmount);

    return {
      success: true,
      message: 'Запрос на вывод отменен',
    };
  }
}
