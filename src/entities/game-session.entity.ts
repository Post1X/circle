import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';
import { GameRoom } from './game-room.entity';

@Entity('game_session')
export class GameSession {
  @PrimaryGeneratedColumn('uuid')
  @Index()
  session_id: string;

  @Column({ type: 'uuid' })
  room_id: string;

  @ManyToOne(() => GameRoom)
  @JoinColumn({ name: 'room_id' })
  room: GameRoom;

  @Column({ type: 'decimal', precision: 18, scale: 6 })
  total_bank: number;

  @Column({ type: 'int', default: 0 })
  zone_fund: number;

  @Column({ type: 'int', default: 0 })
  bonus_fund: number;

  @Column({ type: 'varchar', length: 20, default: 'start' })
  current_phase: string;

  @Column({ type: 'timestamp' })
  next_shrink_at: Date;
}


