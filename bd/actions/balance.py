from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import UUID
from decimal import Decimal

import redis.asyncio as aioredis

from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron
from hdwallet.derivations import CHANGES, BIP44Derivation
from hdwallet.mnemonics import BIP39Mnemonic

from pydantic import BaseModel

from sqlalchemy import func, select

from bd.actions.base import Actions
from bd.models import User, Wallet, Transaction, TransactionStatus, TransactionType

from servises import config


class Adres(BaseModel):
    addres: str
    user_id: Optional[str] = None
    time: datetime = datetime.now(timezone.utc)


_all_addresses: set[str] = set()
_active_addresses: dict[str, Adres] = {}

hdwallet: HDWallet = HDWallet(cryptocurrency=Tron)
hd = hdwallet.from_mnemonic(mnemonic=BIP39Mnemonic(mnemonic=config.mnemonic))


def generate_new_address(address_index=0) -> str:
    """
    Генерирует новый Tron адрес на основе переданного HDWallet.
    """
    hd.clean_derivation()
    
    hd.update_derivation(BIP44Derivation(
        coin_type=Tron.COIN_TYPE,
        account=0,
        change=CHANGES.EXTERNAL_CHAIN,
        address=address_index
    ))
    adr = hd.address()
    if adr:
        return adr
    return ""


class BalanceActions(Actions):
    async def _sync(self):
        query = select(Wallet)
        wallets = list(await self.get_models(query))
        now = datetime.now(timezone.utc)
        for wallet in wallets:
            adr = wallet.address
            _all_addresses.add(adr)
            if adr not in _active_addresses:
                _active_addresses[adr] = Adres(addres=adr, user_id=None, time=now)

    async def get_address(self, user_id: str) -> str:
        await self._sync()
        for adr, rec in _active_addresses.items():
            if rec.user_id == user_id:
                return adr
        now = datetime.now(timezone.utc)
        expiration = timedelta(minutes=10)
        for adr, rec in _active_addresses.items():
            if rec.user_id is None or (now - rec.time) > expiration:
                rec.user_id = user_id
                rec.time = now
                return adr
        adr = await self._create_new_addres(user_id)
        _active_addresses[adr] = Adres(addres=adr, user_id=user_id, time=now)
        return adr

    async def _create_new_addres(self, user_id: str) -> str:
        length = await self.session.scalar(select(func.count()).select_from(Wallet))
        if not length:
            length = 0 
        adr = generate_new_address(length+1)
        
        wallet = Wallet(
            user_id=user_id,
            address=adr,
            network="tron",
            is_primary=False
        )
        self.session.add(wallet)
        await self.commit()
        await self._sync()

        return adr

    async def _get_user_for_update(self, user_id: UUID) -> Optional[User]:
        query = (
            select(User)
            .where(User.user_id == user_id)
            .with_for_update()
        )
        
        return await self.get_model(query)

    async def debit_for_entry_fee(self, user_id: UUID, amount: Decimal) -> bool:
        user = await self._get_user_for_update(user_id)
        if not user:
            return False

        if amount <= 0:
            return False

        if user.balance is None:
            user.balance = Decimal(0)

        if Decimal(user.balance) < Decimal(amount):
            return False

        user.balance = Decimal(user.balance) - Decimal(amount)

        await self.commit()

        return True

    async def credit_winnings(self, user_id: UUID, amount: Decimal) -> bool:
        user = await self._get_user_for_update(user_id)
        if not user:
            return False

        if amount <= 0:
            return False

        if user.balance is None:
            user.balance = Decimal(0)

        if user.total_winnings is None:
            user.total_winnings = Decimal(0)

        user.balance = Decimal(user.balance) + Decimal(amount)
        user.total_winnings = Decimal(user.total_winnings) + Decimal(amount)

        await self.commit()

        return True

    async def credit_early_exit(self, payouts: Dict[str, float]) -> None:
        for pid, amt in payouts.items():
            try:
                uid = UUID(str(pid))
            except Exception:
                continue

            await self.credit_winnings(uid, Decimal(str(amt)))

    async def credit_super_exit(self, payouts: Dict[str, float]) -> None:
        for pid, amt in payouts.items():
            try:
                uid = UUID(str(pid))
            except Exception:
                continue

            await self.credit_winnings(uid, Decimal(str(amt)))

    async def credit_finalists(self, payouts: Dict[str, float]) -> None:
        for pid, amt in payouts.items():
            try:
                uid = UUID(str(pid))
            except Exception:
                continue

            await self.credit_winnings(uid, Decimal(str(amt)))

    async def topup_balance(self, user_id: UUID, amount: Decimal) -> bool:
        user = await self._get_user_for_update(user_id)
        if not user:
            return False

        if amount <= 0:
            return False

        if user.balance is None:
            user.balance = Decimal(0)

        user.balance = Decimal(user.balance) + Decimal(amount)

        await self.commit()

        return True

    async def create_deposit_transaction(self, user_id: UUID, amount: Decimal, transaction_hash: str) -> bool:
        try:
            wallet_address = await self.get_address(str(user_id))
            
            transaction = Transaction(
                amount=float(amount),
                status=TransactionStatus.CREATED,
                type=TransactionType.INCOMING,
                user_wallet_address=wallet_address
            )
            
            await self.add(transaction)
            await self.commit()
            
            return True
        except Exception:
            return False

    async def get_user_transactions(self, user_id: UUID) -> list:
        wallet_address = await self.get_address(str(user_id))
        query = (
            select(Transaction)
            .where(Transaction.user_wallet_address == wallet_address)
            .where(Transaction.type == TransactionType.INCOMING)
            .order_by(Transaction.created_at.desc())
        )
        
        return await self.get_models(query)
