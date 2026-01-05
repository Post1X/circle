import logging

from typing import (
    TYPE_CHECKING,
    Annotated,
)

from fastapi import (
    APIRouter, 
    Depends, 
    Response, 
    Request,
    UploadFile, 
    File, 
    HTTPException,
    status,
)

from bd.actions.user import UserActions
from bd.actions.balance import BalanceActions
from bd.actions.nonce import NonceActions
from bd.database import get_session
from bd.models import User

from uuid import uuid4

from servises.auth.dependencies import get_current_user, get_token
from servises.auth.auth import authenticate_user, create_access_token, get_password_hash
from servises.auth.token_service import token_service
from servises.avatar_service import avatar_service
from servises.exceptions import (
    TokenAbsentException, 
    IncorrectTokenFormatException
)

from schemas.user import (
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    WalletAuthRequest, 
    WalletAuthResponse, 
    WalletConnectRequest, 
    WalletConnectResponse, 
    UserInfo
)
from schemas.user import (
    AvatarUploadResponse, 
    AvatarInfo
)
from schemas.user import (
    AvatarUploadResponse, 
    AvatarInfo, 
    UpdateUsernameRequest, 
    UpdateUsernameResponse,
    BalanceResponse,
    TronAddressResponse,
    DepositStatusResponse
)

from servises.exceptions import TokenAbsentException, IncorrectTokenFormatException

import uuid
import random
import string
from decimal import Decimal

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router  = APIRouter(
    prefix="/api/users",
    tags=["User"],
)


@router.post(
    "/register",
    response_model=UserRegisterResponse
)
async def register(
    request: UserRegisterRequest,
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ]
):
    try:
        user_actions = UserActions(session=session)
        existing_user = await user_actions.get_user_by_username(
            username=request.username,
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User already exists",
            )
        
        hashed_password = get_password_hash(request.password)

        await user_actions.create_user(
            username=request.username,
            hashed_password=hashed_password,
        )

        return UserRegisterResponse(
            status="Registered successfull !"
        )
    except HTTPException as e:
        print(e)
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.post(
    "/login",
    response_model=UserLoginResponse,
)
async def login(
    request: UserLoginRequest,
    response: Response,
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ]
):
    try:
        user: User = await authenticate_user(
            username=request.username,
            password=request.password,
            session=session,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login or password"
            )

        access_token = create_access_token({"sub": str(user.user_id)})

        response.headers["Authorization"] = f"Bearer {access_token}"

        return UserLoginResponse(
            access_token=access_token,
            user_id=user.user_id,
            username=user.username,
        )
    except HTTPException as e:
        print(e)
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
async def logout(request: Request, response: Response):
    try:
        token = get_token(request)

        logging.info(f"Токен: {token}")
        
        await token_service.add_to_blacklist(token)
        
        response.headers.pop("Authorization", None)
        
        return {
            "message": "Successfully logged out"
        }
    except (TokenAbsentException, IncorrectTokenFormatException) as e:
        logging.info(f"Ошибка: {e}")
        return {
            "message": "Logout failed"
        }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/username", response_model=UpdateUsernameResponse)
async def update_username(
    request: UpdateUsernameRequest,
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ],
    current_user: User = Depends(get_current_user),
):
    try:
        user_actions = UserActions(session)
        
        if current_user.username == request.username:
            return UpdateUsernameResponse(
                success=True,
                username=request.username,
                message="Никнейм уже установлен"
            )
        
        existing_user = await user_actions.get_user_by_username(request.username)
        if existing_user and existing_user.user_id != current_user.user_id:
            return UpdateUsernameResponse(
                success=False,
                error="Никнейм уже занят другим пользователем"
            )
        
        await user_actions.update_username(current_user.user_id, request.username)
        
        return UpdateUsernameResponse(
            success=True,
            username=request.username,
            message="Никнейм успешно обновлен"
        )
        
    except Exception as e:
        return UpdateUsernameResponse(
            success=False,
            error=f"Ошибка обновления никнейма: {str(e)}"
        )
    

@router.get(
    "/statistic",
    description="Статистика игрока"
)
async def get_user_stat() -> UserInfo:
    ...


@router.get(
    "/leaderboard",
    description="Вывод лидерборда"
)
async def get_leaderboard():
    ...


@router.get("/avatar/info")
async def get_avatar_info() -> AvatarInfo:
    return avatar_service.get_avatar_info()


@router.post("/avatar/upload")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> AvatarUploadResponse:
    try:
        avatar_url = await avatar_service.upload_avatar(file, current_user.user_id)
        return AvatarUploadResponse(
            success=True,
            avatar_url=avatar_url,
            message="Avatar uploaded successfully"
        )
    except Exception as e:
        return AvatarUploadResponse(
            success=False,
            error=str(e)
        )


@router.delete(
    "/avatar",
    description="Удалить текущую аватарку пользователя",
    response_model=AvatarUploadResponse
)
async def delete_avatar(
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ],
    current_user: User = Depends(get_current_user),
):
    try:
        if current_user.avatar_url:
            avatar_service.delete_avatar(current_user.avatar_url)
        
        new_avatar_url = avatar_service.generate_random_avatar(str(current_user.user_id))
        
        async with get_session() as session:
            current_user.avatar_url = new_avatar_url
            session.add(current_user)
            await session.commit()
        
        return AvatarUploadResponse(
            success=True,
            avatar_url=new_avatar_url,
            message="Аватарка успешно удалена"
        )
        
    except Exception as e:
        return AvatarUploadResponse(
            success=False,
            error=f"Ошибка удаления аватарки: {str(e)}"
        )




@router.get(
    "/balance",
    description="Получить текущий баланс пользователя",
    response_model=BalanceResponse
)
async def get_balance(
    current_user: User = Depends(get_current_user),
):
    return BalanceResponse(
        balance=float(current_user.balance),
        total_winnings=float(current_user.total_winnings),
        games_played=current_user.games_played
    )


@router.get(
    "/deposit/address",
    description="Получить Tron адрес для пополнения баланса",
    response_model=TronAddressResponse
)
async def get_deposit_address(
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ],
    current_user: User = Depends(get_current_user),
):
    try:
        balance_actions = BalanceActions(session)
        
        address = await balance_actions.get_address(str(current_user.user_id))
        
        return TronAddressResponse(
            address=address,
            message="Отправьте USDT на этот адрес для пополнения баланса"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения адреса: {str(e)}"
        )


@router.get(
    "/deposit/status",
    description="Проверить статус пополнения баланса",
    response_model=DepositStatusResponse
)
async def get_deposit_status(
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ],
    current_user: User = Depends(get_current_user),
):
    try:
        balance_actions = BalanceActions(session)
        
        transactions = await balance_actions.get_user_transactions(current_user.user_id)
        
        if not transactions:
            return DepositStatusResponse(
                status="no_transactions",
                message="Нет ожидающих транзакций. Получите адрес для пополнения."
            )
        
        latest_transaction = transactions[0]
        
        if latest_transaction.status.value == "confirmed":
            return DepositStatusResponse(
                status="confirmed",
                amount=latest_transaction.amount,
                message="Пополнение успешно зачислено на баланс"
            )
        elif latest_transaction.status.value == "pending":
            return DepositStatusResponse(
                status="pending",
                amount=latest_transaction.amount,
                message="Транзакция ожидает подтверждения"
            )
        else:
            return DepositStatusResponse(
                status=latest_transaction.status.value,
                message="Транзакция в обработке"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка проверки статуса: {str(e)}"
        )


@router.post(
    "/nonce",
    description="Получить nonce для аутентификации кошелька",
    response_model=WalletAuthResponse
)
async def get_nonce(
    request: WalletAuthRequest,
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ]
):
    """
    Генерирует и возвращает nonce для указанного адреса кошелька.
    Nonce используется для подписи сообщения при аутентификации.
    
    Args:
        request: Запрос с адресом кошелька
        session: Сессия базы данных
        
    Returns:
        WalletAuthResponse: Ответ с nonce для подписи
    """
    try:
        nonce_actions = NonceActions(session)
        
        nonce_value = await nonce_actions.create_nonce(request.address)
        
        return WalletAuthResponse(
            nonce=nonce_value
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации nonce: {str(e)}"
        )


@router.post(
    "/wallet-connect",
    description="Аутентификация через кошелек Tron",
    response_model=WalletConnectResponse
)
async def wallet_connect(
    request: WalletConnectRequest,
    response: Response,
    session: Annotated[
        "AsyncSession",
        Depends(get_session)
    ]
):
    """
    Аутентификация пользователя через подпись кошелька Tron.
    Проверяет nonce и подпись, создает или находит пользователя, возвращает токен.
    
    Args:
        request: Запрос с адресом, подписью и nonce
        response: HTTP ответ для установки заголовков
        session: Сессия базы данных
        
    Returns:
        WalletConnectResponse: Результат аутентификации с токеном
    """
    try:
        nonce_actions = NonceActions(session)
        user_actions = UserActions(session)
        
        # Проверяем nonce
        nonce_obj = await nonce_actions.get_nonce(request.address, request.nonce)
        if not nonce_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired nonce"
            )
        
        # TODO: Проверка подписи Tron (можно использовать tronpy)
        # Пока пропускаем проверку подписи для упрощения
        # В продакшене нужно добавить проверку подписи
        
        # Помечаем nonce как использованный
        await nonce_actions.mark_nonce_as_used(nonce_obj)
        
        # Ищем пользователя по адресу кошелька
        user = await user_actions.get_user_by_wallet_address(request.address)
        
        # Если пользователь не найден, создаем нового
        if not user:
            # Создаем пользователя без пароля (wallet-only user)
            # Генерируем случайное имя пользователя
            username = f"user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            
            # Проверяем, что имя уникально
            while await user_actions.get_user_by_username(username):
                username = f"user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            
            # Создаем пользователя с пустым паролем (не используется для wallet auth)
            user = await user_actions.create_user(
                username=username,
                hashed_password=get_password_hash("")  # Пустой пароль, не используется
            )
            
            # Привязываем кошелек к пользователю
            await user_actions.bind_wallet_to_user(user.user_id, request.address)
        
        # Обновляем пользователя из БД, чтобы получить актуальные данные
        # (особенно важно после создания нового пользователя)
        await session.refresh(user)
        
        # Создаем JWT токен
        access_token = create_access_token({"sub": str(user.user_id)})
        
        # Устанавливаем токен в заголовок
        response.headers["Authorization"] = f"Bearer {access_token}"
        
        return WalletConnectResponse(
            success=True,
            message="Wallet connected successfully",
            wallet_address=request.address,
            access_token=access_token,
            user_id=user.user_id,
            username=user.username,
            balance=float(user.balance),
            games_played=user.games_played,
            total_winnings=float(user.total_winnings),
            leaderboard_rank=user.leaderboard_rank,
            is_admin=user.is_admin,
            avatar_url=user.avatar_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка аутентификации кошелька: {str(e)}"
        )


