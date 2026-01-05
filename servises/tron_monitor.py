import asyncio
import aiohttp
import logging

from decimal import Decimal
from typing import (
    Dict, 
    List, 
    Optional
)
from uuid import UUID

from bd.actions.balance import BalanceActions
from bd.actions.user import UserActions
from bd.database import async_session_maker
from bd.models import (
    Transaction, 
    TransactionStatus, 
    TransactionType, 
    Wallet
)

from sqlalchemy import select
from servises.config import config


class TronMonitor:
    def __init__(self):
        self.session = None
        self.balance_actions = None
        self.user_actions = None
        self.tron_api_url = "https://api.trongrid.io"
        self.usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        self.confirmation_threshold = 3
        self.logger = logging.getLogger(__name__)
        
    async def start_monitoring(self):
        async with async_session_maker() as session:
            self.session = session
            self.balance_actions = BalanceActions(session)
            self.user_actions = UserActions(session)
            
            while True:
                try:
                    await self._check_deposits()
                    await asyncio.sleep(30)
                except Exception as e:
                    self.logger.error(f"Error in monitoring: {e}")
                    await asyncio.sleep(60)
    
    async def _check_deposits(self):
        user_addresses = await self._get_all_user_addresses()
        
        for address in user_addresses:
            try:
                await self._check_address_deposits(address)
            except Exception as e:
                self.logger.error(f"Error checking address {address}: {e}")
    
    async def _get_all_user_addresses(self) -> List[str]:
        query = select(Wallet.address).where(Wallet.user_id.isnot(None))
        result = await self.session.execute(query)
        return [row[0] for row in result.fetchall()]
    
    async def _check_address_deposits(self, address: str):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            url = f"{self.tron_api_url}/v1/accounts/{address}/transactions/trc20"
            params = {
                "limit": 50,
                "contract_address": self.usdt_contract,
                "only_confirmed": True,
                "only_to": True
            }
            headers = {
                "TRON-PRO-API-KEY": config.tron_api_key,
                "Content-Type": "application/json"
            }
            
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._process_transactions(address, data.get('data', []))
                    elif response.status == 429:
                        self.logger.warning(f"Rate limit exceeded for address {address}")
                        await asyncio.sleep(60)
                    else:
                        self.logger.warning(f"TronGrid API error for address {address}: {response.status}")
            except aiohttp.ClientError as e:
                self.logger.error(f"HTTP error checking address {address}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error checking address {address}: {e}")
    
    async def _process_transactions(self, address: str, transactions: List[Dict]):
        for tx in transactions:
            if tx.get('to') == address and tx.get('token_info', {}).get('symbol') == 'USDT':
                await self._process_deposit(address, tx)
    
    async def _process_deposit(self, address: str, tx: Dict):
        tx_hash = tx.get('transaction_id')
        amount = Decimal(tx.get('value', 0)) / Decimal(10**6)
        confirmations = tx.get('confirmed', 0)
        
        if confirmations < self.confirmation_threshold:
            return
        
        existing_tx = await self._get_existing_transaction(address, amount)
        if existing_tx:
            return
        
        user = await self.user_actions.get_user_by_wallet_address(address)
        if not user:
            return
        
        try:
            await self._create_deposit_transaction(user.user_id, amount, tx_hash, address)
            await self.balance_actions.topup_balance(user.user_id, amount)
            self.logger.info(f"Deposit processed: {amount} USDT for user {user.user_id} from {address}")
        except Exception as e:
            self.logger.error(f"Failed to process deposit for user {user.user_id}: {e}")
    
    async def _get_existing_transaction(self, address: str, amount: Decimal) -> Optional[Transaction]:
        query = select(Transaction).where(
            Transaction.user_wallet_address == address,
            Transaction.amount == float(amount),
            Transaction.type == TransactionType.INCOMING
        ).order_by(Transaction.created_at.desc())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _create_deposit_transaction(self, user_id: UUID, amount: Decimal, tx_hash: str, address: str):
        transaction = Transaction(
            amount=float(amount),
            status=TransactionStatus.CONFIRMED,
            type=TransactionType.INCOMING,
            user_wallet_address=address
        )
        
        self.session.add(transaction)
        await self.session.commit()


async def start_tron_monitor():
    monitor = TronMonitor()
    await monitor.start_monitoring()
