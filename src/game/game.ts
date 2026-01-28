import { GamePhases, Phase, GameState, BonusZoneModel, SaveZone, Zone } from './models';
import { Player } from './player';
import { BonusZone } from './bonus-zone';
import { Food, gen_food } from './food';

const BASE_RADIUS = 400;

function calculate_map_size(player_count: number): number {
  let scale_factor: number;
  if (player_count <= 5) {
    scale_factor = 1;
  } else if (player_count <= 20) {
    scale_factor = 1 + (player_count - 5) * 0.027;
  } else if (player_count <= 50) {
    scale_factor = 1.5 + (player_count - 20) * 0.017;
  } else if (player_count <= 100) {
    scale_factor = 2.0 + (player_count - 50) * 0.01;
  } else {
    scale_factor = Math.min(3.0, 2.5 + (player_count - 100) * 0.005);
  }
  return Math.floor(BASE_RADIUS * scale_factor);
}

export class Game {
  players: Map<string, Player> = new Map();
  fund: number;
  radius: number;
  expected_players: number;
  original_radius: number;
  safe_zone_radius: number;
  safe_zone_scale: number = 1.0;

  zone_shrink_interval: number = 120.0;
  zone_shrink_rate: number = 0.9;
  min_zone_scale: number = 0.1;

  game_start_time: number;
  last_zone_shrink_time: number;
  next_zone_shrink_time: number;

  zone_damage_per_second: number = 2.0;

  foods: Food[];
  food_mass: number;

  bonus_zones: BonusZone[] = [];
  bonus_zone_interval: number = 180.0;
  last_bonus_zone_time: number;
  next_bonus_zone_time: number;
  zone_fund: number = 200;
  bonus_fund: number = 0;

  game_phase: GamePhases = GamePhases.START;
  players_remaining: number = 0;

  voting_start_time: number | null = null;
  voting_duration: number = 30.0;
  votes: Map<string, string> = new Map();
  voting_completed: boolean = false;

  super_game_start_time: number = 0;
  super_game_duration: number = 300.0;
  super_game_zone_shrink_rate: number = 0.96;
  super_game_min_zone_scale: number = 0.2;

  early_exits: Map<string, number> = new Map();
  super_exits: Map<string, number> = new Map();
  finalists: string[] = [];

  skill_costs_increased: boolean = false;
  last_chance_used: Map<string, boolean> = new Map();

  constructor(expected_players: number, fund: number) {
    this.fund = fund;
    this.radius = calculate_map_size(expected_players);
    this.expected_players = expected_players;
    this.original_radius = this.radius;
    this.safe_zone_radius = this.radius;

    this.game_start_time = Date.now() / 1000;
    this.last_zone_shrink_time = this.game_start_time;
    this.next_zone_shrink_time = this.game_start_time + this.zone_shrink_interval;

    this.last_bonus_zone_time = this.game_start_time;
    this.next_bonus_zone_time = this.game_start_time + this.bonus_zone_interval;

    const [foods, food_mass] = gen_food(this.fund, this.radius);
    this.foods = foods;
    this.food_mass = food_mass;
  }

  get_game_time(): number {
    return Date.now() / 1000 - this.game_start_time;
  }

  get_bonus_zones(): BonusZoneModel[] {
    return this.bonus_zones.map((z) => ({
      x: z.x,
      y: z.y,
      radius: z.radius,
      multiplier: z.multiplier,
      remaining_time: z.get_remaining_time(),
      funds_collected: z.funds_collected,
      max_funds: z.funds_generated * z.multiplier,
    }));
  }

  get_time_to_next_shrink(): number {
    return Math.max(0, this.next_zone_shrink_time - Date.now() / 1000);
  }

  get_time_to_next_bonus_zone(): number {
    return Math.max(0, this.next_bonus_zone_time - Date.now() / 1000);
  }

  check_phase_transition(): GamePhases {
    if (this.game_phase === GamePhases.START && this.players.size <= 10) {
      return GamePhases.TOP_10;
    } else if (
      this.game_phase === GamePhases.TOP_10 &&
      this.voting_completed
    ) {
      return GamePhases.SUPER;
    } else if (this.players.size <= 1) {
      return GamePhases.FINISHED;
    }
    return this.game_phase;
  }

  start_top10_voting(): void {
    this.game_phase = GamePhases.TOP_10;
    this.voting_start_time = Date.now() / 1000;
    this.votes.clear();
    this.voting_completed = false;

    this.zone_shrink_interval = Infinity;
    this.bonus_zone_interval = Infinity;
  }

  submit_vote(player_id: string, vote: string): boolean {
    if (this.game_phase !== GamePhases.TOP_10 || this.voting_completed) {
      return false;
    }

    if (vote !== 'exit' && vote !== GamePhases.SUPER) {
      return false;
    }

    if (!this.players.has(player_id)) {
      return false;
    }

    this.votes.set(player_id, vote);
    return true;
  }

  get_voting_time_remaining(): number {
    if (!this.voting_start_time) {
      return 0;
    }
    return Math.max(
      0,
      this.voting_duration - (Date.now() / 1000 - this.voting_start_time),
    );
  }

  should_end_voting(): boolean {
    if (!this.voting_start_time) {
      return false;
    }
    return Date.now() / 1000 - this.voting_start_time >= this.voting_duration;
  }

  process_voting_results(): void {
    if (!this.should_end_voting()) {
      return;
    }

    this.voting_completed = true;

    for (const [player_id, vote] of this.votes.entries()) {
      if (vote === 'exit' && this.players.has(player_id)) {
        this.process_early_exit(player_id);
      }
    }

    this.start_super_game();
  }

  process_early_exit(player_id: string): void {
    if (!this.players.has(player_id)) {
      return;
    }

    const player = this.players.get(player_id)!;
    const collected_amount = player.money;

    const player_winnings = collected_amount * 0.5;
    const bonus_contribution = collected_amount * 0.5;

    this.early_exits.set(player_id, player_winnings);
    this.bonus_fund += bonus_contribution;

    this.players.delete(player_id);
  }

  start_super_game(): void {
    this.game_phase = GamePhases.SUPER;
    this.super_game_start_time = Date.now() / 1000;

    this.zone_shrink_interval = 60.0;
    this.zone_shrink_rate = this.super_game_zone_shrink_rate;
    this.min_zone_scale = this.super_game_min_zone_scale;

    this.bonus_zone_interval = 180.0;
  }

  get_super_game_time_remaining(): number {
    if (!this.super_game_start_time) {
      return 0;
    }
    return Math.max(
      0,
      this.super_game_duration -
        (Date.now() / 1000 - this.super_game_start_time),
    );
  }

  should_end_super_game(): boolean {
    if (!this.super_game_start_time) {
      return false;
    }
    return (
      Date.now() / 1000 - this.super_game_start_time >= this.super_game_duration
    );
  }

  process_super_exit(player_id: string): void {
    if (!this.players.has(player_id)) {
      return;
    }

    const player = this.players.get(player_id)!;
    const collected_amount = player.money;

    const player_winnings = collected_amount * 0.25;
    const bonus_contribution = collected_amount * 0.75;

    this.super_exits.set(player_id, player_winnings);
    this.bonus_fund += bonus_contribution;

    this.players.delete(player_id);
  }

  check_last_chance(player_id: string): boolean {
    if (this.game_phase !== GamePhases.SUPER) {
      return false;
    }

    const player = this.players.get(player_id);
    if (!player || player.free_teleport_used) {
      return false;
    }

    const super_game_time = Date.now() / 1000 - this.super_game_start_time;
    const time_remaining = this.super_game_duration - super_game_time;
    if (time_remaining > 180 || time_remaining < 120) {
      return false;
    }

    if (player.money >= 5) {
      return false;
    }

    return true;
  }

  get_skill_cost_percentage(player_id: string, skill_type: string): number {
    const player = this.players.get(player_id);
    if (!player) {
      return 0;
    }
    return player.get_skill_cost_percentage(skill_type) * 100;
  }

  finalize_game(): void {
    const remaining_food_value = this.foods.length * this.food_mass;
    this.bonus_fund += remaining_food_value;

    this.bonus_fund += this.zone_fund;

    this.finalists = Array.from(this.players.keys());

    if (this.finalists.length > 0) {
      let total_finalist_money = 0;
      for (const pid of this.finalists) {
        total_finalist_money += this.players.get(pid)!.money;
      }

      for (const player_id of this.finalists) {
        const player = this.players.get(player_id)!;
        const player_share =
          total_finalist_money !== 0 ? player.money / total_finalist_money : 0;
        player.final_winnings = this.bonus_fund * player_share;
      }
    }
  }

  get_game_phase_info(): Phase {
    if (this.game_phase === GamePhases.TOP_10) {
      let votes_exit = 0;
      let votes_super = 0;
      for (const vote of this.votes.values()) {
        if (vote === 'exit') votes_exit++;
        if (vote === GamePhases.SUPER) votes_super++;
      }

      return {
        phase: this.game_phase,
        voting_time_remaining: this.get_voting_time_remaining(),
        votes_submitted: this.votes.size,
        votes_exit,
        votes_super,
      };
    } else if (this.game_phase === GamePhases.SUPER) {
      return {
        phase: this.game_phase,
        super_game_time_remaining: this.get_super_game_time_remaining(),
        skill_costs_increased: this.skill_costs_increased,
      };
    } else if (this.game_phase === GamePhases.FINISHED) {
      return {
        phase: this.game_phase,
      };
    }
    return { phase: this.game_phase };
  }

  should_shrink_zone(): boolean {
    const current_time = Date.now() / 1000;
    return (
      current_time >= this.next_zone_shrink_time &&
      this.safe_zone_scale > this.min_zone_scale
    );
  }

  should_spawn_bonus_zone(): boolean {
    const current_time = Date.now() / 1000;
    return current_time >= this.next_bonus_zone_time;
  }

  shrink_safe_zone(): boolean {
    if (this.safe_zone_scale <= this.min_zone_scale) {
      return false;
    }

    this.safe_zone_scale *= this.zone_shrink_rate;
    this.safe_zone_radius = Math.floor(
      this.original_radius * this.safe_zone_scale,
    );

    const current_time = Date.now() / 1000;
    this.last_zone_shrink_time = current_time;
    this.next_zone_shrink_time = current_time + this.zone_shrink_interval;

    this.zone_damage_per_second += 0.5;

    return true;
  }

  spawn_bonus_zone(): boolean {
    if (this.zone_fund < 20) {
      return false;
    }

    const zone_x = Math.floor(Math.random() * (this.radius - 200)) + 100;
    const zone_y = Math.floor(Math.random() * (this.radius - 200)) + 100;
    const zone_radius = 80;

    const multiplier = this.bonus_zones.length % 2 === 0 ? 2 : 3;

    const bonus_zone = new BonusZone(zone_x, zone_y, zone_radius, multiplier);
    this.bonus_zones.push(bonus_zone);

    this.zone_fund -= 20;

    const current_time = Date.now() / 1000;
    this.last_bonus_zone_time = current_time;
    this.next_bonus_zone_time = current_time + this.bonus_zone_interval;

    return true;
  }

  update_bonus_zones(): void {
    this.bonus_zones = this.bonus_zones.filter((zone) => !zone.is_expired());

    for (const player of this.players.values()) {
      player.in_bonus_zone = false;
      player.current_bonus_multiplier = 1;

      for (const zone of this.bonus_zones) {
        if (zone.is_player_in_zone(player.x, player.y)) {
          player.in_bonus_zone = true;
          player.current_bonus_multiplier = zone.multiplier;
          break;
        }
      }
    }
  }

  get_safe_zone_bounds(): Zone {
    return { x: 0, y: 0, radius: this.safe_zone_radius };
  }

  update_zone_damage(): void {
    for (const player of this.players.values()) {
      if (player.is_outside_safe_zone(this.safe_zone_radius)) {
        player.apply_zone_damage(this.zone_damage_per_second);
      } else {
        player.reset_zone_damage_timer();
      }
    }
  }

  add_player(player_id: string, username?: string): void {
    this.players.set(
      player_id,
      new Player(
        Math.floor(Math.random() * this.radius),
        Math.floor(Math.random() * this.radius),
        player_id,
        this.radius,
        username,
      ),
    );
  }

  remove_player(player_id: string): void {
    this.players.delete(player_id);
  }

  move_player(player_id: string, dx: number, dy: number): void {
    const player = this.players.get(player_id);
    if (player) {
      player.move(dx, dy, this.radius);
    }
  }

  activate_skill(
    player_id: string,
    skill_type: string,
    is_free: boolean = false,
  ): [boolean, string, number] {
    const player = this.players.get(player_id);
    if (!player) {
      return [false, 'player_not_in_game', 0];
    }

    if (this.game_phase === GamePhases.FINISHED || player.to_remove) {
      return [false, 'game_not_active', 0];
    }

    if (!['teleport', 'shield', 'boost'].includes(skill_type)) {
      return [false, 'invalid_skill_type', 0];
    }

    // Делаем скиллы бесплатными: игнорируем требования по балансу,
    // но сохраняем лимиты по количеству и кулдаунам.
    const [can_use, message] = player.can_use_skill(skill_type, true);
    if (!can_use) {
      return [false, message, 0];
    }

    // Полностью отключаем стоимость скиллов
    let cost = 0;

    if (skill_type === 'teleport') {
      player.activate_teleport();
      if (is_free) {
        player.free_teleport_used = true;
      }
    } else if (skill_type === 'shield') {
      player.activate_shield();
    } else if (skill_type === 'boost') {
      player.activate_speed_boost();
    }

    return [true, 'OK', cost];
  }

  get_skill_cost(player_id: string, skill_type: string): number {
    const player = this.players.get(player_id);
    if (!player) {
      return 0;
    }
    return player.get_skill_cost_amount(skill_type);
  }

  update(): void {
    const new_phase = this.check_phase_transition();
    if (new_phase !== this.game_phase) {
      if (new_phase === GamePhases.TOP_10) {
        this.start_top10_voting();
      } else if (new_phase === GamePhases.SUPER) {
        this.process_voting_results();
      } else if (new_phase === GamePhases.FINISHED) {
        this.finalize_game();
        return;
      }
    }

    if (this.game_phase === GamePhases.TOP_10) {
      this.process_voting_results();
    }

    if (
      this.game_phase === GamePhases.SUPER &&
      this.should_end_super_game()
    ) {
      this.finalize_game();
      return;
    }

    if (
      (this.game_phase === GamePhases.START ||
        this.game_phase === GamePhases.SUPER) &&
      this.should_shrink_zone()
    ) {
      this.shrink_safe_zone();
    }

    if (
      (this.game_phase === GamePhases.START ||
        this.game_phase === GamePhases.SUPER) &&
      this.should_spawn_bonus_zone()
    ) {
      this.spawn_bonus_zone();
    }

    this.update_bonus_zones();
    this.update_zone_damage();

    for (const player of this.players.values()) {
      player.update_skills();

      for (let i = this.foods.length - 1; i >= 0; i--) {
        const food = this.foods[i];
        if (player.have_colision(food.x, food.y, Math.floor(food.mass))) {
          let food_value = food.mass;
          if (player.in_bonus_zone) {
            food_value *= player.current_bonus_multiplier;
            player.bonus_zone_collected += 1;
          }

          player.money += food_value / 20;
          this.foods.splice(i, 1);
          this.fund -= this.food_mass;

          this.foods.push(
            new Food(this.radius, Math.floor(Math.random() * 2) + 1),
          );
        }
      }

      for (const p2 of this.players.values()) {
        if (p2 === player) continue;

        if (player.have_colision(p2.x, p2.y, p2.get_radius())) {
          if (player.money > p2.money) {
            player.money += p2.money;
            p2.to_remove = true;
          } else if (p2.money > player.money) {
            p2.money += player.money;
            player.to_remove = true;
            break;
          }
        }
      }
    }

    const players_to_remove: string[] = [];
    for (const [player_id, player] of this.players.entries()) {
      if (player.to_remove) {
        players_to_remove.push(player_id);
      }
    }

    for (const player_id of players_to_remove) {
      this.players.delete(player_id);
    }
  }

  get_state(): GameState {
    const safe_zone_bounds = this.get_safe_zone_bounds();
    const phase_info = this.get_game_phase_info();

    const players_data: Array<Record<string, any>> = [];
    for (const [pid, p] of this.players.entries()) {
      players_data.push({
        [pid]: {
          x: p.x,
          y: p.y,
          mass: p.get_radius(),
          money: p.money,
          color: p.color,
          shield_active: p.shield_active,
          speed_boost_active: p.speed_boost_active,
          skills_used: p.skills_used,
          zone_damage_taken: 1,
          in_bonus_zone: p.in_bonus_zone,
          bonus_multiplier: p.current_bonus_multiplier,
          outside_zone: true,
          bonus_zone_collected: p.bonus_zone_collected,
          cooldowns: {
            teleport: Math.round(Math.max(0, p.teleport_cooldown) * 10) / 10,
            shield: Math.round(Math.max(0, p.shield_cooldown) * 10) / 10,
            boost: Math.round(Math.max(0, p.boost_cooldown) * 10) / 10,
          },
          username: p.username,
          teleport_effect_time: p.teleport_effect_time
            ? p.teleport_effect_time * 1000
            : undefined,
          shield_end_time: p.shield_end_time ? p.shield_end_time * 1000 : undefined,
          speed_boost_end_time: p.speed_boost_end_time
            ? p.speed_boost_end_time * 1000
            : undefined,
        },
      });
    }

    const state: GameState = {
      zone_fund: this.zone_fund,
      bonus_fund: this.bonus_fund,
      time_to_next_bonus_zone: this.get_time_to_next_bonus_zone(),
      game_phase: phase_info,
      foods: this.foods.map((f) => ({
        x: f.x,
        y: f.y,
        mass: f.mass,
        color: f.color,
      })),
      map_info: {
        radius: this.radius,
        player_count: this.players.size,
        expected_players: this.expected_players,
      },
      players: players_data,
      bonus_zones: this.get_bonus_zones(),
      safe_zone: {
        x: safe_zone_bounds.x,
        y: safe_zone_bounds.y,
        radius: safe_zone_bounds.radius,
        scale: this.safe_zone_scale,
        damage_per_second: this.zone_damage_per_second,
        time_to_next_shrink: this.get_time_to_next_shrink(),
        game_time: this.get_game_time(),
      },
    };

    if (this.early_exits.size > 0) {
      state.early_exits = Object.fromEntries(this.early_exits);
    }
    if (this.super_exits.size > 0) {
      state.super_exits = Object.fromEntries(this.super_exits);
    }
    if (this.finalists.length > 0) {
      state.finalists = this.finalists;
    }

    return state;
  }
}

const _active_games: Map<string, Game> = new Map();

export async function create_game(
  g_id: string,
  expected_players: number = 10,
  fund: number = 100,
): Promise<Game> {
  const new_game = new Game(expected_players, fund);
  _active_games.set(g_id, new_game);
  return new_game;
}

export async function get_game(g_id: string): Promise<Game | undefined> {
  return _active_games.get(g_id);
}

export async function set_changes(g_id: string, data: Game): Promise<void> {
  _active_games.set(g_id, data);
}

export async function close_game(g_id: string): Promise<void> {
  _active_games.delete(g_id);
}

export class BetaGame extends Game {
  bot_players: Map<string, Player> = new Map();

  constructor(expected_players: number, fund: number) {
    super(10, fund);
    for (let i = 1; i < 10; i++) {
      const bot_id = `bot_${i}`;
      const bot = new Player(
        Math.floor(Math.random() * this.radius),
        Math.floor(Math.random() * this.radius),
        bot_id,
        this.radius,
      );
      this.bot_players.set(bot_id, bot);
      this.players.set(bot_id, bot);
    }
  }

  get_skill_cost_percentage(player_id: string, skill_type: string): number {
    return 0.0;
  }
}

const _beta_active_games: Map<string, BetaGame> = new Map();

export async function create_beta_game(
  g_id: string,
  expected_players: number = 10,
  fund: number = 10000,
): Promise<BetaGame> {
  const new_game = new BetaGame(expected_players, fund);
  _beta_active_games.set(g_id, new_game);
  return new_game;
}

export async function get_beta_game(
  g_id: string,
): Promise<BetaGame | undefined> {
  return _beta_active_games.get(g_id);
}

export async function set_beta_changes(
  g_id: string,
  data: BetaGame,
): Promise<void> {
  _beta_active_games.set(g_id, data);
}

export async function close_beta_game(g_id: string): Promise<void> {
  _beta_active_games.delete(g_id);
}


