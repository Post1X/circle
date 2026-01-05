export class BonusZone {
  x: number;
  y: number;
  radius: number;
  multiplier: number;
  duration: number;
  start_time: number;
  end_time: number;
  is_active: boolean;
  funds_generated: number;
  funds_collected: number;

  constructor(
    x: number,
    y: number,
    radius: number,
    multiplier: number,
    duration: number = 30.0,
  ) {
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.multiplier = multiplier;
    this.duration = duration;
    this.start_time = Date.now() / 1000;
    this.end_time = this.start_time + duration;
    this.is_active = true;
    this.funds_generated = 20;
    this.funds_collected = 0;
  }

  is_expired(): boolean {
    return Date.now() / 1000 >= this.end_time;
  }

  is_player_in_zone(player_x: number, player_y: number): boolean {
    const distance = Math.sqrt(
      Math.pow(player_x - this.x, 2) + Math.pow(player_y - this.y, 2),
    );
    return distance <= this.radius;
  }

  get_remaining_time(): number {
    return Math.max(0, this.end_time - Date.now() / 1000);
  }

  collect_funds(amount: number): number {
    if (!this.is_active) {
      return 0;
    }

    const max_collectible = this.funds_generated * this.multiplier;
    if (this.funds_collected >= max_collectible) {
      return 0;
    }

    const collectible = Math.min(amount, max_collectible - this.funds_collected);
    this.funds_collected += collectible;
    return collectible * this.multiplier;
  }
}


