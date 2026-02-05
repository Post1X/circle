import random
import time
from math import atan2, cos, sin, sqrt
from typing import List, Optional

from .models import (
    BonusZoneModel,
    Cooldowns,
    FoodModel,
    GamePhases,
    GameState,
    MapInfo,
    Phase,
    PlayerData,
    SaveZone,
    Zone,
)

# Базовые размеры карты
BASE_RADIUS = 400
FOOD_COLLISION_FACTOR = 0.2


def calculate_map_size(player_count: int) -> int:
    """
    Рассчитывает размеры карты в зависимости от количества игроков.

    Логика масштабирования:
    - 1-5 игроков: базовый размер 800x800
    - 6-20 игроков: линейное увеличение до 1200x1200
    - 21-50 игроков: увеличение до 1600x1600
    - 51-100 игроков: увеличение до 2000x2000
    - 100+ игроков: максимальный размер 2400x2400
    """
    if player_count <= 5:
        scale_factor = 1
    elif player_count <= 20:
        scale_factor = 1 + (player_count - 5) * 0.027
    elif player_count <= 50:
        scale_factor = 1.5 + (player_count - 20) * 0.017
    elif player_count <= 100:
        scale_factor = 2.0 + (player_count - 50) * 0.01
    else:
        scale_factor = min(3.0, 2.5 + (player_count - 100) * 0.005)
    return int(BASE_RADIUS * scale_factor)


class BonusZone:
    """Класс для бонусных зон с множителями"""

    def __init__(
        self, x: int, y: int, radius: int, multiplier: int, duration: float = 30.0
    ):
        self.x = x
        self.y = y
        self.radius = radius
        self.multiplier = multiplier
        self.duration = duration
        self.start_time = time.time()
        self.end_time = self.start_time + duration
        self.is_active = True
        self.funds_generated = 20
        self.funds_collected = 0

    def is_expired(self) -> bool:
        """Проверяет, истекло ли время действия зоны"""
        return time.time() >= self.end_time

    def is_player_in_zone(self, player_x: float, player_y: float) -> bool:
        """Проверяет, находится ли игрок в бонусной зоне"""
        distance = sqrt((player_x - self.x) ** 2 + (player_y - self.y) ** 2)
        return distance <= self.radius

    def get_remaining_time(self) -> float:
        """Возвращает оставшееся время действия зоны"""
        return max(0, self.end_time - time.time())

    def collect_funds(self, amount: float) -> float:
        """Собирает средства из зоны с учетом множителя"""
        if not self.is_active:
            return 0

        max_collectible = self.funds_generated * self.multiplier
        if self.funds_collected >= max_collectible:
            return 0

        collectible = min(amount, max_collectible - self.funds_collected)
        self.funds_collected += collectible
        return collectible * self.multiplier


class Player:
    def __init__(self, x: float, y: float, player_id: str, radius: int, username: str = None):
        self.x: float = x
        self.y: float = y
        self.radius = 5

        self.money: float = 0
        self.username: str = username or f"Player_{player_id[:8]}"
        self.color = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255),
        )
        self.player_id: str = player_id
        self.map_radius: int = radius

        self.skills_used: int = 0
        self.max_skills_per_game: int = 5

        self.shield_active: bool = False
        self.shield_end_time: float = 0
        self.speed_boost_active: bool = False
        self.speed_boost_end_time: float = 0
        self.teleport_effect_time: float = 0  # Время окончания эффекта телепорта

        self.teleport_cooldown: float = 0
        self.shield_cooldown: float = 0
        self.boost_cooldown: float = 0

        self.base_speed: float = 10.0
        self.boost_speed_multiplier: float = 2.0

        self.outside_zone_damage: float = 0
        self.last_zone_damage_time: float = 0

        # Бонусные зоны
        self.in_bonus_zone: bool = False
        self.current_bonus_multiplier: float = 1
        self.bonus_zone_collected: int = 0

        # Финальные выигрыши
        self.final_winnings: float = 0

        # Целевые координаты для ботов
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None

    def get_radius(self, all_money: float = 1_000, players: int = 50) -> float:
        # Рассчитываем массу на основе собранных денег
        # Минимальная масса 5, максимальная 100
        if self.money <= 0:
            return 5.0
        
        # Логарифмический рост массы для более сбалансированной игры
        import math
        mass = 5 + math.log(self.money + 1) * 8  # +1 чтобы избежать log(0)
        radius = min(100, max(5, mass))
        return round(radius, 1)

    def have_colision(
        self,
        x: int,
        y: int,
        radius: int,
    ) -> bool:
        dis = sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        # Еда (или другой объект) должна считаться съеденной/задетой,
        # если расстояние между центрами меньше либо РАВНО сумме радиусов.
        return dis <= (self.get_radius() + radius)

    def is_outside_safe_zone(self, safe_radius: int) -> bool:
        """Проверяет, находится ли игрок за пределами безопасной зоны"""
        return not (self.x < safe_radius and self.y < safe_radius)

    def apply_zone_damage(self, damage_per_second: float = 2.0):
        """Применяет урон от нахождения вне безопасной зоны"""
        current_time = time.time()

        if self.last_zone_damage_time == 0:
            self.last_zone_damage_time = current_time
            return

        time_diff = current_time - self.last_zone_damage_time
        if time_diff >= 1.0:  # Урон каждую секунду
            damage = damage_per_second * time_diff
            self.money -= damage
            self.outside_zone_damage += damage
            self.last_zone_damage_time = current_time

    def reset_zone_damage_timer(self):
        """Сбрасывает таймер урона от зоны"""
        self.last_zone_damage_time = 0

    def move(self, dx, dy, map_radius):
        speed_multiplier = (
            self.boost_speed_multiplier if self.speed_boost_active else self.base_speed
        )
        self.x += dx * speed_multiplier
        self.y += dy * speed_multiplier

        if self.x > map_radius:
            self.x = map_radius
        elif self.x < 0:
            self.x = 0

        if self.y > map_radius:
            self.y = map_radius
        elif self.y < 0:
            self.y = 0

    def update_skills(self):
        """Update skill states and cooldowns"""
        current_time = time.time()

        # Update teleport effect
        if self.teleport_effect_time > 0 and current_time >= self.teleport_effect_time:
            self.teleport_effect_time = 0

        # Update shield status
        if self.shield_active and current_time >= self.shield_end_time:
            self.shield_active = False

        # Update speed boost status
        if self.speed_boost_active and current_time >= self.speed_boost_end_time:
            self.speed_boost_active = False

        # Update cooldowns
        if self.teleport_cooldown > 0:
            self.teleport_cooldown = max(
                0, self.teleport_cooldown - 0.05
            )  # Decrease by game tick
        if self.shield_cooldown > 0:
            self.shield_cooldown = max(0, self.shield_cooldown - 0.05)
        if self.boost_cooldown > 0:
            self.boost_cooldown = max(0, self.boost_cooldown - 0.05)

    def can_use_skill(self, skill_type):
        """Check if player can use a specific skill"""
        if self.skills_used >= self.max_skills_per_game:
            return False, "Max skills per game reached"

        if skill_type == "teleport" and self.teleport_cooldown > 0:
            return False, f"Teleport on cooldown: {self.teleport_cooldown:.1f}s"
        elif skill_type == "shield" and self.shield_cooldown > 0:
            return False, f"Shield on cooldown: {self.shield_cooldown:.1f}s"
        elif skill_type == "boost" and self.boost_cooldown > 0:
            return False, f"Boost on cooldown: {self.boost_cooldown:.1f}s"

        return True, "OK"

    def activate_teleport(self):
        """Teleport to random safe location"""
        self.x = random.randint(50, self.map_radius - 50)
        self.y = random.randint(50, self.map_radius - 50)
        self.teleport_cooldown = 60.0
        self.teleport_effect_time = time.time() + 1.0  # Эффект длится 1 секунду
        self.skills_used += 1
        print(f"TELEPORT ACTIVATED: Player {self.player_id}, effect_time: {self.teleport_effect_time}")

    def activate_shield(self):
        """Activate 3-second shield"""
        self.shield_active = True
        self.shield_end_time = time.time() + 3.0
        self.shield_cooldown = 30.0
        self.skills_used += 1
        print(f"SHIELD ACTIVATED: Player {self.player_id}, end_time: {self.shield_end_time}")

    def activate_speed_boost(self):
        """Activate 5-second speed boost"""
        self.speed_boost_active = True
        self.speed_boost_end_time = time.time() + 5.0
        self.boost_cooldown = 15.0
        self.skills_used += 1
        print(f"SPEED BOOST ACTIVATED: Player {self.player_id}, end_time: {self.speed_boost_end_time}")

    def get_skill_cost_percentage(self, skill_type):
        """Get cost percentage for skill"""
        if skill_type == "teleport":
            return 0.15  # 15%
        elif skill_type == "shield":
            return 0.10  # 10%
        elif skill_type == "boost":
            return 0.05  # 5%
        return 0


class Food:
    def __init__(self, radius: int, mass: float):
        self.x = random.randint(0, radius - 1)
        self.y = random.randint(0, radius - 1)
        self.mass = mass
        self.color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        self.sprite_types = [
            "coin",  # Монета
            "gem",  # Драгоценный камень
            "star",  # Звезда
            "diamond",  # Алмаз
            "crystal",  # Кристалл
            "orb",  # Сфера
            "cube",  # Куб
            "pyramid",  # Пирамида
        ]

        self.sprite_type = random.choice(self.sprite_types)

        self._set_color_by_sprite_type()

    def _set_color_by_sprite_type(self):
        """Устанавливает цвет еды в зависимости от типа спрайта"""
        sprite_colors = {
            "coin": (255, 215, 0),  # Золотой
            "gem": (138, 43, 226),  # Фиолетовый
            "star": (255, 255, 0),  # Желтый
            "diamond": (0, 191, 255),  # Голубой
            "crystal": (255, 20, 147),  # Розовый
            "orb": (50, 205, 50),  # Зеленый
            "cube": (255, 69, 0),  # Оранжевый
            "pyramid": (128, 0, 128),  # Темно-фиолетовый
        }

        self.color = sprite_colors.get(self.sprite_type, (0, 255, 0))


def gen_food(fund: float, radius: int, num=100) -> tuple[list[Food], int]:
    num_food = min(100, random.randint(int(radius / 100), 500))
    food_fund = int(fund / num_food)
    return [
        # Food(radius=radius, mass=food_fund) for _ in range(min(num_food, num))
        # Food(radius=radius, mass=random.randint(1, 3)) for _ in range(min(num_food, num))
        Food(radius=radius, mass=random.randint(1, 3))
        for _ in range(100)
    ], food_fund


class Game:
    def __init__(self, expected_players: int, fund: float):
        """
        Инициализация игры с предварительным расчетом размера карты

        Args:
            expected_players: Ожидаемое количество игроков для расчета размера карты
        """
        self.players = {}
        self.fund: float = fund

        self.radius = calculate_map_size(expected_players)
        self.expected_players = expected_players

        self.original_radius = self.radius
        self.safe_zone_radius = self.radius
        self.safe_zone_scale = 1.0

        self.zone_shrink_interval = 120.0
        self.zone_shrink_rate = 0.9
        self.min_zone_scale = 0.1

        self.game_start_time = time.time()
        self.last_zone_shrink_time = self.game_start_time
        self.next_zone_shrink_time = self.game_start_time + self.zone_shrink_interval

        self.zone_damage_per_second = 2.0

        self.foods, self.food_mass = gen_food(fund=self.fund, radius=self.radius)

        # Бонусные зоны согласно ТЗ
        self.bonus_zones: List[BonusZone] = []
        self.bonus_zone_interval = 180.0
        self.last_bonus_zone_time = self.game_start_time
        self.next_bonus_zone_time = self.game_start_time + self.bonus_zone_interval
        self.zone_fund = 200  # $200 зональный фонд
        self.bonus_fund = 0  # Бонусный фонд

        # Фазы игры
        self.game_phase = GamePhases.START  # start, top10, super
        self.players_remaining = 0

        self.voting_start_time = None
        self.voting_duration = 30.0  # 30 секунд на голосование
        self.votes = {}  # player_id: "exit" или GamePhases.SUPER
        self.voting_completed = False

        # Супер игра
        self.super_game_start_time = 0
        self.super_game_duration = 300.0  # 5 минут
        self.super_game_zone_shrink_rate = 0.96  # 4% в минуту (20% за 5 минут)
        self.super_game_min_zone_scale = 0.2  # 20% от начального размера

        # Выходы игроков
        self.early_exits = {}  # player_id: collected_amount
        self.super_exits = {}  # player_id: collected_amount
        self.finalists = []  # Список финалистов

        # Навыки в супер игре
        self.skill_costs_increased = False  # Флаг увеличения стоимости навыков
        self.last_chance_used = {}  # player_id: True если использовал "последний шанс"

    def get_game_time(self) -> float:
        """Возвращает время с начала игры в секундах"""
        return time.time() - self.game_start_time

    def get_bonus_zones(self) -> list[BonusZoneModel]:
        return [
            BonusZoneModel(
                x=z.x,
                y=z.y,
                radius=z.radius,
                multiplier=z.multiplier,
                remaining_time=z.get_remaining_time(),
                funds_collected=z.funds_collected,
                max_funds=z.funds_generated * z.multiplier,
            )
            for z in self.bonus_zones
        ]

    def get_time_to_next_shrink(self) -> float:
        """Возвращает время до следующего сужения зоны в секундах"""
        return max(0, self.next_zone_shrink_time - time.time())

    def get_time_to_next_bonus_zone(self) -> float:
        """Возвращает время до следующей бонусной зоны в секундах"""
        return max(0, self.next_bonus_zone_time - time.time())

    def check_phase_transition(self) -> GamePhases:
        """Проверяет необходимость перехода между фазами игры"""
        if self.game_phase == GamePhases.START and len(self.players) <= 10:
            return GamePhases.TOP_10
        elif self.game_phase == GamePhases.TOP_10 and self.voting_completed:
            return GamePhases.SUPER
        elif len(self.players) <= 1:
            return GamePhases.FINISHED
        return self.game_phase

    def start_top10_voting(self):
        """Начинает голосование в топ-10"""
        self.game_phase = GamePhases.TOP_10
        self.voting_start_time = time.time()
        self.votes = {}
        self.voting_completed = False

        self.zone_shrink_interval = float("inf")
        self.bonus_zone_interval = float("inf")

    def submit_vote(self, player_id: str, vote: str) -> bool:
        """Отправляет голос игрока"""
        if self.game_phase != GamePhases.TOP_10 or self.voting_completed:
            return False

        if vote not in ["exit", GamePhases.SUPER]:
            return False

        if player_id not in self.players:
            return False

        self.votes[player_id] = vote
        return True

    def get_voting_time_remaining(self) -> float:
        """Возвращает оставшееся время голосования"""
        if not self.voting_start_time:
            return 0
        return max(0, self.voting_duration - (time.time() - self.voting_start_time))

    def should_end_voting(self) -> bool:
        """Проверяет, нужно ли завершить голосование"""
        if not self.voting_start_time:
            return False
        return time.time() - self.voting_start_time >= self.voting_duration

    def process_voting_results(self):
        """Обрабатывает результаты голосования"""
        if not self.should_end_voting():
            return

        self.voting_completed = True

        for player_id, vote in self.votes.items():
            if vote == "exit" and player_id in self.players:
                self.process_early_exit(player_id)

        self.start_super_game()

    def process_early_exit(self, player_id: str):
        """Обрабатывает ранний выход игрока (50% от собранного)"""
        if player_id not in self.players:
            return

        player: Player = self.players[player_id]
        collected_amount = player.money

        # 50% игроку, 50% в бонусный фонд
        player_winnings = collected_amount * 0.5
        bonus_contribution = collected_amount * 0.5

        self.early_exits[player_id] = player_winnings
        self.bonus_fund += bonus_contribution

        # Удаляем игрока
        del self.players[player_id]

    def start_super_game(self):
        """Начинает супер игру"""
        self.game_phase = GamePhases.SUPER
        self.super_game_start_time = time.time()

        self.zone_shrink_interval = 60.0
        self.zone_shrink_rate = self.super_game_zone_shrink_rate
        self.min_zone_scale = self.super_game_min_zone_scale

        self.bonus_zone_interval = 180.0

    def get_super_game_time_remaining(self) -> float:
        """Возвращает оставшееся время супер игры"""
        if not self.super_game_start_time:
            return 0
        return max(
            0, self.super_game_duration - (time.time() - self.super_game_start_time)
        )

    def should_end_super_game(self) -> bool:
        """Проверяет, нужно ли завершить супер игру"""
        if not self.super_game_start_time:
            return False
        return time.time() - self.super_game_start_time >= self.super_game_duration

    def process_super_exit(self, player_id: str):
        """Обрабатывает выход из супер игры (25% от собранного)"""
        if player_id not in self.players:
            return

        player: Player = self.players[player_id]
        collected_amount = player.money
        # 25% игроку, 75% в бонусный фонд
        player_winnings = collected_amount * 0.25
        bonus_contribution = collected_amount * 0.75

        self.super_exits[player_id] = player_winnings
        self.bonus_fund += bonus_contribution

        del self.players[player_id]

    def check_last_chance(self, player_id: str) -> bool:
        """Проверяет и активирует "последний шанс" для игрока"""
        if self.game_phase != GamePhases.SUPER:
            return False

        if player_id in self.last_chance_used:
            return False

        super_game_time = time.time() - self.super_game_start_time
        if super_game_time < 120 or super_game_time > 180:
            return False

        if player_id not in self.players:
            return False

        player: Player = self.players[player_id]
        if player.money >= 5:  # $5
            return False

        player.activate_teleport()
        self.last_chance_used[player_id] = True
        self.skill_costs_increased = True

        return True

    def get_skill_cost_percentage(self, player_id: str, skill_type: str) -> float:
        """Возвращает стоимость навыка с учетом увеличения в супер игре"""
        base_costs = {"teleport": 15.0, "shield": 10.0, "boost": 5.0}

        base_cost = base_costs.get(skill_type, 0)

        # Увеличиваем стоимость на 5% если использован "последний шанс"
        if self.skill_costs_increased:
            base_cost += 5.0

        return base_cost

    def finalize_game(self):
        """Завершает игру и распределяет бонусный фонд"""
        # Добавляем несобранные центы с карты в бонусный фонд
        remaining_food_value = len(self.foods) * self.food_mass
        self.bonus_fund += remaining_food_value

        # Добавляем остаток зонального фонда
        self.bonus_fund += self.zone_fund

        # Определяем финалистов
        self.finalists = list(self.players.keys())

        # Распределяем бонусный фонд между финалистами
        if self.finalists:
            total_finalist_money = sum(
                self.players[pid].money for pid in self.finalists
            )
            for player_id in self.finalists:
                player = self.players[player_id]
                player_share = 0
                if total_finalist_money != 0:
                    player_share = player.money / total_finalist_money
                player.final_winnings = self.bonus_fund * player_share

    def get_game_phase_info(self) -> Phase:
        """Возвращает информацию о текущей фазе игры"""
        if self.game_phase == GamePhases.TOP_10:
            return Phase(
                phase=self.game_phase,
                voting_time_remaining=self.get_voting_time_remaining(),
                votes_submitted=len(self.votes),
                votes_exit=sum(1 for v in self.votes.values() if v == "exit"),
                votes_super=sum(
                    1 for v in self.votes.values() if v == GamePhases.SUPER
                ),
            )
        elif self.game_phase == GamePhases.SUPER:
            return Phase(
                phase=self.game_phase,
                super_game_time_remaining=self.get_super_game_time_remaining(),
                skill_costs_increased=self.skill_costs_increased,
            )
        elif self.game_phase == GamePhases.FINISHED:
            return Phase(
                phase=self.game_phase,
            )
        return Phase(phase=self.game_phase)

    def should_shrink_zone(self) -> bool:
        """Проверяет, нужно ли сжать зону"""
        current_time = time.time()
        return (
            current_time >= self.next_zone_shrink_time
            and self.safe_zone_scale > self.min_zone_scale
        )

    def should_spawn_bonus_zone(self) -> bool:
        """Проверяет, нужно ли создать бонусную зону"""
        current_time = time.time()
        return current_time >= self.next_bonus_zone_time

    def shrink_safe_zone(self):
        """Сжимает безопасную зону"""
        if self.safe_zone_scale <= self.min_zone_scale:
            return False

        self.safe_zone_scale *= self.zone_shrink_rate
        self.safe_zone_radius = int(self.original_radius * self.safe_zone_scale)

        current_time = time.time()
        self.last_zone_shrink_time = current_time
        self.next_zone_shrink_time = current_time + self.zone_shrink_interval

        self.zone_damage_per_second += 0.5

        return True

    def spawn_bonus_zone(self):
        """Создает новую бонусную зону"""
        if self.zone_fund < 20:  # Минимум $20 для зоны
            return False

        # Случайное положение зоны
        zone_x = random.randint(100, self.radius - 100)
        zone_y = random.randint(100, self.radius - 100)
        zone_radius = 80

        # Чередование x2 и x3
        if len(self.bonus_zones) % 2 == 0:
            multiplier = 2
        else:
            multiplier = 3

        bonus_zone = BonusZone(zone_x, zone_y, zone_radius, multiplier)
        self.bonus_zones.append(bonus_zone)

        # Уменьшаем зональный фонд
        self.zone_fund -= 20

        current_time = time.time()
        self.last_bonus_zone_time = current_time
        self.next_bonus_zone_time = current_time + self.bonus_zone_interval

        return True

    def update_bonus_zones(self):
        """Обновляет состояние бонусных зон"""

        # Удаляем истекшие зоны
        self.bonus_zones = [zone for zone in self.bonus_zones if not zone.is_expired()]

        # Обновляем статус игроков в зонах
        for player in self.players.values():
            player.in_bonus_zone = False
            player.current_bonus_multiplier = 1

            for zone in self.bonus_zones:
                if zone.is_player_in_zone(player.x, player.y):
                    player.in_bonus_zone = True
                    player.current_bonus_multiplier = zone.multiplier
                    break

    def get_safe_zone_bounds(self) -> Zone:
        """Возвращает границы безопасной зоны"""
        return Zone(x=0, y=0, radius=self.safe_zone_radius)

    def update_zone_damage(self):
        """Обновляет урон игрокам вне безопасной зоны"""
        for player in self.players.values():
            if player.is_outside_safe_zone(self.safe_zone_radius):
                player.apply_zone_damage(self.zone_damage_per_second)
            else:
                player.reset_zone_damage_timer()

    def add_player(self, player_id, username=None):
        """Добавляет игрока без изменения размера карты"""
        self.players[player_id] = Player(
            x=random.randint(0, self.radius),
            y=random.randint(0, self.radius),
            player_id=player_id,
            radius=self.radius,
            username=username,
        )

    def remove_player(self, player_id):
        """Удаляет игрока без изменения размера карты"""
        if player_id in self.players:
            del self.players[player_id]

    def move_player(self, player_id, dx, dy):
        if player_id in self.players:
            self.players[player_id].move(dx, dy, self.radius)

    def activate_skill(self, player_id, skill_type):
        """Activate a skill for a player"""
        if player_id not in self.players:
            return False, "Player not found"

        player = self.players[player_id]
        can_use, message = player.can_use_skill(skill_type)

        if not can_use:
            return False, message

        # Activate the skill
        if skill_type == "teleport":
            player.activate_teleport()
        elif skill_type == "shield":
            player.activate_shield()
        elif skill_type == "boost":
            player.activate_speed_boost()
        else:
            return False, "Unknown skill type"

        return True, f"{skill_type.capitalize()} activated"

    def get_skill_cost(self, player_id, skill_type):
        """Calculate skill cost in dollars"""
        if player_id not in self.players:
            return 0

        cost_percentage = self.get_skill_cost_percentage(player_id, skill_type)
        return cost_percentage

    def update(self):
        # Проверяем переходы между фазами
        new_phase = self.check_phase_transition()
        if new_phase != self.game_phase:
            if new_phase == GamePhases.TOP_10:
                self.start_top10_voting()
            elif new_phase == GamePhases.SUPER:
                self.process_voting_results()
            elif new_phase == GamePhases.FINISHED:
                self.finalize_game()
                return

        # Обрабатываем голосование в топ-10
        if self.game_phase == GamePhases.TOP_10:
            self.process_voting_results()

        # Проверяем завершение супер игры
        if self.game_phase == GamePhases.SUPER and self.should_end_super_game():
            self.finalize_game()
            return

        # Обновляем сужение зоны (только в start и super фазах)
        if (
            self.game_phase in [GamePhases.START, GamePhases.SUPER]
            and self.should_shrink_zone()
        ):
            self.shrink_safe_zone()

        # Обновляем бонусные зоны (только в start и super фазах)
        if (
            self.game_phase in [GamePhases.START, GamePhases.SUPER]
            and self.should_spawn_bonus_zone()
        ):
            self.spawn_bonus_zone()

        self.update_bonus_zones()
        self.update_zone_damage()

        for player in self.players.values():
            if player:
                player: Player
                player.update_skills()
                if isinstance(self, BetaGame) and player.player_id.startswith("bot_"):
                    if (
                        player.target_x is None
                        or player.target_y is None
                        or (
                            abs(player.x - player.target_x) < 5
                            and abs(player.y - player.target_y) < 5
                        )
                    ):
                        player.target_x = random.randint(0, self.safe_zone_radius)
                        player.target_y = random.randint(0, self.safe_zone_radius)

                    angle = atan2(
                        player.target_y - player.y, player.target_x - player.x
                    )
                    dx = cos(angle)
                    dy = sin(angle)
                    player.move(dx, dy, self.radius)

                for food in self.foods[:]:
                    food_radius = max(1, int(food.mass))

                    # Столкновение еды и игрока считаем по сумме радиусов,
                    # как и при столкновении игроков между собой
                    if player.have_colision(food.x, food.y, food_radius):
                        # Применяем множитель бонусной зоны
                        food_value = food.mass
                        if player.in_bonus_zone:
                            food_value *= player.current_bonus_multiplier
                            # player.bonus_zone_collected += int(food_value)
                            player.bonus_zone_collected += 1

                        player.money += food_value / 20
                        self.foods.remove(food)
                        self.fund -= self.food_mass
                        # if self.food_mass > self.fund:
                        if True:
                            self.foods.append(
                                # Food(self.safe_zone_radius, self.food_mass)
                                Food(self.radius, random.randint(1, 3))  # Генерируем еду по всей карте
                            )

                for p2 in self.players.values():
                    if p2 == player:
                        continue

                    if player.have_colision(p2.x, p2.y, p2.get_radius()):
                        if (player.money > p2.money) or (
                            isinstance(self, BetaGame)
                            and not player.player_id.startswith("bot_")
                        ):
                            player.money += p2.money
                            # Помечаем игрока для удаления
                            p2.to_remove = True
                        elif p2.money > player.money:
                            p2.money += player.money
                            # Помечаем игрока для удаления
                            player.to_remove = True
                            break

        # Удаляем помеченных игроков
        players_to_remove = []
        for player_id, player in self.players.items():
            if hasattr(player, 'to_remove') and player.to_remove:
                players_to_remove.append(player_id)
        
        for player_id in players_to_remove:
            del self.players[player_id]

    def get_state(self) -> GameState:
        safe_zone_bounds = self.get_safe_zone_bounds()

        state = GameState(
            zone_fund=self.zone_fund,
            bonus_fund=self.bonus_fund,
            time_to_next_bonus_zone=self.get_time_to_next_bonus_zone(),
            game_phase=self.get_game_phase_info(),
            foods=[
                FoodModel(x=f.x, y=f.y, mass=f.mass, color=f.color) for f in self.foods
            ],
            map_info=MapInfo(
                radius=self.radius,
                player_count=len(self.players),
                exepcted_players=self.expected_players,
            ),
            players=[
                {
                    pid: PlayerData(
                        x=p.x,
                        y=p.y,
                        mass=p.get_radius(),
                        money=p.money,
                        color=p.color,
                        shield_active=p.shield_active,
                        speed_boost_active=p.speed_boost_active,
                        skills_used=p.skills_used,
                        zone_damage_taken=1,
                        in_bonus_zone=p.in_bonus_zone,
                        bonus_multiplier=1,
                        outside_zone=True,
                        bonus_zone_collected=p.bonus_zone_collected,
                        cooldowns=Cooldowns(
                            # Гарантируем, что cooldowns всегда отправляются, даже если они были сброшены
                            # Используем getattr для безопасности
                            teleport=float(round(max(0.0, getattr(p, 'teleport_cooldown', 0.0)), 1)),
                            shield=float(round(max(0.0, getattr(p, 'shield_cooldown', 0.0)), 1)),
                            boost=float(round(max(0.0, getattr(p, 'boost_cooldown', 0.0)), 1)),
                        ),
                        username=getattr(p, 'username', f'Player_{pid[:8]}'),
                        # Время окончания эффектов для анимаций (конвертируем в миллисекунды)
                        teleport_effect_time=p.teleport_effect_time * 1000 if p.teleport_effect_time else None,
                        shield_end_time=p.shield_end_time * 1000 if p.shield_end_time else None,
                        speed_boost_end_time=p.speed_boost_end_time * 1000 if p.speed_boost_end_time else None,
                    )
                }
                for pid, p in self.players.items()
            ],
            bonus_zones=[
                BonusZoneModel(
                    x=z.x,
                    y=z.y,
                    radius=z.radius,
                    multiplier=z.multiplier,
                    remaining_time=z.get_remaining_time(),
                    funds_collected=z.funds_collected,
                    max_funds=z.funds_generated * z.multiplier,
                )
                for z in self.bonus_zones
            ],
            safe_zone=SaveZone(
                x=safe_zone_bounds.x,
                y=safe_zone_bounds.y,
                radius=safe_zone_bounds.radius,
                scale=self.safe_zone_scale,
                damage_per_second=self.zone_damage_per_second,
                time_to_next_shrink=self.get_time_to_next_shrink(),
                game_time=self.get_game_time(),
            ),
        )

        # Добавляем информацию о выходах игроков
        if self.early_exits:
            state.early_exits = self.early_exits
        if self.super_exits:
            state.super_exits = self.super_exits
        if self.finalists:
            state.finalists = self.finalists

        return state


_active_games: dict[str, Game] = {}


async def create_game(g_id: str, expected_players: int = 10, fund: float = 100) -> Game:
    new_game = Game(expected_players, fund)

    _active_games.update({g_id: new_game})
    return new_game


async def get_game(g_id: str) -> Game:
    return _active_games[g_id]


async def set_changes(g_id: str, data: Game) -> None:
    _active_games[g_id] = data


async def close_game(g_id: str) -> None:
    try:
        _active_games.pop(g_id)
    except KeyError:
        pass


class BetaGame(Game):
    def __init__(self, expected_players: int, fund: float):
        super().__init__(expected_players=10, fund=fund)
        self.bot_players: dict[str, Player] = {}
        for i in range(1, 10):
            bot_id = f"bot_{i}"
            self.bot_players[bot_id] = Player(
                x=random.randint(0, self.radius),
                y=random.randint(0, self.radius),
                player_id=bot_id,
                radius=self.radius,
            )
            self.players.update(self.bot_players)

    def get_skill_cost_percentage(self, player_id: str, skill_type: str) -> float:
        return 0.0


_beta_active_games: dict[str, BetaGame] = {}


async def create_beta_game(
    g_id: str, expected_players: int = 10, fund: float = 10000
) -> BetaGame:
    new_game = BetaGame(expected_players, fund)
    _beta_active_games.update({g_id: new_game})
    return new_game


async def get_beta_game(g_id: str) -> BetaGame:
    return _beta_active_games[g_id]


async def set_beta_changes(g_id: str, data: BetaGame) -> None:
    _beta_active_games[g_id] = data


async def close_beta_game(g_id: str) -> None:
    try:
        _beta_active_games.pop(g_id)
    except KeyError:
        pass
