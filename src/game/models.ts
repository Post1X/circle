export enum GamePhases {
  START = 'start',
  TOP_10 = 'top10',
  SUPER = 'super',
  FINISHED = 'finished',
}

export interface Zone {
  x: number;
  y: number;
  radius: number;
}

export interface SaveZone extends Zone {
  scale: number;
  damage_per_second: number;
  time_to_next_shrink: number;
  game_time: number;
}

export interface BonusZoneModel extends Zone {
  multiplier: number;
  remaining_time: number;
  funds_collected: number;
  max_funds: number;
}

export interface Phase {
  phase: GamePhases;
  super_game_time_remaining?: number;
  skill_costs_increased?: boolean;
  voting_time_remaining?: number;
  votes_submitted?: number;
  votes_exit?: number;
  votes_super?: number;
}

export interface Cooldowns {
  teleport: number;
  shield: number;
  boost: number;
}

export interface PlayerData {
  x: number;
  y: number;
  mass: number;
  money: number;
  color: [number, number, number];
  shield_active: boolean;
  speed_boost_active: boolean;
  skills_used: number;
  outside_zone: boolean;
  zone_damage_taken: number;
  in_bonus_zone: boolean;
  bonus_multiplier: number;
  bonus_zone_collected: number;
  cooldowns: Cooldowns;
  username: string;
  teleport_effect_time?: number;
  shield_end_time?: number;
  speed_boost_end_time?: number;
}

export interface MapInfo {
  radius: number;
  player_count: number;
  expected_players: number;
}

export interface FoodModel {
  x: number;
  y: number;
  mass: number;
  color: [number, number, number];
}

export interface GameState {
  map_info: MapInfo;
  safe_zone: SaveZone;
  bonus_zones: (BonusZoneModel | null)[];
  zone_fund: number;
  bonus_fund: number;
  time_to_next_bonus_zone: number;
  game_phase: Phase;
  players: Array<Record<string, PlayerData>>;
  foods: FoodModel[];
  early_exits?: Record<string, number>;
  super_exits?: Record<string, number>;
  finalists?: string[];
}


