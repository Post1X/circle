import logging

from bd.actions.withdrawal import HotWalletActions
from bd.database import async_session_maker

from cryptography.fernet import Fernet

from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron
from hdwallet.derivations import (
    CHANGES, 
    BIP44Derivation
)
from hdwallet.mnemonics import BIP39Mnemonic

from servises.config import config

logger = logging.getLogger(__name__)


async def init_hot_wallet():
    try:
        async with async_session_maker() as session:
            hot_wallet_actions = HotWalletActions(session)
            
            existing_wallet = await hot_wallet_actions.get_active_hot_wallet()
            if existing_wallet:
                logger.info(f"Hot wallet already exists: {existing_wallet.address}")
                return
            
            cipher = Fernet(config.ENCRYPTION_KEY.encode())
            
            hdwallet = HDWallet(cryptocurrency=Tron)
            hd = hdwallet.from_mnemonic(mnemonic=BIP39Mnemonic(mnemonic=config.mnemonic))
            
            hd.clean_derivation()
            hd.update_derivation(BIP44Derivation(
                coin_type=Tron.COIN_TYPE,
                account=0,
                change=CHANGES.EXTERNAL_CHAIN,
                address=999999
            ))
            
            address = hd.address()
            private_key = hd.private_key()
            
            encrypted_private_key = cipher.encrypt(private_key.encode()).decode()
            
            hot_wallet = await hot_wallet_actions.create_hot_wallet(
                address=address,
                encrypted_private_key=encrypted_private_key
            )
            
            logger.info("Hot wallet created successfully!")
            logger.info(f"Address: {hot_wallet.address}")
            logger.warning("Please fund this wallet with USDT for withdrawals to work")
            logger.warning("Without funding, withdrawals will fail!")
    except Exception as e:
        logger.error(f"Hot wallet initialization failed: {e}")
        logger.warning("System will work for deposits only. Withdrawals will be disabled.")
