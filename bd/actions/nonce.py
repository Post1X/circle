from typing import Optional
from datetime import datetime, timedelta

from bd.actions.base import Actions
from bd.models import Nonce

from sqlalchemy import select, delete
import secrets


class NonceActions(Actions):
    async def create_nonce(self, address: str) -> str:
        """
        Создает новый nonce для указанного адреса.
        Помечает старые неиспользованные nonce как использованные.
        
        Args:
            address: Адрес кошелька Tron
            
        Returns:
            str: Сгенерированный nonce
        """
        nonce_value = secrets.token_hex(32)
        
        await self._invalidate_old_nonces(address)
        
        nonce = Nonce(
            address=address,
            nonce=nonce_value,
            used=False,
            created_at=datetime.utcnow()
        )
        
        await self.add(nonce)
        await self.commit()
        
        return nonce_value
    
    async def get_nonce(self, address: str, nonce_value: str) -> Optional[Nonce]:
        """
        Получает nonce по адресу и значению.
        
        Args:
            address: Адрес кошелька
            nonce_value: Значение nonce
            
        Returns:
            Optional[Nonce]: Найденный nonce или None
        """
        query = (
            select(Nonce)
            .where(Nonce.address == address)
            .where(Nonce.nonce == nonce_value)
            .where(Nonce.used == False)
        )
        
        return await self.get_model(query)
    
    async def mark_nonce_as_used(self, nonce: Nonce) -> None:
        """
        Помечает nonce как использованный.
        
        Args:
            nonce: Экземпляр Nonce
        """
        nonce.used = True
        await self.commit()
    
    async def _invalidate_old_nonces(self, address: str) -> None:
        """
        Помечает старые неиспользованные nonce как использованные.
        Удаляет nonce старше 1 часа.
        
        Args:
            address: Адрес кошелька
        """
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        query = (
            delete(Nonce)
            .where(Nonce.address == address)
            .where(Nonce.created_at < one_hour_ago)
        )
        
        await self.session.execute(query)
        
        query = (
            select(Nonce)
            .where(Nonce.address == address)
            .where(Nonce.used == False)
        )
        
        old_nonces = await self.get_models(query)
        for old_nonce in old_nonces:
            old_nonce.used = True
        
        if old_nonces:
            await self.commit()

