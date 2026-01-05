import { IsString, MinLength, MaxLength, IsNotEmpty } from 'class-validator';
export * from './wallet.dto';

export class UserRegisterDto {
  @IsString()
  @MinLength(3)
  @MaxLength(15)
  username: string;

  @IsString()
  @MinLength(8)
  @MaxLength(35)
  password: string;
}

export class UserLoginDto {
  @IsString()
  @MinLength(3)
  @MaxLength(15)
  username: string;

  @IsString()
  @MinLength(8)
  @MaxLength(35)
  password: string;
}

export class UserLoginResponseDto {
  access_token: string;
  user_id: string;
  username: string;
}

export class UpdateUsernameDto {
  @IsString()
  @MinLength(3)
  @MaxLength(20)
  username: string;
}

export class BalanceResponseDto {
  balance: number;
  total_winnings: number;
  games_played: number;
}

export class TronAddressResponseDto {
  address: string;
  network: string;
  message: string;
}

export class DepositStatusResponseDto {
  status: string;
  amount?: number;
  transaction_hash?: string;
  confirmations?: number;
  message: string;
}


