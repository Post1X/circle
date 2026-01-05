from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime

from fastapi import Depends, Request, HTTPException
from jose import JWTError, jwt 

from servises.config import config

from bd.actions.user import UserActions

from bd.database import get_session

from servises.exceptions import  (
    TokenAbsentException,
    IncorrectTokenFormatException,
    TokenExpiredException,
    UserIsNotPresentException,
)

from servises.auth.token_service import token_service


def get_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise TokenAbsentException
    
    if not auth_header.startswith("Bearer "):
        raise IncorrectTokenFormatException
    
    token = auth_header.split(" ")[1]
    if not token:
        raise TokenAbsentException
    
    return token


async def get_current_user(
        token: str = Depends(get_token),
        session: AsyncSession = Depends(get_session)
):
    actions = UserActions(session)

    try:
        payload = jwt.decode(
            token, config.SECRET_KEY, config.ALGORITHM
        )
    except JWTError:
        raise IncorrectTokenFormatException
    
    expire: str = payload.get("exp")
    if (not expire) or (int(expire) < int(datetime.utcnow().timestamp())):
        raise TokenExpiredException
    
    if await token_service.is_blacklisted(token):
        raise IncorrectTokenFormatException
    
    user_id: str = payload.get("sub")
    if not user_id:
        raise UserIsNotPresentException
    
    user = await actions.get_user_by_id(
        user_id=user_id,
    )
    if not user:
        raise UserIsNotPresentException
    
    return user


async def get_current_admin_user(
        current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Требуются права администратора."
        )
    return current_user
