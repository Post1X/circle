import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Injectable, Logger } from '@nestjs/common';
import { RoomsService } from './rooms.service';
import { UsersService } from '../users/users.service';
import { PlayerCounterService } from '../../services/player-counter/player-counter.service';
import { WithdrawalService } from '../withdrawal/withdrawal.service';
import { CacheService } from '../../services/cache/cache.service';
import { SkillStatsService } from '../../services/skill-stats/skill-stats.service';
import { GameTrackerService } from '../../services/game-tracker/game-tracker.service';
import { GameStatsService } from '../../services/game-stats/game-stats.service';
import { User } from '../../entities/user.entity';

interface ActiveConnection {
  user_id: string | null;
  room_id: string | null;
  authenticated: boolean;
  username: string | null;
}

@WebSocketGateway({
  cors: {
    origin: '*',
  },
  namespace: '/',
})
@Injectable()
export class RoomsGateway
  implements OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  private readonly logger = new Logger(RoomsGateway.name);
  private activeConnections: Map<string, ActiveConnection> = new Map();
  private playersInRoom: Map<string, Array<{ user_id: string; username: string }>> = new Map();

  constructor(
    private roomsService: RoomsService,
    private usersService: UsersService,
    private playerCounterService: PlayerCounterService,
    private withdrawalService: WithdrawalService,
    private cacheService: CacheService,
    private skillStatsService: SkillStatsService,
    private gameTrackerService: GameTrackerService,
    private gameStatsService: GameStatsService,
  ) {}

  handleConnection(client: Socket) {
    this.logger.log(`Client connected: ${client.id}`);
    this.activeConnections.set(client.id, {
      user_id: null,
      room_id: null,
      authenticated: false,
      username: null,
    });
    client.emit('connected', { sid: client.id });
  }

  async handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);
    const connection = this.activeConnections.get(client.id);
    if (connection) {
      if (connection.user_id) {
        await this.playerCounterService.decrementRealCount(connection.user_id);
      }
      if (connection.room_id) {
        await this.leaveRoomSocket(client, connection.room_id);
      }
      this.activeConnections.delete(client.id);
    }
  }

  @SubscribeMessage('authenticate')
  async handleAuthenticate(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { user_id: string },
  ) {
    try {
      const user = await this.usersService.getUserById(data.user_id);
      if (!user) {
        client.emit('auth_error', { message: 'User not found' });
        return;
      }

      const connection = this.activeConnections.get(client.id);
      if (connection) {
        connection.user_id = user.user_id;
        connection.authenticated = true;
        connection.username = user.username;
      }

      await this.playerCounterService.incrementRealCount(user.user_id);

      client.emit('authenticated', {
        user_id: user.user_id,
        wallet_address: user.wallet_address,
        username: user.username,
      });
    } catch (error) {
      client.emit('auth_error', { message: error.message });
    }
  }

  @SubscribeMessage('create_room')
  async handleCreateRoom(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { entry_fee?: number; min_players?: number; max_players?: number },
  ) {
    try {
      const connection = this.activeConnections.get(client.id);
      if (!connection || !connection.authenticated) {
        client.emit('error', { message: 'Authentication required' });
        return;
      }

      const entryFee = data.entry_fee !== undefined && data.entry_fee !== null 
        ? Math.max(0, Number(data.entry_fee)) 
        : 0;
      
      const minPlayers = data.min_players || 2;
      const maxPlayers = data.max_players || 50;

      const room = await this.roomsService.createRoom(
        entryFee,
        minPlayers,
        maxPlayers,
      );

      client.emit('room_created', {
        room_id: room.room_id,
        entry_fee: room.entry_fee,
        min_players: room.min_players,
        max_players: room.max_players,
        status: room.status,
        created_at: room.created_at.toISOString(),
      });
    } catch (error) {
      client.emit('error', { message: error.message + 'createroom' });
    }
  }

  @SubscribeMessage('join_game')
  async handleJoinGame(
    @ConnectedSocket() client: Socket,
    @MessageBody()
    data: { entry_fee?: number; min_players?: number; max_players?: number },
  ) {
    try {
      const connection = this.activeConnections.get(client.id);
      if (!connection || !connection.authenticated) {
        client.emit('error', { message: 'Authentication required' });
        return;
      }

      const entryFee =
        data.entry_fee !== undefined && data.entry_fee !== null
          ? Math.max(0, Number(data.entry_fee))
          : 0;

      // Временно по умолчанию запускаем игру даже с 1 игроком
      const minPlayers = data.min_players ?? 1;
      const maxPlayers = data.max_players ?? 50;

      // Пытаемся найти свободную подходящую комнату
      let room =
        (await this.roomsService.findFreeRoom(
          entryFee,
          minPlayers,
          maxPlayers,
        )) ?? null;

      // Если нет — создаём новую
      if (!room) {
        room = await this.roomsService.createRoom(
          entryFee,
          minPlayers,
          maxPlayers,
        );
      }

      const roomId = room.room_id;

      // Обновляем playersInRoom локально, чтобы joinRoomSocket разослал корректный список
      if (!this.playersInRoom.has(roomId)) {
        this.playersInRoom.set(roomId, []);
      }
      const players = this.playersInRoom.get(roomId)!;
      const alreadyInRoom = players.some(
        (p) => p.user_id === connection.user_id,
      );
      if (!alreadyInRoom) {
        players.push({
          user_id: connection.user_id!,
          username: connection.username || connection.user_id!,
        });
      }

      await this.joinRoomSocket(client, roomId);
    } catch (error: any) {
      client.emit('error', { message: (error?.message || String(error)) + ' join_game' });
    }
  }

  @SubscribeMessage('join_room')
  async handleJoinRoom(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { room_id: string },
  ) {
    try {
      const connection = this.activeConnections.get(client.id);
      if (!connection || !connection.authenticated) {
        client.emit('error', { message: 'Authentication required' });
        return;
      }

      const roomId = data.room_id;
      if (!this.playersInRoom.has(roomId)) {
        this.playersInRoom.set(roomId, []);
      }

      const players = this.playersInRoom.get(roomId);
      const alreadyInRoom = players.some(
        (p) => p.user_id === connection.user_id,
      );

      if (!alreadyInRoom) {
        players.push({
          user_id: connection.user_id,
          username: connection.username || connection.user_id,
        });
      }

      await this.joinRoomSocket(client, roomId);
    } catch (error) {
      client.emit('error', { message: error.message + 'joinroom' });
    }
  }

  @SubscribeMessage('leave_room')
  async handleLeaveRoom(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { room_id: string },
  ) {
    try {
      await this.leaveRoomSocket(client, data.room_id);
    } catch (error) {
      client.emit('error', { message: error.message });
    }
  }

  @SubscribeMessage('get_rooms')
  async handleGetRooms(@ConnectedSocket() client: Socket) {
    try {
      const rooms = await this.roomsService.getAllRooms();
      const roomsData = rooms.map((room) => ({
        room_id: room.room_id,
        entry_fee: room.entry_fee,
        min_players: room.min_players,
        max_players: room.max_players,
        status: room.status,
        created_at: room.created_at.toISOString(),
      }));
      client.emit('rooms_list', { rooms: roomsData });
    } catch (error) {
      client.emit('error', { message: error.message + 'get_rooms' });
    }
  }

  @SubscribeMessage('move')
  async handleMove(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { dx: number; dy: number },
  ) {
    const connection = this.activeConnections.get(client.id);
    const roomId = connection?.room_id;
    const userId = connection?.user_id;

    if (!roomId || !userId) {
      return;
    }

    const { get_game, set_changes } = await import('../../game');
    const game = await get_game(roomId);
    if (game) {
      game.move_player(userId, data.dx, data.dy);
      await set_changes(roomId, game);
    }
  }

  @SubscribeMessage('activate_skill')
  async handleActivateSkill(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { skill_type: string },
  ) {
    const connection = this.activeConnections.get(client.id);
    const roomId = connection?.room_id;
    const userId = connection?.user_id;

    if (!roomId || !userId) {
      client.emit('skill_error', { message: 'Not in game' });
      return;
    }

    const skillType = data.skill_type;
    if (!['teleport', 'shield', 'boost'].includes(skillType)) {
      client.emit('skill_error', { message: 'Invalid skill type' });
      return;
    }

    const { get_game, set_changes } = await import('../../game');
    const game = await get_game(roomId);
    if (!game) {
      client.emit('skill_error', { message: 'Game not found' });
      return;
    }

    const player = game.players.get(userId);

    // Проверяем "последний шанс" для игроков с низким балансом в супер игре
    if (game.game_phase === 'super' && player && skillType === 'teleport') {
      const lastChanceSuccess = game.check_last_chance(userId);
      if (lastChanceSuccess) {
        this.server.to(roomId).emit('last_chance_activated', {
          player_id: userId,
          skill_type: skillType,
          skill_costs_increased: game.skill_costs_increased,
        });
        return;
      }
    }

    const balanceBefore = player?.money || 0;
    const [success, errorCode, cost] = game.activate_skill(
      userId,
      skillType,
      false,
    );

    if (success) {
      const playerAfter = game.players.get(userId);
      if (!playerAfter) {
        client.emit('skill_error', {
          error_code: 'player_not_in_game',
          message: 'Player not found',
          skill_type: skillType,
        });
        return;
      }

      const cooldowns = {
        teleport: Math.round(Math.max(0, playerAfter.teleport_cooldown) * 10) / 10,
        shield: Math.round(Math.max(0, playerAfter.shield_cooldown) * 10) / 10,
        boost: Math.round(Math.max(0, playerAfter.boost_cooldown) * 10) / 10,
      };

      await set_changes(roomId, game);

      await this.skillStatsService.recordSkillUsage(
        userId,
        roomId,
        skillType,
        cost,
        balanceBefore,
        playerAfter.money,
        false,
      );

      const skillActivatedData: any = {
        player_id: userId,
        skill_type: skillType,
        cost: cost,
        new_balance: playerAfter.money,
        skills_used: playerAfter.skills_used,
        cooldowns,
        free_teleport_used: playerAfter.free_teleport_used,
      };

      if (skillType === 'teleport') {
        skillActivatedData.new_position = {
          x: playerAfter.x,
          y: playerAfter.y,
        };
      } else if (skillType === 'shield') {
        skillActivatedData.shield_active = playerAfter.shield_active;
        skillActivatedData.shield_duration = 3;
      }

      client.emit('skill_activated', skillActivatedData);

      this.server.to(roomId).emit('player_used_skill', {
        player_id: userId,
        skill_type: skillType,
      });

      const gameState = game.get_state();
      this.server.to(roomId).emit('game_state', gameState);
    } else {
      client.emit('skill_error', {
        error_code: errorCode,
        message: this.getErrorMessage(errorCode),
        skill_type: skillType,
      });
    }
  }

  private getErrorMessage(errorCode: string): string {
    const messages: Record<string, string> = {
      minimum_balance_required: 'Minimum balance of $1 required to use skills',
      skill_limit_reached: 'Maximum skill uses (5) reached for this game',
      skill_on_cooldown: 'Skill is on cooldown',
      insufficient_balance: 'Insufficient balance to activate skill',
      player_not_in_game: 'Player not in game',
      game_not_active: 'Game is not active',
      invalid_skill_type: 'Invalid skill type',
      free_teleport_used: 'Free teleport already used',
    };
    return messages[errorCode] || 'Unknown error';
  }

  @SubscribeMessage('get_players')
  async handleGetPlayers(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { room_id: string },
  ) {
    const { get_game } = await import('../../game');
    const game = await get_game(data.room_id);
    if (game) {
      client.emit('all_players', Object.fromEntries(game.players));
    }
  }

  @SubscribeMessage('get_bonus_zones_info')
  async handleGetBonusZonesInfo(@ConnectedSocket() client: Socket) {
    try {
      const connection = this.activeConnections.get(client.id);
      const roomId = connection?.room_id;

      if (!roomId) {
        client.emit('error', { message: 'Not in game' });
        return;
      }

      const { get_game } = await import('../../game');
      const game = await get_game(roomId);

      if (!game) {
        client.emit('error', { message: 'Game not found' });
        return;
      }

      const bonusZonesInfo = {
        active_zones: game.bonus_zones.map((zone) => ({
          x: zone.x,
          y: zone.y,
          radius: zone.radius,
          multiplier: zone.multiplier,
          remaining_time: zone.get_remaining_time(),
          funds_collected: zone.funds_collected,
          max_funds: zone.funds_generated * zone.multiplier,
          is_active: zone.is_active,
        })),
        zone_fund: game.zone_fund,
        bonus_fund: game.bonus_fund,
        time_to_next_zone: game.get_time_to_next_bonus_zone(),
        zone_settings: {
          spawn_interval_seconds: game.bonus_zone_interval,
          zone_duration_seconds: 30.0,
          funds_per_zone: 20,
        },
      };

      client.emit('bonus_zones_info', bonusZonesInfo);
    } catch (error: any) {
      client.emit('error', {
        message: `Error getting bonus zones info: ${error?.message || String(error)}`,
      });
    }
  }

  @SubscribeMessage('get_game_phase')
  async handleGetGamePhase(@ConnectedSocket() client: Socket) {
    try {
      const connection = this.activeConnections.get(client.id);
      const roomId = connection?.room_id;
      const userId = connection?.user_id;

      if (!roomId || !userId) {
        client.emit('game_phase_error', { message: 'Not in game' });
        return;
      }

      const { get_game } = await import('../../game');
      const game = await get_game(roomId);

      if (!game) {
        client.emit('game_phase_error', { message: 'Game not found' });
        return;
      }

      const phaseInfo = game.get_game_phase_info();
      client.emit('game_phase_info', phaseInfo);
    } catch (error: any) {
      client.emit('game_phase_error', { message: error?.message || String(error) });
    }
  }

  @SubscribeMessage('submit_vote')
  async handleSubmitVote(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { vote: string },
  ) {
    try {
      const connection = this.activeConnections.get(client.id);
      const roomId = connection?.room_id;
      const userId = connection?.user_id;

      if (!roomId || !userId) {
        client.emit('vote_error', { message: 'Not in game' });
        return;
      }

      const { get_game, set_changes } = await import('../../game');
      const game = await get_game(roomId);

      if (!game) {
        client.emit('vote_error', { message: 'Game not found' });
        return;
      }

      const vote = data.vote;
      if (vote !== 'exit' && vote !== 'super') {
        client.emit('vote_error', { message: 'Invalid vote' });
        return;
      }

      const success = game.submit_vote(userId, vote);

      if (success) {
        client.emit('vote_submitted', {
          vote: vote,
          voting_time_remaining: game.get_voting_time_remaining(),
        });

        let votesExit = 0;
        let votesSuper = 0;
        for (const v of game.votes.values()) {
          if (v === 'exit') votesExit++;
          if (v === 'super') votesSuper++;
        }

        this.server.to(roomId).emit('vote_update', {
          votes_submitted: game.votes.size,
          votes_exit: votesExit,
          votes_super: votesSuper,
        });

        await set_changes(roomId, game);
      } else {
        client.emit('vote_error', { message: 'Cannot submit vote' });
      }
    } catch (error: any) {
      client.emit('vote_error', { message: error?.message || String(error) });
    }
  }

  @SubscribeMessage('request_last_chance')
  async handleRequestLastChance(@ConnectedSocket() client: Socket) {
    try {
      const connection = this.activeConnections.get(client.id);
      const roomId = connection?.room_id;
      const userId = connection?.user_id;

      if (!roomId || !userId) {
        client.emit('last_chance_error', { message: 'Not in game' });
        return;
      }

      const { get_game } = await import('../../game');
      const game = await get_game(roomId);

      if (!game) {
        client.emit('last_chance_error', { message: 'Game not found' });
        return;
      }

      const success = game.check_last_chance(userId);

      if (success) {
        this.server.to(roomId).emit('last_chance_activated', {
          player_id: userId,
          skill_costs_increased: game.skill_costs_increased,
        });
      } else {
        client.emit('last_chance_error', {
          message: 'Cannot activate last chance',
        });
      }
    } catch (error: any) {
      client.emit('last_chance_error', { message: error?.message || String(error) });
    }
  }

  @SubscribeMessage('get_game_results')
  async handleGetGameResults(@ConnectedSocket() client: Socket) {
    try {
      const connection = this.activeConnections.get(client.id);
      const roomId = connection?.room_id;

      if (!roomId) {
        client.emit('results_error', { message: 'Not in game' });
        return;
      }

      const { get_game } = await import('../../game');
      const game = await get_game(roomId);

      if (!game) {
        client.emit('results_error', { message: 'Game not found' });
        return;
      }

      const results: any = {
        early_exits: Object.fromEntries(game.early_exits),
        super_exits: Object.fromEntries(game.super_exits),
        finalists: game.finalists,
        bonus_fund: game.bonus_fund,
        zone_fund: game.zone_fund,
        final_winnings: {},
      };

      for (const playerId of game.finalists) {
        if (game.players.has(playerId)) {
          results.final_winnings[playerId] =
            game.players.get(playerId)?.final_winnings || 0;
        }
      }

      client.emit('game_results', results);
    } catch (error: any) {
      client.emit('results_error', { message: error?.message || String(error) });
    }
  }

  private async buildLeaderboardData(roomId: string, game: any): Promise<any | null> {
    try {
      const playersList: any[] = [];
      for (const [playerId, player] of game.players.entries()) {
        // В Python: сначала player_id, потом ищется в players_in_room
        let playerUsername = playerId;
        const playersInRoom = this.playersInRoom.get(roomId);
        if (playersInRoom) {
          const playerInfo = playersInRoom.find((p) => p.user_id === playerId);
          if (playerInfo) {
            playerUsername = playerInfo.username;
          } else if (player.username) {
            // Если не нашли в playersInRoom, используем username из игрока
            playerUsername = player.username;
          }
        } else if (player.username) {
          playerUsername = player.username;
        }

        const colorTuple =
          Array.isArray(player.color) && player.color.length === 3
            ? (player.color as [number, number, number])
            : ([0, 255, 0] as [number, number, number]);

        playersList.push({
          player_id: playerId,
          mass: player.get_radius(),
          x: player.x,
          y: player.y,
          r: colorTuple[0],
          g: colorTuple[1],
          b: colorTuple[2],
          skills_used: player.skills_used,
          bonus_zone_collected: player.bonus_zone_collected,
          outside_zone_damage: player.outside_zone_damage,
          in_bonus_zone: player.in_bonus_zone,
          bonus_multiplier: player.current_bonus_multiplier,
          rank: 0,
          username: playerUsername,
        });
      }

      playersList.sort((a, b) => b.mass - a.mass);
      playersList.forEach((p, i) => {
        p.rank = i + 1;
      });

      const phase = game.get_game_phase_info();

      const gamePhaseInfo: any = {
        phase: phase.phase,
        players_count: game.players.size,
        bonus_fund: game.bonus_fund,
        zone_fund: game.zone_fund,
      };

      if (phase.voting_time_remaining !== undefined) {
        gamePhaseInfo.voting_time_remaining = phase.voting_time_remaining;
      }
      if (phase.votes_submitted !== undefined) {
        gamePhaseInfo.votes_submitted = phase.votes_submitted;
      }
      if (phase.votes_exit !== undefined) {
        gamePhaseInfo.votes_exit = phase.votes_exit;
      }
      if (phase.votes_super !== undefined) {
        gamePhaseInfo.votes_super = phase.votes_super;
      }
      if (phase.super_game_time_remaining !== undefined) {
        gamePhaseInfo.super_game_time_remaining = phase.super_game_time_remaining;
      }
      if (phase.skill_costs_increased !== undefined) {
        gamePhaseInfo.skill_costs_increased = phase.skill_costs_increased;
      }

      const leaderboardData: any = {
        current_players: playersList,
        total_players: playersList.length,
        game_phase: gamePhaseInfo,
        game_time: game.get_game_time(),
        safe_zone_scale: game.safe_zone_scale,
        zone_fund: game.zone_fund,
        bonus_fund: game.bonus_fund,
      };

      if (game.early_exits.size > 0) {
        const earlyExitsList = Array.from(game.early_exits.entries())
          .map(([pid, amount]) => ({
            player_id: pid,
            winnings: amount,
            exit_type: 'early',
            percentage: 50,
          }))
          .sort((a, b) => b.winnings - a.winnings);
        leaderboardData.early_exits = earlyExitsList;
      }

      if (game.super_exits.size > 0) {
        const superExitsList = Array.from(game.super_exits.entries())
          .map(([pid, amount]) => ({
            player_id: pid,
            winnings: amount,
            exit_type: 'super',
            percentage: 25,
          }))
          .sort((a, b) => b.winnings - a.winnings);
        leaderboardData.super_exits = superExitsList;
      }

      if (game.finalists.length > 0) {
        const finalistsList = game.finalists
          .filter((pid) => game.players.has(pid))
          .map((pid) => ({
            player_id: pid,
            final_winnings: game.players.get(pid)?.final_winnings || 0,
            final_mass: game.players.get(pid)?.get_radius() || 0,
          }))
          .sort((a, b) => b.final_winnings - a.final_winnings);
        leaderboardData.finalists = finalistsList;
      }

      return leaderboardData;
    } catch (error) {
      this.logger.error(`Error building leaderboard for room ${roomId}: ${error?.message || error}`);
      return null;
    }
  }

  @SubscribeMessage('get_leaderboard')
  async handleGetLeaderboard(@ConnectedSocket() client: Socket) {
    try {
      const connection = this.activeConnections.get(client.id);
      const roomId = connection?.room_id;

      if (!roomId) {
        client.emit('leaderboard_error', { message: 'Not in game' });
        return;
      }

      const { get_game } = await import('../../game');
      const game = await get_game(roomId);

      if (!game) {
        client.emit('leaderboard_error', { message: 'Game not found' });
        return;
      }

      const leaderboardData = await this.buildLeaderboardData(roomId, game);
      if (leaderboardData) {
        client.emit('leaderboard', leaderboardData);
      } else {
        client.emit('leaderboard_error', { message: 'Failed to build leaderboard' });
      }
    } catch (error: any) {
      client.emit('leaderboard_error', { message: error?.message || String(error) });
    }
  }

  @SubscribeMessage('exit_game')
  async handleExitGame(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { exit_type: string },
  ) {
    const connection = this.activeConnections.get(client.id);
    const roomId = connection?.room_id;
    const userId = connection?.user_id;

    if (!roomId || !userId) {
      client.emit('exit_error', { message: 'Not in game' });
      return;
    }

    try {
      const { get_game, set_changes } = await import('../../game');
      const game = await get_game(roomId);
      if (!game) {
        client.emit('exit_error', { message: 'Game not found' });
        return;
      }

      const exitType = data.exit_type;

      const player = game.players.get(userId);
      if (!player) {
        client.emit('exit_error', { message: 'Player not found' });
        return;
      }

      if (exitType === 'early' && game.game_phase === 'start') {
        const originalBalance = player.money;
        game.process_early_exit(userId);
        const finalBalance = game.early_exits.get(userId) || 0;
        const penalty = originalBalance - finalBalance;

        await this.withdrawalService.creditUserBalance(userId, finalBalance);

        await this.gameStatsService.savePlayerGameStats(
          userId,
          roomId,
          player,
          'early',
          game.game_start_time,
          null,
        );

        client.emit('finished', {
          player_id: userId,
          exit_type: 'early',
          original_balance: originalBalance,
          final_balance: finalBalance,
          penalty: penalty,
          message: 'You left the game early. You saved 50% of your balance.',
        });

        this.server.to(roomId).emit('player_exited', {
          player_id: userId,
          exit_type: 'early',
          winnings: finalBalance,
        });
      } else if (exitType === 'super' && game.game_phase === 'super') {
        const originalBalance = player.money;
        game.process_super_exit(userId);
        const finalBalance = game.super_exits.get(userId) || 0;
        const penalty = originalBalance - finalBalance;

        await this.withdrawalService.creditUserBalance(userId, finalBalance);

        await this.gameStatsService.savePlayerGameStats(
          userId,
          roomId,
          player,
          'super',
          game.game_start_time,
          null,
        );

        client.emit('finished', {
          player_id: userId,
          exit_type: 'super',
          original_balance: originalBalance,
          final_balance: finalBalance,
          penalty: penalty,
          message: 'You left the super game. You saved 25% of your balance.',
        });

        this.server.to(roomId).emit('player_exited', {
          player_id: userId,
          exit_type: 'super',
          winnings: finalBalance,
        });
      } else {
        client.emit('exit_error', {
          message: 'Invalid exit type or phase',
        });
        return;
      }

      await this.gameTrackerService.removePlayerFromRoom(userId, roomId);
      await set_changes(roomId, game);
      await this.leaveRoomSocket(client, roomId);
    } catch (error) {
      client.emit('exit_error', { message: error.message });
    }
  }

  private async joinRoomSocket(client: Socket, roomId: string) {
    try {
      const room = await this.roomsService.getRoomById(roomId);
      if (!room) {
        client.emit('error', { message: 'Room not found' });
        return;
      }

      if (room.status !== 'waiting') {
        client.emit('error', { message: 'Room is not accepting players' });
        return;
      }

      const connection = this.activeConnections.get(client.id);
      if (!connection) return;

      if (room.entry_fee && room.entry_fee > 0) {
        const user = await this.usersService.getUserById(connection.user_id);
        const userBalance = parseFloat(user.balance.toString());
        if (userBalance < room.entry_fee) {
          client.emit('error', {
            message: 'Insufficient balance for entry fee',
          });
          return;
        }

        await this.withdrawalService.debitUserBalance(
          connection.user_id!,
          room.entry_fee,
        );
      }

      await client.join(roomId);
      await this.roomsService.addPlayer(roomId);
      connection.room_id = roomId;

      const players = this.playersInRoom.get(roomId) || [];
      this.server.to(roomId).emit('player_joined', {
        players,
        room_id: roomId,
      });

      const needStartGame = await this.roomsService.checkStartGame(roomId);
      client.emit('joined_room', {
        players,
        room_id: roomId,
        message: 'Successfully joined room',
        time_to_start: needStartGame ? 30 : null,
      });

      if (needStartGame) {
        this.server.to(roomId).emit('game_started', { time_to_start: 30 });
        setTimeout(() => {
          this.startGameLoop(roomId).catch((err) => {
            this.logger.error(
              `Failed to start game loop for room ${roomId}: ${err?.message || err}`,
            );
          });
        }, 30000);
      }
    } catch (error) {
      client.emit('error', { message: error.message + 'join from socket' });
    }
  }

  private async leaveRoomSocket(client: Socket, roomId: string) {
    try {
      await client.leave(roomId);
      const connection = this.activeConnections.get(client.id);
      if (connection && connection.user_id) {
        await this.gameTrackerService.removePlayerFromRoom(
          connection.user_id,
          roomId,
        );
        connection.room_id = null;

        const players = this.playersInRoom.get(roomId);
        if (players) {
          const index = players.findIndex(
            (p) => p.user_id === connection.user_id,
          );
          if (index > -1) {
            players.splice(index, 1);
          }
        }
      }

      this.server.to(roomId).emit('player_left', {
        user_id: connection?.user_id,
        room_id: roomId,
      });

      client.emit('left_room', {
        room_id: roomId,
        message: 'Successfully left room',
      });
    } catch (error) {
      client.emit('error', { message: error.message });
    }
  }

  private async startGameLoop(roomId: string) {
    const { create_game, get_game, set_changes, close_game } = await import('../../game');
    const game = await create_game(roomId, 50, 1000);

    const players = Array.from(this.activeConnections.entries())
      .filter(([_, conn]) => conn.room_id === roomId)
      .map(([_, conn]) => ({
        user_id: conn.user_id!,
        username: conn.username || conn.user_id!,
      }));

    for (const player of players) {
      game.add_player(player.user_id, player.username);
      await this.gameTrackerService.setPlayerInRoom(player.user_id, roomId);
    }

    let lastPhase = game.game_phase;
    let lastLeaderboardTime = Date.now();
    let lastPlayersPositionsTime = Date.now();

    const loop = setInterval(async () => {
      const currentGame = await get_game(roomId);
      if (!currentGame) {
        clearInterval(loop);
        return;
      }

      const roomPlayers = Array.from(this.activeConnections.entries())
        .filter(([_, conn]) => conn.room_id === roomId)
        .map(([_, conn]) => conn.user_id!);

      if (roomPlayers.length === 0) {
        clearInterval(loop);
        await close_game(roomId);
        return;
      }

      const playersBeforeUpdate = new Map(currentGame.players);
      currentGame.update();

      const playersRemoved: string[] = [];
      for (const [playerId, player] of playersBeforeUpdate.entries()) {
        if (!currentGame.players.has(playerId)) {
          playersRemoved.push(playerId);
        }
      }

      for (const playerId of playersRemoved) {
        const removedPlayer = playersBeforeUpdate.get(playerId);
        if (removedPlayer) {
          try {
            await this.gameStatsService.savePlayerGameStats(
              playerId,
              roomId,
              removedPlayer,
              'death',
              currentGame.game_start_time,
              null,
            );
            await this.gameTrackerService.removePlayerFromRoom(playerId, roomId);
          } catch (error) {
            this.logger.error(`Failed to save stats for player ${playerId}: ${error.message}`);
          }
        }
      }

      if (currentGame.game_phase !== lastPhase) {
        if (currentGame.game_phase === 'top10') {
          this.server.to(roomId).emit('phase_changed', {
            new_phase: 'top10',
            voting_time_remaining: currentGame.get_voting_time_remaining(),
            message: 'Голосование в топ-10 началось!',
          });
        } else if (currentGame.game_phase === 'super') {
          this.server.to(roomId).emit('phase_changed', {
            new_phase: 'super',
            super_game_time_remaining: currentGame.get_super_game_time_remaining(),
            message: 'Супер игра началась!',
          });
        } else if (currentGame.game_phase === 'finished') {
          this.server.to(roomId).emit('phase_changed', {
            new_phase: 'finished',
            message: 'Игра завершена!',
          });
          clearInterval(loop);
          
          currentGame.finalize_game();
          const finalists = currentGame.finalists;
          for (let i = 0; i < finalists.length; i++) {
            const playerId = finalists[i];
            const player = currentGame.players.get(playerId);
            if (player) {
              try {
                await this.gameStatsService.savePlayerGameStats(
                  playerId,
                  roomId,
                  player,
                  'final',
                  currentGame.game_start_time,
                  i + 1,
                );
                await this.gameTrackerService.removePlayerFromRoom(playerId, roomId);
              } catch (error) {
                this.logger.error(`Failed to save stats for finalist ${playerId}: ${error.message}`);
              }
            }
          }

          const results = {
            early_exits: Object.fromEntries(currentGame.early_exits),
            super_exits: Object.fromEntries(currentGame.super_exits),
            finalists: finalists,
            bonus_fund: currentGame.bonus_fund,
            zone_fund: currentGame.zone_fund,
            final_winnings: Object.fromEntries(
              finalists.map((pid) => [
                pid,
                currentGame.players.get(pid)?.final_winnings || 0,
              ]),
            ),
          };

          this.server.to(roomId).emit('game_finished', results);
          await close_game(roomId);
          return;
        }
        lastPhase = currentGame.game_phase;
      }

      if (currentGame.should_shrink_zone()) {
        currentGame.shrink_safe_zone();
        this.server.to(roomId).emit('zone_shrunk', {
          new_scale: currentGame.safe_zone_scale,
          damage_per_second: currentGame.zone_damage_per_second,
          time_to_next_shrink: currentGame.get_time_to_next_shrink(),
        });
      }

      if (currentGame.should_spawn_bonus_zone()) {
        if (currentGame.spawn_bonus_zone()) {
          const latestZone = currentGame.bonus_zones[currentGame.bonus_zones.length - 1];
          this.server.to(roomId).emit('bonus_zone_spawned', {
            x: latestZone.x,
            y: latestZone.y,
            radius: latestZone.radius,
            multiplier: latestZone.multiplier,
            duration: latestZone.duration,
            zone_fund: currentGame.zone_fund,
          });
        }
      }

      const expiredZones = currentGame.bonus_zones.filter((z) => z.is_expired());
      for (const zone of expiredZones) {
        this.server.to(roomId).emit('bonus_zone_expired', {
          x: zone.x,
          y: zone.y,
          multiplier: zone.multiplier,
          funds_collected: zone.funds_collected,
        });
      }

      if (currentGame.game_phase === 'top10') {
        const votingTime = currentGame.get_voting_time_remaining();
        if (votingTime <= 10 && votingTime > 0) {
          let votesExit = 0;
          let votesSuper = 0;
          for (const vote of currentGame.votes.values()) {
            if (vote === 'exit') votesExit++;
            if (vote === 'super') votesSuper++;
          }
          this.server.to(roomId).emit('voting_warning', {
            time_remaining: votingTime,
            votes_submitted: currentGame.votes.size,
            votes_exit: votesExit,
            votes_super: votesSuper,
          });
        }
      }

      if (currentGame.game_phase === 'super') {
        const superTime = currentGame.get_super_game_time_remaining();
        if (superTime <= 60 && superTime > 0) {
          this.server.to(roomId).emit('super_game_warning', {
            time_remaining: superTime,
            players_remaining: currentGame.players.size,
          });
        }
      }

      const gameState = currentGame.get_state();
      this.server.to(roomId).emit('game_state', gameState);

      const now = Date.now();
      if (now - lastLeaderboardTime >= 10000) {
        const leaderboardData = await this.buildLeaderboardData(roomId, currentGame);
        if (leaderboardData) {
          this.server.to(roomId).emit('leaderboard', leaderboardData);
        }
        lastLeaderboardTime = now;
      }

      if (now - lastPlayersPositionsTime >= 3000) {
        const playersPositions = Array.from(currentGame.players.entries()).map(
          ([playerId, player]) => ({
            player_id: playerId,
            x: player.x,
            y: player.y,
            mass: player.get_radius(),
          }),
        );
        this.server.to(roomId).emit('players_positions', {
          players: playersPositions,
          timestamp: now,
        });
        lastPlayersPositionsTime = now;
      }

      await set_changes(roomId, currentGame);
    }, 50);
  }
}
