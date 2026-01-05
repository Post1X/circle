from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from bd.database import get_session
from bd.actions.user import UserActions
from bd.models import User
from uuid import UUID

router = APIRouter(
    prefix="/api/skills",
    tags=["Skills"],
)


@router.get("/info")
async def get_skills_info():
    """Get information about available skills"""
    return {
        "skills": [
            {
                "type": "teleport",
                "name": "Рандомный телепорт",
                "description": "Мгновенный телепорт в 100% безопасное место",
                "cost_percentage": 15,
                "cooldown": 60,
                "duration": 0
            },
            {
                "type": "shield", 
                "name": "Защитный щит",
                "description": "3 секунды неуязвимости",
                "cost_percentage": 10,
                "cooldown": 30,
                "duration": 3
            },
            {
                "type": "boost",
                "name": "Ускорение",
                "description": "5 секунд повышенной скорости",
                "cost_percentage": 5,
                "cooldown": 15,
                "duration": 5
            }
        ],
        "rules": {
            "max_activations_per_game": 5,
            "minimum_balance": 1.0,
            "cost_taken_from_game_balance": True
        }
    }


@router.get("/cost/{skill_type}")
async def get_skill_cost(
    skill_type: str, 
    user_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Calculate skill cost for specific user"""
    if skill_type not in ["teleport", "shield", "boost"]:
        raise HTTPException(status_code=400, detail="Invalid skill type")
        
    user_actions = UserActions(session)
    user = await user_actions.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    balance = float(user.balance)
    
    cost_percentages = {
        "teleport": 0.15,
        "shield": 0.10,
        "boost": 0.05
    }
    
    cost = balance * cost_percentages[skill_type]
    
    return {
        "skill_type": skill_type,
        "current_balance": balance,
        "cost_percentage": cost_percentages[skill_type] * 100,
        "cost_amount": cost,
        "can_afford": balance >= 1.0
    }