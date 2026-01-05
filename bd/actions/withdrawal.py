from typing import Optional, List

from uuid import UUID

from decimal import Decimal
from datetime import datetime

from sqlalchemy import select, update, func

from bd.actions.base import Actions
from bd.models import (
    WithdrawalRequest, 
    HotWallet, 
    ColdWallet
)


class WithdrawalActions(Actions):
    async def create_withdrawal_request(
        self, 
        user_id: UUID, 
        amount: Decimal, 
        to_address: str, 
        fee: Decimal = Decimal("0")
    ) -> WithdrawalRequest:
        withdrawal = WithdrawalRequest(
            user_id=user_id,
            amount=amount,
            to_address=to_address,
            fee=fee,
            status="pending"
        )
        
        await self.add(withdrawal)
        await self.commit()
        await self.session.refresh(withdrawal)
        
        return withdrawal

    async def get_withdrawal_by_id(self, withdrawal_id: int) -> Optional[WithdrawalRequest]:
        query = select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id)
        return await self.get_model(query)

    async def get_user_withdrawals(
        self, 
        user_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[WithdrawalRequest]:
        query = (
            select(WithdrawalRequest)
            .where(WithdrawalRequest.user_id == user_id)
            .order_by(WithdrawalRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return await self.get_models(query)

    async def get_pending_withdrawals(self) -> List[WithdrawalRequest]:
        query = select(WithdrawalRequest).where(
            WithdrawalRequest.status == "pending"
        )
        return await self.get_models(query)

    async def get_processing_withdrawals(self) -> List[WithdrawalRequest]:
        query = select(WithdrawalRequest).where(
            WithdrawalRequest.status == "processing"
        )
        return await self.get_models(query)

    async def update_withdrawal_status(
        self, 
        withdrawal_id: int, 
        status: str,
        transaction_hash: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        update_data = {
            "status": status,
            "processed_at": datetime.now() if status in ["completed", "failed"] else None
        }
        
        if transaction_hash:
            update_data["transaction_hash"] = transaction_hash
        if error_message:
            update_data["error_message"] = error_message
            
        query = (
            update(WithdrawalRequest)
            .where(WithdrawalRequest.id == withdrawal_id)
            .values(**update_data)
        )
        
        result = await self.session.execute(query)
        await self.commit()
        
        return result.rowcount > 0

    async def get_withdrawal_stats(self) -> dict:
        total_withdrawals_query = select(func.count()).select_from(WithdrawalRequest)
        total_amount_query = select(func.sum(WithdrawalRequest.amount)).where(
            WithdrawalRequest.status == "completed"
        )
        pending_query = select(func.count()).select_from(WithdrawalRequest).where(
            WithdrawalRequest.status == "pending"
        )
        failed_query = select(func.count()).select_from(WithdrawalRequest).where(
            WithdrawalRequest.status == "failed"
        )
        
        total_withdrawals = await self.session.scalar(total_withdrawals_query) or 0
        total_amount = await self.session.scalar(total_amount_query) or Decimal("0")
        pending_count = await self.session.scalar(pending_query) or 0
        failed_count = await self.session.scalar(failed_query) or 0
        
        return {
            "total_withdrawals": total_withdrawals,
            "total_amount": total_amount,
            "pending_withdrawals": pending_count,
            "failed_withdrawals": failed_count
        }

    async def get_user_withdrawal_count(self, user_id: UUID) -> int:
        query = select(func.count()).select_from(WithdrawalRequest).where(
            WithdrawalRequest.user_id == user_id
        )
        return await self.session.scalar(query) or 0


class HotWalletActions(Actions):
    async def get_active_hot_wallet(self) -> Optional[HotWallet]:
        query = select(HotWallet).where(HotWallet.is_active == True)
        return await self.get_model(query)

    async def get_all_hot_wallets(self) -> List[HotWallet]:
        query = select(HotWallet)
        return await self.get_models(query)

    async def create_hot_wallet(
        self, 
        address: str, 
        encrypted_private_key: str
    ) -> HotWallet:
        hot_wallet = HotWallet(
            address=address,
            encrypted_private_key=encrypted_private_key,
            balance=Decimal("0"),
            is_active=True
        )
        
        await self.add(hot_wallet)
        await self.commit()
        await self.session.refresh(hot_wallet)
        
        return hot_wallet

    async def update_hot_wallet_balance(
        self, 
        wallet_id: int, 
        new_balance: Decimal
    ) -> bool:
        query = (
            update(HotWallet)
            .where(HotWallet.id == wallet_id)
            .values(
                balance=new_balance,
                last_updated=datetime.now()
            )
        )
        
        result = await self.session.execute(query)
        await self.commit()
        
        return result.rowcount > 0

    async def get_hot_wallet_balance(self, wallet_id: int) -> Optional[Decimal]:
        query = select(HotWallet.balance).where(HotWallet.id == wallet_id)
        return await self.session.scalar(query)

    async def deactivate_hot_wallet(self, wallet_id: int) -> bool:
        query = (
            update(HotWallet)
            .where(HotWallet.id == wallet_id)
            .values(is_active=False)
        )
        
        result = await self.session.execute(query)
        await self.commit()
        
        return result.rowcount > 0


class ColdWalletActions(Actions):
    async def get_active_cold_wallets(self) -> List[ColdWallet]:
        query = select(ColdWallet).where(ColdWallet.is_active == True)
        return await self.get_models(query)

    async def create_cold_wallet(self, address: str) -> ColdWallet:
        cold_wallet = ColdWallet(
            address=address,
            balance=Decimal("0"),
            is_active=True
        )
        
        await self.add(cold_wallet)
        await self.commit()
        await self.session.refresh(cold_wallet)
        
        return cold_wallet

    async def update_cold_wallet_balance(
        self, 
        wallet_id: int, 
        new_balance: Decimal
    ) -> bool:
        query = (
            update(ColdWallet)
            .where(ColdWallet.id == wallet_id)
            .values(balance=new_balance)
        )
        
        result = await self.session.execute(query)
        await self.commit()
        
        return result.rowcount > 0
