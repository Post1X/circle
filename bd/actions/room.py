from bd.actions.base import Actions
from bd.models import GameRoom
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime

class RoomActions(Actions):
    async def create_room(self, entry_fee: int, min_players: int, max_players: int, status: str = "waiting") -> GameRoom:
        room = GameRoom(
            entry_fee=entry_fee,
            min_players=min_players,
            max_players=max_players,
            status=status,
            created_at=datetime.utcnow(),
        )
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room

    async def get_room_by_id(self, room_id) -> Optional[GameRoom]:
        result = await self.session.execute(select(GameRoom).where(GameRoom.room_id == room_id))
        return result.scalar_one_or_none()

    async def get_all_rooms(self) -> List[GameRoom]:
        query = select(GameRoom)
        return list(await self.get_models(query)) 
    
    async def add_player(self, room_id) -> None:
        room = await self.get_room_by_id(room_id)
        if room:
            room.players += 1
            await self.session.commit()

    async def check_start_game(self, room_id) -> bool:
        # return True
        room = await self.get_room_by_id(room_id)
        if room and room.min_players <= room.players:
            return True
        return False
