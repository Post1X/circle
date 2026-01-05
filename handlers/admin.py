from fastapi import APIRouter, Depends, HTTPException
from servises.player_counter import player_counter_service
from servises.auth.dependencies import get_current_admin_user
from bd.models import User


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/active-players/real", description="Получить реальное количество активных игроков (только для админов)")
async def get_real_active_players(current_user: User = Depends(get_current_admin_user)):
    """
    Эндпоинт для получения реального количества активных игроков.
    Доступен только администраторам.
    """
    try:
        count = await player_counter_service.get_real_count()
        return {
            "active_players": count,
            "timestamp": "real_time"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении количества активных игроков: {str(e)}")
