import { BonusZone } from './bonus-zone';

export class Player {
  x: number;
  y: number;
  radius: number = 5;
  money: number = 0;
  username: string;
  color: [number, number, number];
  player_id: string;
  map_radius: number;

  skills_used: number = 0;
  max_skills_per_game: number = 5;
  free_teleport_used: boolean = false;

  shield_active: boolean = false;
  shield_end_time: number = 0;
  speed_boost_active: boolean = false;
  speed_boost_end_time: number = 0;
  teleport_effect_time: number = 0;

  teleport_cooldown: number = 0;
  shield_cooldown: number = 0;
  boost_cooldown: number = 0;

  base_speed: number = 10.0;
  boost_speed_multiplier: number = 2.0;

  outside_zone_damage: number = 0;
  last_zone_damage_time: number = 0;

  in_bonus_zone: boolean = false;
  current_bonus_multiplier: number = 1;
  bonus_zone_collected: number = 0;

  final_winnings: number = 0;

  target_x: number | null = null;
  target_y: number | null = null;

  to_remove: boolean = false;

  constructor(
    x: number,
    y: number,
    player_id: string,
    radius: number,
    username?: string,
  ) {
    this.x = x;
    this.y = y;
    this.player_id = player_id;
    this.map_radius = radius;
    this.username = username || `Player_${player_id.substring(0, 8)}`;

    this.color = [
      Math.floor(Math.random() * 205) + 50,
      Math.floor(Math.random() * 205) + 50,
      Math.floor(Math.random() * 205) + 50,
    ] as [number, number, number];
  }

  get_radius(): number {
    if (this.money <= 0) {
      return 5.0;
    }

    const mass = 5 + Math.log(this.money + 1) * 8;
    const radius = Math.min(100, Math.max(5, mass));
    return Math.round(radius * 10) / 10;
  }

  have_colision(x: number, y: number, radius: number): boolean {
    const dis = Math.sqrt(
      Math.pow(this.x - x, 2) + Math.pow(this.y - y, 2),
    );
    return dis < this.get_radius() + radius;
  }

  is_outside_safe_zone(safe_radius: number): boolean {
    return !(this.x < safe_radius && this.y < safe_radius);
  }

  apply_zone_damage(damage_per_second: number = 2.0): void {
    const current_time = Date.now() / 1000;

    if (this.last_zone_damage_time === 0) {
      this.last_zone_damage_time = current_time;
      return;
    }

    const time_diff = current_time - this.last_zone_damage_time;
    if (time_diff >= 1.0) {
      const damage = damage_per_second * time_diff;
      this.money -= damage;
      this.outside_zone_damage += damage;
      this.last_zone_damage_time = current_time;
    }
  }

  reset_zone_damage_timer(): void {
    this.last_zone_damage_time = 0;
  }

  move(dx: number, dy: number, map_radius: number): void {
    const speed_multiplier = this.speed_boost_active
      ? this.boost_speed_multiplier
      : this.base_speed;
    this.x += dx * speed_multiplier;
    this.y += dy * speed_multiplier;

    if (this.x > map_radius) {
      this.x = map_radius;
    } else if (this.x < 0) {
      this.x = 0;
    }

    if (this.y > map_radius) {
      this.y = map_radius;
    } else if (this.y < 0) {
      this.y = 0;
    }
  }

  update_skills(): void {
    const current_time = Date.now() / 1000;

    if (this.teleport_effect_time > 0 && current_time >= this.teleport_effect_time) {
      this.teleport_effect_time = 0;
    }

    if (this.shield_active && current_time >= this.shield_end_time) {
      this.shield_active = false;
    }

    if (this.speed_boost_active && current_time >= this.speed_boost_end_time) {
      this.speed_boost_active = false;
    }

    if (this.teleport_cooldown > 0) {
      this.teleport_cooldown = Math.max(0, this.teleport_cooldown - 0.05);
    }
    if (this.shield_cooldown > 0) {
      this.shield_cooldown = Math.max(0, this.shield_cooldown - 0.05);
    }
    if (this.boost_cooldown > 0) {
      this.boost_cooldown = Math.max(0, this.boost_cooldown - 0.05);
    }
  }

  can_use_skill(skill_type: string): [boolean, string] {
    if (this.money < 1.0) {
      return [false, 'minimum_balance_required'];
    }

    if (this.skills_used >= this.max_skills_per_game) {
      return [false, 'skill_limit_reached'];
    }

    if (skill_type === 'teleport' && this.teleport_cooldown > 0) {
      return [false, 'skill_on_cooldown'];
    } else if (skill_type === 'shield' && this.shield_cooldown > 0) {
      return [false, 'skill_on_cooldown'];
    } else if (skill_type === 'boost' && this.boost_cooldown > 0) {
      return [false, 'skill_on_cooldown'];
    }

    return [true, 'OK'];
  }

  activate_teleport(): void {
    this.x = Math.floor(Math.random() * (this.map_radius - 100)) + 50;
    this.y = Math.floor(Math.random() * (this.map_radius - 100)) + 50;
    this.teleport_cooldown = 60.0;
    this.teleport_effect_time = Date.now() / 1000 + 1.0;
    this.skills_used += 1;
  }

  activate_shield(): void {
    this.shield_active = true;
    this.shield_end_time = Date.now() / 1000 + 3.0;
    this.shield_cooldown = 30.0;
    this.skills_used += 1;
  }

  activate_speed_boost(): void {
    this.speed_boost_active = true;
    this.speed_boost_end_time = Date.now() / 1000 + 5.0;
    this.boost_cooldown = 15.0;
    this.skills_used += 1;
  }

  get_skill_cost_percentage(skill_type: string): number {
    const base_costs: Record<string, number> = {
      teleport: 0.15,
      shield: 0.1,
      boost: 0.05,
    };

    let base_cost = base_costs[skill_type] || 0;

    if (this.free_teleport_used) {
      base_cost += 0.05;
    }

    return base_cost;
  }

  get_skill_cost_amount(skill_type: string): number {
    const percentage = this.get_skill_cost_percentage(skill_type);
    return this.money * percentage;
  }

  reset_for_new_game(): void {
    this.skills_used = 0;
    this.free_teleport_used = false;

    this.shield_active = false;
    this.shield_end_time = 0;
    this.speed_boost_active = false;
    this.speed_boost_end_time = 0;
    this.teleport_effect_time = 0;

    this.teleport_cooldown = 0;
    this.shield_cooldown = 0;
    this.boost_cooldown = 0;

    this.outside_zone_damage = 0;
    this.last_zone_damage_time = 0;

    this.in_bonus_zone = false;
    this.current_bonus_multiplier = 1;
    this.bonus_zone_collected = 0;

    this.final_winnings = 0;

    this.target_x = null;
    this.target_y = null;

    this.to_remove = false;
  }
}


