import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  OneToMany,
  Index,
} from 'typeorm';
import { Wallet } from './wallet.entity';
import { WithdrawalRequest } from './withdrawal-request.entity';

@Entity('user')
export class User {
  @PrimaryGeneratedColumn('uuid')
  @Index()
  user_id: string;

  @Column({ type: 'varchar', length: 255, unique: true })
  username: string;

  @Column({ type: 'varchar', length: 255 })
  hashed_password: string;

  @Column({ type: 'varchar', length: 34, nullable: true })
  wallet_address: string | null;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  balance: number;

  @Column({ type: 'int', default: 0 })
  games_played: number;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  total_winnings: number;

  @Column({ type: 'int', default: 0 })
  leaderboard_rank: number;

  @Column({ type: 'boolean', default: false })
  is_admin: boolean;

  @Column({ type: 'varchar', length: 500, nullable: true })
  avatar_url: string | null;

  @OneToMany(() => Wallet, (wallet) => wallet.user)
  wallets: Wallet[];

  @OneToMany(() => WithdrawalRequest, (withdrawal) => withdrawal.user)
  withdrawals: WithdrawalRequest[];
}


