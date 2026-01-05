from .admin import router as admin_router
from .rooms import sio
from .public import router as pub_router
from .game import router as game_router
from .skills import router as skills_router
from .user import router as user_router
from .beta_game import router as beta_game_router
from .withdrawal import router as withdrawal_router

__all__ = [
    "admin_router",
    "pub_router",
    "game_router",
    "skills_router",
    "user_router",
    "beta_game_router",
    "withdrawal_router",
    "sio"
]