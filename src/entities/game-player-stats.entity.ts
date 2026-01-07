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

@Entity('game_player_stats')
export class GamePlayerStats {
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

  @Column({ type: 'int', default: 0 })
  skills_used_total: number;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  skills_cost_total: number;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  final_winnings: number;

  @Column({ type: 'int', nullable: true })
  final_rank: number | null;

  @Column({ type: 'int', default: 0 })
  game_duration_seconds: number;

  @Column({ type: 'varchar', length: 20 })
  exit_type: string;

  @Column({ type: 'int', default: 0 })
  teleport_uses: number;

  @Column({ type: 'int', default: 0 })
  shield_uses: number;

  @Column({ type: 'int', default: 0 })
  boost_uses: number;

  @Column({ type: 'boolean', default: false })
  free_teleport_used: boolean;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  bonus_zone_collected: number;

  @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
  outside_zone_damage: number;

  @CreateDateColumn()
  created_at: Date;
}

