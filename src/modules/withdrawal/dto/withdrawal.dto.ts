import { IsString, IsNumber, Min, Max, MinLength, MaxLength } from 'class-validator';

export class WithdrawalCreateDto {
  @IsNumber()
  @Min(0.01)
  amount: number;

  @IsString()
  @MinLength(34)
  @MaxLength(34)
  to_address: string;

  @IsNumber()
  @Min(0)
  fee?: number = 2.5;
}

export class WithdrawalResponseDto {
  id: number;
  amount: number;
  to_address: string;
  fee: number;
  status: string;
  created_at: Date;
  transaction_hash?: string | null;
  error_message?: string | null;
}

export class WithdrawalStatusResponseDto {
  id: number;
  status: string;
  amount: number;
  to_address: string;
  transaction_hash?: string | null;
  error_message?: string | null;
  created_at: Date;
  processed_at?: Date | null;
}

export class WithdrawalHistoryResponseDto {
  withdrawals: WithdrawalResponseDto[];
  total_count: number;
  page: number;
  per_page: number;
}

export class WithdrawalCreateResponseDto {
  success: boolean;
  withdrawal_id?: number;
  message?: string;
  error?: string;
}

export class HotWalletResponseDto {
  address: string;
  balance: number;
  is_active: boolean;
  last_updated: Date;
}

export class WithdrawalStatsResponseDto {
  total_withdrawals: number;
  total_amount: number;
  pending_withdrawals: number;
  failed_withdrawals: number;
  hot_wallet_balance: number;
}


