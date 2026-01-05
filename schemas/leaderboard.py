from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CurrentPlayer(BaseModel):
    player_id: str = Field(..., description="Уникальный идентификатор игрока")
    mass: float = Field(..., description="Масса игрока в пикселях")
    x: float = Field(..., description="X координата")
    y: float = Field(..., description="Y координата")
    r: int = Field(..., description="Красный компонент цвета (0-255)")
    g: int = Field(..., description="Зеленый компонент цвета (0-255)")
    b: int = Field(..., description="Синий компонент цвета (0-255)")
    skills_used: int = Field(..., description="Количество использованных навыков")
    bonus_zone_collected: float = Field(..., description="Собранные бонусы из зон")
    outside_zone_damage: float = Field(..., description="Урон от нахождения вне безопасной зоны")
    in_bonus_zone: bool = Field(..., description="Находится ли в бонусной зоне")
    bonus_multiplier: float = Field(..., description="Текущий множитель бонусной зоны")
    rank: int = Field(..., description="Ранг игрока в лидерборде")
    username: str = Field(..., description="Username игрока")


class GamePhaseInfo(BaseModel):
    phase: str = Field(..., description="Текущая фаза игры")
    players_count: int = Field(..., description="Количество игроков")
    bonus_fund: float = Field(..., description="Бонусный фонд")
    zone_fund: float = Field(..., description="Зональный фонд")
    voting_time_remaining: Optional[float] = Field(None, description="Время голосования для фазы top10")
    votes_submitted: Optional[int] = Field(None, description="Количество поданных голосов")
    votes_exit: Optional[int] = Field(None, description="Голоса за выход")
    votes_super: Optional[int] = Field(None, description="Голоса за супер игру")
    super_game_time_remaining: Optional[float] = Field(None, description="Время супер игры")
    skill_costs_increased: Optional[bool] = Field(None, description="Увеличены ли стоимости навыков")


class EarlyExit(BaseModel):
    player_id: str = Field(..., description="Идентификатор игрока")
    winnings: float = Field(..., description="Выигрыш в USDT")
    exit_type: str = Field(..., description="Тип выхода (early)")
    percentage: int = Field(..., description="Процент от выигрыша")


class SuperExit(BaseModel):
    player_id: str = Field(..., description="Идентификатор игрока")
    winnings: float = Field(..., description="Выигрыш в USDT")
    exit_type: str = Field(..., description="Тип выхода (super)")
    percentage: int = Field(..., description="Процент от выигрыша")


class Finalist(BaseModel):
    player_id: str = Field(..., description="Идентификатор игрока")
    final_winnings: float = Field(..., description="Финальный выигрыш в USDT")
    final_mass: float = Field(..., description="Финальная масса в пикселях")


class LeaderboardData(BaseModel):
    current_players: List[CurrentPlayer] = Field(..., description="Список текущих игроков")
    total_players: int = Field(..., description="Общее количество игроков")
    game_phase: GamePhaseInfo = Field(..., description="Информация о фазе игры")
    game_time: float = Field(..., description="Время игры в секундах")
    safe_zone_scale: float = Field(..., description="Масштаб безопасной зоны")
    zone_fund: float = Field(..., description="Фонд зоны")
    bonus_fund: float = Field(..., description="Бонусный фонд")
    early_exits: Optional[List[EarlyExit]] = None
    super_exits: Optional[List[SuperExit]] = None
    finalists: Optional[List[Finalist]] = None


class LeaderboardResponse(BaseModel):
    success: bool = Field(..., description="Успешность запроса")
    leaderboard: LeaderboardData = Field(..., description="Данные лидерборда")
    error: Optional[str] = None
    message: Optional[str] = None


class LeaderboardErrorResponse(BaseModel):
    success: bool = False
    error: str = Field(..., description="Описание ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
