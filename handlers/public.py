from fastapi import APIRouter, HTTPException
from servises.player_counter import player_counter_service


router = APIRouter(
    prefix="/api",
    tags=["pub"]
)

@router.get("/health", description="Эндпоинт для проверки работы сервиса")
def health():
    return {"status": "all good"}


@router.get("/active-players", description="Получить количество активных игроков для отображения на сайте")
async def get_active_players():
    """
    Эндпоинт для получения количества активных игроков для отображения на сайте.
    Возвращает стабильное значение в районе 8-10 тысяч.
    """
    try:
        count = await player_counter_service.get_fake_count()
        return {
            "active_players": count,
            "timestamp": "display_value"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении количества активных игроков: {str(e)}")
    