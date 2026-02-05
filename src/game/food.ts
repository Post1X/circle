export class Food {
  x: number;
  y: number;
  mass: number;
  color: [number, number, number];
  sprite_type: string;

  private sprite_types = [
    'coin',
    'gem',
    'star',
    'diamond',
    'crystal',
    'orb',
    'cube',
    'pyramid',
  ];

  constructor(radius: number, mass: number) {
    // Координаты еды генерируем в той же системе, что и игрока:
    // центр в (0, 0), допустимый диапазон [-radius, radius].
    this.x = Math.floor(Math.random() * (radius * 2)) - radius;
    this.y = Math.floor(Math.random() * (radius * 2)) - radius;
    this.mass = mass;
    this.sprite_type =
      this.sprite_types[
        Math.floor(Math.random() * this.sprite_types.length)
      ];
    this._set_color_by_sprite_type();
  }

  private _set_color_by_sprite_type(): void {
    const sprite_colors: Record<string, [number, number, number]> = {
      coin: [255, 215, 0],
      gem: [138, 43, 226],
      star: [255, 255, 0],
      diamond: [0, 191, 255],
      crystal: [255, 20, 147],
      orb: [50, 205, 50],
      cube: [255, 69, 0],
      pyramid: [128, 0, 128],
    };

    this.color = sprite_colors[this.sprite_type] || [0, 255, 0];
  }
}

export function gen_food(
  fund: number,
  radius: number,
  num: number = 100,
): [Food[], number] {
  const num_food = Math.min(100, Math.floor(Math.random() * (radius / 100)) + 500);
  const food_fund = Math.floor(fund / num_food);
  const foods: Food[] = [];
  for (let i = 0; i < 100; i++) {
    foods.push(new Food(radius, Math.floor(Math.random() * 2) + 1));
  }
  return [foods, food_fund];
}


