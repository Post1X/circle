import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
} from 'typeorm';
import { Wallet } from './wallet.entity';

export enum TransactionStatus {
  CREATED = 'created',
  BROADCASTED = 'broadcasted',
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  FAILED = 'failed',
  DROPPED = 'dropped',
}

export enum TransactionType {
  OUTGOING = 'outgoing',
  INCOMING = 'incoming',
}

@Entity('transaction')
export class Transaction {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'decimal', precision: 18, scale: 6 })
  amount: number;

  @Column({
    type: 'enum',
    enum: TransactionStatus,
    default: TransactionStatus.CREATED,
  })
  status: TransactionStatus;

  @Column({ type: 'enum', enum: TransactionType })
  type: TransactionType;

  @Column({ type: 'varchar', length: 42 })
  user_wallet_address: string;

  @ManyToOne(() => Wallet)
  @JoinColumn({ name: 'user_wallet_address', referencedColumnName: 'address' })
  wallet: Wallet;

  @CreateDateColumn()
  created_at: Date;
}


