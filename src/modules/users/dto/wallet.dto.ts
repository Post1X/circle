import { IsString, IsNotEmpty, IsEnum, IsOptional } from 'class-validator';

export enum WalletType {
  TRONLINK = 'tronlink',
  SOLFLARE = 'solflare',
  PHANTOM = 'phantom',
  LEDGER = 'ledger',
  TORUS = 'torus',
  SOLONG = 'solong',
  SAFEPAL = 'safepal',
  METAMASK = 'metamask',
}

export enum BlockchainNetwork {
  TRON = 'tron',
  SOLANA = 'solana',
  ETHEREUM = 'ethereum',
  BSC = 'bsc',
  POLYGON = 'polygon',
}

export class WalletAuthDto {
  @IsString()
  @IsNotEmpty()
  address: string;

  @IsEnum(WalletType)
  @IsOptional()
  wallet_type?: WalletType;
}

export class WalletConnectDto {
  @IsString()
  @IsNotEmpty()
  address: string;

  @IsString()
  @IsNotEmpty()
  signature: string;

  @IsString()
  @IsNotEmpty()
  nonce: string;

  @IsString()
  @IsNotEmpty()
  message: string;

  @IsEnum(WalletType)
  @IsNotEmpty()
  wallet_type: WalletType;
}

export class WalletBindDto {
  @IsString()
  @IsNotEmpty()
  address: string;

  @IsString()
  @IsNotEmpty()
  signature: string;

  @IsString()
  @IsNotEmpty()
  message: string;

  @IsEnum(WalletType)
  @IsNotEmpty()
  wallet_type: WalletType;
}

export class WalletResponseDto {
  id: number;
  address: string;
  network: string;
  wallet_type: WalletType;
  is_primary: boolean;
  created_at: Date;
}

