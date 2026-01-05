import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  Index,
} from 'typeorm';

@Entity('game_room')
export class GameRoom {
  @PrimaryGeneratedColumn('uuid')
  @Index()
  room_id: string;

  @Column({ type: 'int' })
  entry_fee: number;

  @Column({ type: 'int', default: 0 })
  players: number;

  @Column({ type: 'int', default: 20 })
  min_players: number;

  @Column({ type: 'int', default: 100 })
  max_players: number;

  @Column({ type: 'varchar', default: 'waiting' })
  status: string;

  @CreateDateColumn()
  created_at: Date;
}


