from datetime import (
    datetime, 
    timedelta
)

from bd.models import User
from bd.actions.user import UserActions

from typing import (
    TYPE_CHECKING,
    Optional,
    Union,
)

from jose import jwt
from passlib.context import CryptContext

from servises.config import config


pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto"
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=365)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.SECRET_KEY, config.ALGORITHM
    )
    
    return encoded_jwt


async def authenticate_user(
        username: str, 
        password: str,
        session: "AsyncSession"
) -> Union[User, None]:
    user_actions = UserActions(session=session)

    user: Optional[User] = await user_actions.get_user_by_username(
        username=username,
    )

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
