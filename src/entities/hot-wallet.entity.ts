import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

@Entity('hot_wallet')
export class HotWallet {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'varchar', length: 42, unique: true })
  address: string;

  @Column({ type: 'varchar', length: 255 })
  encrypted_private_key: string;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  balance: number;

  @Column({ type: 'boolean', default: true })
  is_active: boolean;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  last_updated: Date;
}


