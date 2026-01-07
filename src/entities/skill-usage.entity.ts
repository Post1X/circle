import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  Index,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { User } from './user.entity';
import { GameSession } from './game-session.entity';

@Entity('skill_usage')
export class SkillUsage {
  @PrimaryGeneratedColumn('uuid')
  @Index()
  id: string;

  @Column({ type: 'uuid' })
  @Index()
  user_id: string;

  @ManyToOne(() => User)
  @JoinColumn({ name: 'user_id' })
  user: User;

  @Column({ type: 'uuid' })
  @Index()
  session_id: string;

  @ManyToOne(() => GameSession)
  @JoinColumn({ name: 'session_id' })
  session: GameSession;

  @Column({ type: 'varchar', length: 20 })
  skill_type: string;

  @Column({ type: 'decimal', precision: 18, scale: 6 })
  cost: number;

  @Column({ type: 'decimal', precision: 18, scale: 6 })
  balance_before: number;

  @Column({ type: 'decimal', precision: 18, scale: 6 })
  balance_after: number;

  @Column({ type: 'boolean', default: false })
  is_free: boolean;

  @CreateDateColumn()
  created_at: Date;
}

