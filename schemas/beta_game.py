from typing import (
    Any, 
    Dict, 
    Literal, 
    Optional,
)

from pydantic import BaseModel, Field


class CreateBetaGameRequest(BaseModel):
    player_id: str = Field(..., min_length=1, description="Идентификатор игрока")


class MoveRequest(BaseModel):
    game_id: str
    player_id: str
    dx: float = Field(..., ge=-10, le=10, description="Смещение по X")
    dy: float = Field(..., ge=-10, le=10, description="Смещение по Y")


class SkillRequest(BaseModel):
    game_id: str
    player_id: str
    skill_type: Literal["teleport", "shield", "boost"] = Field(..., description="Тип навыка")


class VoteRequest(BaseModel):
    game_id: str
    player_id: str
    vote: Literal["exit", "super"] = Field(..., description="Голос в топ-10")


class ExitRequest(BaseModel):
    game_id: str
    player_id: str
    exit_type: Literal["early", "super"] = Field(..., description="Тип выхода из игры")


class BetaGameResponse(BaseModel):
    success: bool
    game_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
