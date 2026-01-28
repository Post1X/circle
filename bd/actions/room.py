from typing import Optional, List

from sqlalchemy import select, and_

from bd.actions.base import Actions
from bd.models import GameRoom


class RoomActions(Actions):
    async def create_room(
        self,
        entry_fee: int,
        min_players: int,
        max_players: int,
        status: str = "waiting",
    ) -> GameRoom:
        """
        Создает новую игровую комнату.
        """
        room = GameRoom(
            entry_fee=entry_fee,
            min_players=min_players,
            max_players=max_players,
            status=status,
        )
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room

    async def get_room_by_id(self, room_id) -> Optional[GameRoom]:
        result = await self.session.execute(
            select(GameRoom).where(GameRoom.room_id == room_id)
        )
        return result.scalar_one_or_none()

    async def get_all_rooms(self) -> List[GameRoom]:
        query = select(GameRoom)
        return list(await self.get_models(query))

    async def get_free_room(
        self,
        entry_fee: int,
        min_players: int,
        max_players: int,
    ) -> Optional[GameRoom]:
        """
        Возвращает первую попавшуюся комнату в статусе "waiting",
        которая еще не заполнена и соответствует параметрам.
        """
        query = (
            select(GameRoom)
            .where(
                and_(
                    GameRoom.status == "waiting",
                    GameRoom.players < GameRoom.max_players,
                    GameRoom.entry_fee == entry_fee,
                    GameRoom.min_players == min_players,
                    GameRoom.max_players == max_players,
                )
            )
            .order_by(GameRoom.created_at)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def add_player(self, room_id) -> None:
        room = await self.get_room_by_id(room_id)
        if room:
            room.players += 1
            await self.session.commit()

    async def check_start_game(self, room_id) -> bool:
        room = await self.get_room_by_id(room_id)
        if room and room.min_players <= room.players:
            return True
        return False
