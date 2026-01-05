import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

@Entity('cold_wallet')
export class ColdWallet {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'varchar', length: 42, unique: true })
  address: string;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  balance: number;

  @Column({ type: 'boolean', default: true })
  is_active: boolean;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  last_updated: Date;
}


