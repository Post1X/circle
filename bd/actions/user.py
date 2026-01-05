from typing import Optional

from uuid import UUID

from decimal import Decimal

from bd.actions.base import Actions

from bd.models import User

from sqlalchemy import select, update


class UserActions(Actions):
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        query = (
            select(User)
            .where(User.user_id == user_id)
        )

        return await self.get_model(query)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        query = (
            select(User)
            .where(User.username == username)
        )

        return await self.get_model(query)
    
    async def get_user_by_wallet_address(self, wallet_address: str) -> Optional[User]:
        from bd.models import Wallet
        
        query = (
            select(User)
            .join(Wallet, User.user_id == Wallet.user_id)
            .where(Wallet.address == wallet_address)
        )

        return await self.get_model(query)
    
    async def create_user(self, username: str, hashed_password: str) -> User:
        user_data = {
            "username": username,
            "hashed_password": hashed_password,
            "balance": Decimal("0.0"),
            "games_played": 0,
            "total_winnings": Decimal('0.0'),
            "leaderboard_rank": 0
        }
        
        user = User(**user_data)

        await self.add(user)
        await self.commit()
        await self.session.refresh(user)

        return user

    async def update_user_balance(self, user_id: UUID, new_balance: Decimal) -> None:
        query = (
            update(User)
            .where(User.user_id == user_id)
            .values(balance=new_balance)
        )
        
        await self.session.execute(query)
        await self.commit()

    async def bind_wallet_to_user(self, user_id: UUID, wallet_address: str) -> bool:
        from bd.models import Wallet
        
        existing_user = await self.get_user_by_wallet_address(wallet_address)
        if existing_user:
            return False
        
        wallet = Wallet(
            user_id=user_id,
            address=wallet_address,
            network="tron",
            is_primary=True
        )
        
        await self.add(wallet)
        await self.commit()
        
        return True
    
    async def update_username(self, user_id: UUID, new_username: str) -> None:
        query = (
            update(User)
            .where(User.user_id == user_id)
            .values(username=new_username)
        )
        
        await self.session.execute(query)
        await self.commit()
