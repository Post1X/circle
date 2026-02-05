from pydantic import BaseModel
from typing import Optional, List, Dict, Tuple
from enum import StrEnum


class GamePhases(StrEnum):
    START = "start"
    TOP_10 = "top10"
    SUPER = "super"
    FINISHED = "finished"


class Zone(BaseModel):
    x: int
    y: int
    radius: int


class SaveZone(Zone):
    scale: float
    damage_per_second: float
    time_to_next_shrink: float
    game_time: float


class BonusZoneModel(Zone):
    multiplier: int
    remaining_time: float
    funds_collected: float
    max_funds: int


class Phase(BaseModel):
    phase: GamePhases
    super_game_time_remaining: Optional[float] = None
    skill_costs_increased: Optional[bool] = None
    voting_time_remaining: Optional[float] = None
    votes_submitted: Optional[int] = None
    votes_exit: Optional[int] = None
    votes_super: Optional[int] = None


class Cooldowns(BaseModel):
    teleport: float
    shield: float
    boost: float


class PlayerData(BaseModel):
    x: float
    y: float
    mass: float
    money: float
    color: Tuple[int, int, int]
    shield_active: bool
    speed_boost_active: bool
    skills_used: int
    outside_zone: bool
    zone_damage_taken: int
    in_bonus_zone: bool
    bonus_multiplier: float
    bonus_zone_collected: int
    cooldowns: Cooldowns
    username: str
    # Время окончания эффектов для анимаций
    teleport_effect_time: Optional[float] = None
    shield_end_time: Optional[float] = None
    speed_boost_end_time: Optional[float] = None


class MapInfo(BaseModel):
    radius: int
    player_count: int
    exepcted_players: int


class FoodModel(BaseModel):
    id: str
    x: int
    y: int
    mass: float
    color: Tuple[int, int, int]


class GameState(BaseModel):
    map_info: MapInfo
    safe_zone: SaveZone
    bonus_zones: List[Optional[BonusZoneModel]] = []
    zone_fund: int
    bonus_fund: float
    time_to_next_bonus_zone: float
    game_phase: Phase
    players: List[Dict[str, PlayerData]]
    foods: List[FoodModel]
    early_exits: Optional[Dict[str, float]] = None
    super_exits: Optional[Dict[str, float]] = None
    finalists: Optional[List[str]] = None
