import asyncio
import aiohttp
import logging

from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron
from hdwallet.derivations import (
    CHANGES, 
    BIP44Derivation
)
from hdwallet.mnemonics import BIP39Mnemonic

from decimal import Decimal

from typing import Optional, List

from cryptography.fernet import Fernet

from bd.actions.withdrawal import (
    WithdrawalActions, 
    HotWalletActions
)
from bd.actions.balance import BalanceActions
from bd.database import async_session_maker
from bd.models import (
    WithdrawalRequest, 
    HotWallet,
    Wallet
)

from sqlalchemy import select

from servises.config import config


class TronAPIError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class WithdrawalService:
    def __init__(self):
        self.tron_api_url = "https://api.trongrid.io"
        self.usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        self.confirmation_threshold = 3
        self.logger = logging.getLogger(__name__)
        self.cipher = Fernet(config.ENCRYPTION_KEY.encode())

    def encrypt_private_key(self, private_key: str) -> str:
        return self.cipher.encrypt(private_key.encode()).decode()

    def decrypt_private_key(self, encrypted_key: str) -> str:
        return self.cipher.decrypt(encrypted_key.encode()).decode()

    async def start_processing_withdrawals(self):
        async with async_session_maker() as session:
            withdrawal_actions = WithdrawalActions(session)
            hot_wallet_actions = HotWalletActions(session)
            balance_actions = BalanceActions(session)
            
            while True:
                try:
                    await self._process_pending_withdrawals(
                        withdrawal_actions, 
                        hot_wallet_actions, 
                        balance_actions
                    )
                    await asyncio.sleep(30)
                except Exception as e:
                    self.logger.error(f"Error processing withdrawals: {e}")
                    await asyncio.sleep(60)

    async def _process_pending_withdrawals(
        self, 
        withdrawal_actions: WithdrawalActions,
        hot_wallet_actions: HotWalletActions,
        balance_actions: BalanceActions
    ):
        pending_withdrawals = await withdrawal_actions.get_pending_withdrawals()
        
        for withdrawal in pending_withdrawals:
            try:
                await self._process_single_withdrawal(
                    withdrawal, 
                    withdrawal_actions, 
                    hot_wallet_actions, 
                    balance_actions
                )
            except Exception as e:
                self.logger.error(f"Error processing withdrawal {withdrawal.id}: {e}")
                await withdrawal_actions.update_withdrawal_status(
                    withdrawal.id,
                    "failed",
                    error_message=str(e)
                )

    async def _process_single_withdrawal(
        self,
        withdrawal: WithdrawalRequest,
        withdrawal_actions: WithdrawalActions,
        hot_wallet_actions: HotWalletActions,
        balance_actions: BalanceActions
    ):
        await withdrawal_actions.update_withdrawal_status(
            withdrawal.id,
            "processing"
        )

        hot_wallet = await hot_wallet_actions.get_active_hot_wallet()
        if not hot_wallet:
            self.logger.warning("No active hot wallet found. Withdrawals disabled.")
            await withdrawal_actions.update_withdrawal_status(
                withdrawal.id,
                "failed",
                error_message="Withdrawal system not configured. Please contact administrator."
            )
            return

        real_balance = await self._get_real_usdt_balance(hot_wallet.address)
        required_amount = withdrawal.amount + withdrawal.fee

        if real_balance < required_amount:
            await self._collect_funds_to_hot_wallet(hot_wallet, required_amount - real_balance)
            real_balance = await self._get_real_usdt_balance(hot_wallet.address)

        if real_balance < required_amount:
            raise InsufficientFundsError(f"Insufficient funds in hot wallet. Required: {required_amount}, Available: {real_balance}")

        try:
            tx_hash = await self._send_usdt_transaction(
                hot_wallet,
                withdrawal.to_address,
                withdrawal.amount
            )

            await withdrawal_actions.update_withdrawal_status(
                withdrawal.id,
                "completed",
                transaction_hash=tx_hash
            )

            await balance_actions.debit_for_entry_fee(
                withdrawal.user_id,
                withdrawal.amount + withdrawal.fee
            )

            self.logger.info(f"Withdrawal {withdrawal.id} completed. TX: {tx_hash}")

        except Exception as e:
            await withdrawal_actions.update_withdrawal_status(
                withdrawal.id,
                "failed",
                error_message=str(e)
            )
            raise

    async def _get_real_usdt_balance(self, address: str) -> Decimal:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            url = f"{self.tron_api_url}/v1/accounts/{address}/tokens"
            params = {
                "contract_address": self.usdt_contract
            }
            headers = {
                "TRON-PRO-API-KEY": config.tron_api_key,
                "Content-Type": "application/json"
            }

            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        tokens = data.get('data', [])
                        
                        for token in tokens:
                            if token.get('contract_address') == self.usdt_contract:
                                balance = Decimal(token.get('balance', 0)) / Decimal(10**6)
                                return balance
                        return Decimal("0")
                    else:
                        self.logger.warning(f"TronGrid API error: {response.status}")
                        return Decimal("0")
            except Exception as e:
                self.logger.error(f"Error getting balance for {address}: {e}")
                return Decimal("0")

    async def _collect_funds_to_hot_wallet(self, hot_wallet: HotWallet, required_amount: Decimal):
        user_addresses = await self._get_user_addresses_with_balance()
        
        for address in user_addresses:
            if required_amount <= 0:
                break
                
            balance = await self._get_real_usdt_balance(address)
            if balance > 0:
                transfer_amount = min(balance, required_amount)
                await self._transfer_from_user_address(address, hot_wallet.address, transfer_amount)
                required_amount -= transfer_amount

    async def _get_user_addresses_with_balance(self) -> List[str]:
        async with async_session_maker() as session:
            query = select(Wallet.address).where(Wallet.user_id.isnot(None))
            result = await session.execute(query)

            return [row[0] for row in result.fetchall()]

    async def _transfer_from_user_address(self, from_address: str, to_address: str, amount: Decimal):
        private_key = await self._get_private_key_for_address(from_address)
        if not private_key:
            return

        try:
            tx_hash = await self._send_usdt_with_private_key(
                private_key,
                to_address,
                amount
            )
            self.logger.info(f"Transferred {amount} USDT from {from_address} to {to_address}. TX: {tx_hash}")
        except Exception as e:
            self.logger.error(f"Error transferring from {from_address}: {e}")

    async def _get_private_key_for_address(self, address: str) -> Optional[str]:
        try:
            hdwallet = HDWallet(cryptocurrency=Tron)
            hd = hdwallet.from_mnemonic(mnemonic=BIP39Mnemonic(mnemonic=config.mnemonic))

            for i in range(1000):
                hd.clean_derivation()
                hd.update_derivation(BIP44Derivation(
                    coin_type=Tron.COIN_TYPE,
                    account=0,
                    change=CHANGES.EXTERNAL_CHAIN,
                    address=i
                ))
                
                if hd.address() == address:
                    return hd.private_key()
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting private key for {address}: {e}")
            return None

    async def _send_usdt_transaction(self, hot_wallet: HotWallet, to_address: str, amount: Decimal) -> str:
        private_key = self.decrypt_private_key(hot_wallet.encrypted_private_key)
        return await self._send_usdt_with_private_key(private_key, to_address, amount)

    async def _send_usdt_with_private_key(self, private_key: str, to_address: str, amount: Decimal) -> str:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            url = f"{self.tron_api_url}/wallet/createtransaction"
            
            amount_sun = int(amount * Decimal(10**6))
            
            data = {
                "to_address": to_address,
                "owner_address": private_key,
                "amount": amount_sun,
                "contract_address": self.usdt_contract
            }
            
            headers = {
                "TRON-PRO-API-KEY": config.tron_api_key,
                "Content-Type": "application/json"
            }

            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        tx_hash = result.get('txID')
                        if tx_hash:
                            return tx_hash
                        else:
                            raise TronAPIError(f"Transaction creation failed: {result}")
                    else:
                        raise TronAPIError(f"TronGrid API error: {response.status}")
            except Exception as e:
                raise TronAPIError(f"Error sending USDT: {e}")

    async def monitor_withdrawal_transactions(self):
        async with async_session_maker() as session:
            withdrawal_actions = WithdrawalActions(session)
            
            while True:
                try:
                    processing_withdrawals = await withdrawal_actions.get_processing_withdrawals()
                    
                    for withdrawal in processing_withdrawals:
                        if withdrawal.transaction_hash:
                            confirmed = await self._check_transaction_confirmation(
                                withdrawal.transaction_hash
                            )
                            
                            if confirmed:
                                await withdrawal_actions.update_withdrawal_status(
                                    withdrawal.id,
                                    "completed"
                                )
                    
                    await asyncio.sleep(60)
                except Exception as e:
                    self.logger.error(f"Error monitoring transactions: {e}")
                    await asyncio.sleep(60)

    async def _check_transaction_confirmation(self, tx_hash: str) -> bool:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            url = f"{self.tron_api_url}/wallet/gettransactionbyid"
            params = {"value": tx_hash}
            headers = {
                "TRON-PRO-API-KEY": config.tron_api_key,
                "Content-Type": "application/json"
            }

            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        confirmations = data.get('confirmed', 0)
                        return confirmations >= self.confirmation_threshold
                    return False
            except Exception as e:
                self.logger.error(f"Error checking transaction {tx_hash}: {e}")
                return False


async def start_withdrawal_processing():
    service = WithdrawalService()
    await service.start_processing_withdrawals()


async def start_withdrawal_monitoring():
    service = WithdrawalService()
    await service.monitor_withdrawal_transactions()
