from bd.actions.base import Actions

from bd.models import Wallet


class WalletActions(Actions):
    async def add_wallet(self, **data) -> Wallet:
        wallet = Wallet(**data)

        await self.add(wallet)
        await self.commit()

        return wallet
