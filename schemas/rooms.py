from pydantic import BaseModel, Field


class AuthenticateRequest(BaseModel):
    user_id: str = Field(..., description="UUID пользователя")


class CreateRoomRequest(BaseModel):
    entry_fee: int = Field(default=0, ge=0, description="Вступительный взнос")
    min_players: int = Field(
        default=2, ge=1, le=100, description="Минимальное количество игроков"
    )
    max_players: int = Field(
        default=100, ge=1, le=1000, description="Максимальное количество игроков"
    )


class JoinRoomRequest(BaseModel):
    room_id: str = Field(..., description="UUID комнаты для присоединения")


class LeaveRoomRequest(BaseModel):
    room_id: str = Field(..., description="UUID комнаты для выхода")


class VoteRequest(BaseModel):
    vote: str = Field(..., description="Голос: 'exit' или 'super'")


class ExitGameRequest(BaseModel):
    exit_type: str = Field(..., description="Тип выхода: 'early' или 'super'")


class ActivateSkillRequest(BaseModel):
    skill_type: str = Field(
        ..., description="Тип навыка: 'teleport', 'shield', 'boost'"
    )


class GamePhaseInfo(BaseModel):
    phase: str = Field(..., description="Текущая фаза игры")
    players_count: int = Field(..., description="Количество игроков")
    bonus_fund: float = Field(..., description="Бонусный фонд")
    zone_fund: float = Field(..., description="Зональный фонд")
    voting_time_remaining: float = Field(0, description="Время до конца голосования")
    votes_submitted: int = Field(0, description="Количество поданных голосов")
    votes_exit: int = Field(0, description="Голоса за выход")
    votes_super: int = Field(0, description="Голоса за супер игру")
    super_game_time_remaining: float = Field(0, description="Время до конца супер игры")
    skill_costs_increased: bool = Field(
        False, description="Увеличена ли стоимость навыков"
    )


class GameResults(BaseModel):
    early_exits: dict = Field(..., description="Ранние выходы игроков")
    super_exits: dict = Field(..., description="Выходы из супер игры")
    finalists: list = Field(..., description="Список финалистов")
    bonus_fund: float = Field(..., description="Бонусный фонд")
    zone_fund: float = Field(..., description="Зональный фонд")
    final_winnings: dict = Field(..., description="Финальные выигрыши")
