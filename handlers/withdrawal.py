import logging

from typing import (
    TYPE_CHECKING, 
    Annotated,
)

from decimal import Decimal

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status,
    Query,
)

from sqlalchemy.ext.asyncio import AsyncSession

from bd.actions.withdrawal import (
    WithdrawalActions, 
    HotWalletActions,
)
from bd.actions.balance import BalanceActions
from bd.database import get_session
from bd.models import (
    User, 
)

from servises.auth.dependencies import get_current_user

from schemas.withdrawal import (
    WithdrawalCreateRequest,
    WithdrawalResponse,
    WithdrawalStatusResponse,
    WithdrawalHistoryResponse,
    WithdrawalCreateResponse,
    HotWalletResponse,
    WithdrawalStatsResponse
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(
    prefix="/api/withdrawals",
    tags=["Withdrawals"],
)


@router.post(
    "/request",
    response_model=WithdrawalCreateResponse,
    description="Создать запрос на вывод средств"
)
async def create_withdrawal_request(
    request: WithdrawalCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: User = Depends(get_current_user)
):
    try:
        withdrawal_actions = WithdrawalActions(session)
        balance_actions = BalanceActions(session)
        
        total_amount = request.amount + request.fee
        
        if current_user.balance < total_amount:
            return WithdrawalCreateResponse(
                success=False,
                error="Недостаточно средств на балансе"
            )
        
        if request.amount < Decimal("1.0"):
            return WithdrawalCreateResponse(
                success=False,
                error="Минимальная сумма для вывода: 1 USDT"
            )
        
        if request.amount > Decimal("10000.0"):
            return WithdrawalCreateResponse(
                success=False,
                error="Максимальная сумма для вывода: 10000 USDT"
            )
        
        withdrawal = await withdrawal_actions.create_withdrawal_request(
            user_id=current_user.user_id,
            amount=request.amount,
            to_address=request.to_address,
            fee=request.fee
        )
        
        return WithdrawalCreateResponse(
            success=True,
            withdrawal_id=withdrawal.id,
            message="Запрос на вывод создан успешно"
        )
        
    except Exception as e:
        logging.error(f"Error creating withdrawal request: {e}")
        return WithdrawalCreateResponse(
            success=False,
            error="Ошибка создания запроса на вывод"
        )


@router.get(
    "/status/{withdrawal_id}",
    response_model=WithdrawalStatusResponse,
    description="Получить статус запроса на вывод"
)
async def get_withdrawal_status(
    withdrawal_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: User = Depends(get_current_user)
):
    try:
        withdrawal_actions = WithdrawalActions(session)
        
        withdrawal = await withdrawal_actions.get_withdrawal_by_id(withdrawal_id)
        
        if not withdrawal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запрос на вывод не найден"
            )
        
        if withdrawal.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
        
        return WithdrawalStatusResponse(
            id=withdrawal.id,
            status=withdrawal.status,
            amount=withdrawal.amount,
            to_address=withdrawal.to_address,
            transaction_hash=withdrawal.transaction_hash,
            error_message=withdrawal.error_message,
            created_at=withdrawal.created_at,
            processed_at=withdrawal.processed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting withdrawal status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статуса вывода"
        )


@router.get(
    "/history",
    response_model=WithdrawalHistoryResponse,
    description="Получить историю выводов пользователя"
)
async def get_withdrawal_history(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на странице")
):
    try:
        withdrawal_actions = WithdrawalActions(session)
        
        offset = (page - 1) * per_page
        
        withdrawals = await withdrawal_actions.get_user_withdrawals(
            user_id=current_user.user_id,
            limit=per_page,
            offset=offset
        )
        
        total_count = await withdrawal_actions.get_user_withdrawal_count(current_user.user_id)
        
        withdrawal_responses = [
            WithdrawalResponse(
                id=w.id,
                amount=w.amount,
                to_address=w.to_address,
                fee=w.fee,
                status=w.status,
                created_at=w.created_at,
                transaction_hash=w.transaction_hash,
                error_message=w.error_message
            )
            for w in withdrawals
        ]
        
        return WithdrawalHistoryResponse(
            withdrawals=withdrawal_responses,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logging.error(f"Error getting withdrawal history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения истории выводов"
        )


@router.get(
    "/hot-wallet",
    response_model=HotWalletResponse,
    description="Получить информацию о горячем кошельке"
)
async def get_hot_wallet_info(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: User = Depends(get_current_user)
):
    try:
        hot_wallet_actions = HotWalletActions(session)
        
        hot_wallet = await hot_wallet_actions.get_active_hot_wallet()
        
        if not hot_wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Горячий кошелек не найден"
            )
        
        return HotWalletResponse(
            address=hot_wallet.address,
            balance=hot_wallet.balance,
            is_active=hot_wallet.is_active,
            last_updated=hot_wallet.last_updated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting hot wallet info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения информации о кошельке"
        )


@router.get(
    "/stats",
    response_model=WithdrawalStatsResponse,
    description="Получить статистику выводов"
)
async def get_withdrawal_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: User = Depends(get_current_user)
):
    try:
        withdrawal_actions = WithdrawalActions(session)
        hot_wallet_actions = HotWalletActions(session)
        
        stats = await withdrawal_actions.get_withdrawal_stats()
        
        hot_wallet = await hot_wallet_actions.get_active_hot_wallet()
        hot_wallet_balance = hot_wallet.balance if hot_wallet else Decimal("0")
        
        return WithdrawalStatsResponse(
            total_withdrawals=stats["total_withdrawals"],
            total_amount=stats["total_amount"],
            pending_withdrawals=stats["pending_withdrawals"],
            failed_withdrawals=stats["failed_withdrawals"],
            hot_wallet_balance=hot_wallet_balance
        )
        
    except Exception as e:
        logging.error(f"Error getting withdrawal stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики"
        )


@router.post(
    "/cancel/{withdrawal_id}",
    description="Отменить запрос на вывод"
)
async def cancel_withdrawal(
    withdrawal_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: User = Depends(get_current_user)
):
    try:
        withdrawal_actions = WithdrawalActions(session)
        balance_actions = BalanceActions(session)
        
        withdrawal = await withdrawal_actions.get_withdrawal_by_id(withdrawal_id)
        
        if not withdrawal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запрос на вывод не найден"
            )
        
        if withdrawal.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
        
        if withdrawal.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Можно отменить только ожидающие запросы"
            )
        
        await withdrawal_actions.update_withdrawal_status(
            withdrawal_id,
            "cancelled"
        )
        
        await balance_actions.credit_winnings(
            current_user.user_id,
            withdrawal.amount + withdrawal.fee
        )
        
        return {"success": True, "message": "Запрос на вывод отменен"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error canceling withdrawal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отмены вывода"
        )
