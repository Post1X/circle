from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
)


class WithdrawalCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма для вывода")
    to_address: str = Field(
        ..., min_length=34, max_length=34, description="Tron адрес получателя"
    )
    fee: Decimal = Field(default=Decimal("2.5"), ge=0, description="Комиссия за вывод")


class WithdrawalResponse(BaseModel):
    id: int
    amount: Decimal
    to_address: str
    fee: Decimal
    status: str
    created_at: datetime
    transaction_hash: Optional[str] = None
    error_message: Optional[str] = None


class WithdrawalStatusResponse(BaseModel):
    id: int
    status: str
    amount: Decimal
    to_address: str
    transaction_hash: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class WithdrawalHistoryResponse(BaseModel):
    withdrawals: list[WithdrawalResponse]
    total_count: int
    page: int
    per_page: int


class WithdrawalCreateResponse(BaseModel):
    success: bool
    withdrawal_id: int
    message: str
    error: Optional[str] = None


class HotWalletResponse(BaseModel):
    address: str
    balance: Decimal
    is_active: bool
    last_updated: datetime


class WithdrawalStatsResponse(BaseModel):
    total_withdrawals: int
    total_amount: Decimal
    pending_withdrawals: int
    failed_withdrawals: int
    hot_wallet_balance: Decimal
