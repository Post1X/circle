import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { GameRoom } from '../../entities/game-room.entity';

@Injectable()
export class RoomsService {
  constructor(
    @InjectRepository(GameRoom)
    private gameRoomRepository: Repository<GameRoom>,
  ) {}

  async createRoom(
    entryFee: number,
    minPlayers: number,
    maxPlayers: number,
  ): Promise<GameRoom> {
    const room = this.gameRoomRepository.create({
      entry_fee: entryFee,
      min_players: minPlayers,
      max_players: maxPlayers,
      status: 'waiting',
      players: 0,
    });

    return await this.gameRoomRepository.save(room);
  }

  async getRoomById(roomId: string): Promise<GameRoom | null> {
    return await this.gameRoomRepository.findOne({
      where: { room_id: roomId },
    });
  }

  async getAllRooms(): Promise<GameRoom[]> {
    return await this.gameRoomRepository.find();
  }

  async addPlayer(roomId: string): Promise<void> {
    const room = await this.getRoomById(roomId);
    if (room) {
      room.players += 1;
      await this.gameRoomRepository.save(room);
    }
  }

  async checkStartGame(roomId: string): Promise<boolean> {
    const room = await this.getRoomById(roomId);
    return room ? room.min_players <= room.players : false;
  }
}


