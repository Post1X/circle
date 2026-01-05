from pydantic import BaseModel, Field

import uuid


class UserRegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Имя пользователя",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=35,
        description="Пароль",
    )


class UserRegisterResponse(BaseModel):
    status: str = "registered successfull !"


class UserLoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Имя пользователя",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=35,
        description="Пароль",
    )


class UserLoginResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT токен для авторизации"
    )
    # user_id: uuid4 = Field(
    #     ...,
    #     description="ID пользователя"
    # )
    user_id: uuid.UUID = Field(
        default_factory=uuid.uuid4
    )
    username: str = Field(
        ...,
        description="Имя пользователя"
    )


class WalletAuthRequest(BaseModel):
    address: str = Field(
        ...,
        min_length=34,
        max_length=34,
        description="Адрес кошелька Tron (Base58)"
    )


class WalletAuthResponse(BaseModel):
    nonce: str = Field(
        ...,
        description="Nonce для подписи"
    )


class WalletConnectRequest(BaseModel):
    address: str = Field(
        ...,
        min_length=34,
        max_length=34,
        description="Адрес кошелька Tron (Base58)"
    )
    signature: str = Field(
        ...,
        description="Подпись от кошелька"
    )
    nonce: str = Field(
        ...,
        description="Nonce для проверки"
    )


class WalletConnectResponse(BaseModel):
    success: bool = Field(
        ...,
        description="Успешность привязки кошелька"
    )
    message: str = Field(
        ...,
        description="Сообщение о результате"
    )
    wallet_address: str = Field(
        ...,
        description="Адрес привязанного кошелька"
    )
    access_token: str = Field(
        ...,
        description="JWT токен для авторизации"
    )
    user_id: uuid.UUID = Field(
        ...,
        description="ID пользователя"
    )
    username: str = Field(
        ...,
        description="Имя пользователя"
    )
    balance: float = Field(
        ...,
        description="Текущий баланс пользователя"
    )
    games_played: int = Field(
        ...,
        description="Количество сыгранных игр"
    )
    total_winnings: float = Field(
        ...,
        description="Общий выигрыш"
    )
    leaderboard_rank: int = Field(
        ...,
        description="Ранг в лидерборде"
    )
    is_admin: bool = Field(
        ...,
        description="Является ли пользователь администратором"
    )
    avatar_url: str | None = Field(
        None,
        description="URL аватара пользователя"
    )


class UserInfo(BaseModel):
    games_played: int
    total_winnings: int
    leaderboard_rank: int


class UpdateUsernameRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Новый никнейм пользователя"
    )


class UpdateUsernameResponse(BaseModel):
    success: bool
    username: str | None = None
    message: str | None = None
    error: str | None = None


class UserResponse(BaseModel):
    user_id: str
    wallet_address: str
    username: str
    balance: float
    games_played: int
    total_winnings: int
    leaderboard_rank: int
    is_admin: bool
    avatar_url: str | None = None


class AvatarUploadResponse(BaseModel):
    success: bool
    avatar_url: str | None = None
    message: str | None = None
    error: str | None = None


class AvatarInfo(BaseModel):
    avatar_url: str
    avatar_size: int
    supported_formats: list[str]
    max_file_size: int




class BalanceResponse(BaseModel):
    balance: float
    total_winnings: float
    games_played: int


class TronAddressResponse(BaseModel):
    address: str
    network: str = "tron"
    message: str


class DepositStatusResponse(BaseModel):
    status: str
    amount: float | None = None
    transaction_hash: str | None = None
    confirmations: int | None = None
    message: str


