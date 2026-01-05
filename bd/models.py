from typing import Dict, List, Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    Boolean,
    String,
    Integer,
    DateTime,
    func,
    ForeignKey,
    DECIMAL as PG_DECIMAL,
    Enum as PG_ENUM
)
from datetime import datetime
from decimal import Decimal

from uuid import UUID, uuid4

from bd import Base

from enum import Enum


class TransactionStatus(Enum):
    CREATED = "created"
    BROADCASTED = "broadcasted"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DROPPED = "dropped"


class TransactionType(Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(34), nullable=True)

    balance: Mapped[Decimal] = mapped_column(PG_DECIMAL, nullable=False)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    total_winnings: Mapped[Decimal] = mapped_column(PG_DECIMAL, nullable=False)
    leaderboard_rank: Mapped[int] = mapped_column(Integer, default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Nonce(Base):
    __tablename__ = "nonce"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(34), nullable=False, index=True)
    nonce: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    used: Mapped[bool] = mapped_column(Boolean, default=False)



class GameSession(Base):
    __tablename__ = "game_session"

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    room_id: Mapped[UUID] = mapped_column(ForeignKey("game_room.room_id"), nullable=False)
    total_bank: Mapped[Decimal] = mapped_column(PG_DECIMAL)
    zone_fund: Mapped[int] = mapped_column(Integer, default=0)
    bonus_fund: Mapped[int] = mapped_column(Integer, default=0)
    current_phase: Mapped[str] = mapped_column(String(20), default="start")
    next_shrink_at: Mapped[datetime] = mapped_column(DateTime)


class GameRoom(Base):
    __tablename__ = "game_room"

    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    entry_fee: Mapped[int] = mapped_column(Integer)

    players: Mapped[int] = mapped_column(Integer, default=0)
    min_players: Mapped[int] = mapped_column(Integer, default=20)
    max_players: Mapped[int] = mapped_column(Integer, default=100)

    status: Mapped[str] = mapped_column(String, default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Wallet(Base):
    __tablename__ = "wallet"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.user_id"))
    address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False)
    network: Mapped[str] = mapped_column(String(10), nullable=False)
    wallet_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount: Mapped[float] = mapped_column(PG_DECIMAL, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        PG_ENUM(TransactionStatus), 
        nullable=False,
        default=TransactionStatus.CREATED,
    )
    type: Mapped[TransactionType] = mapped_column(PG_ENUM(TransactionType), nullable=False)
    user_wallet_address: Mapped[str] = mapped_column(
        ForeignKey("wallet.address"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )


class WithdrawalStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.user_id"))
    amount: Mapped[Decimal] = mapped_column(PG_DECIMAL, nullable=False)
    to_address: Mapped[str] = mapped_column(String(42), nullable=False)
    fee: Mapped[Decimal] = mapped_column(PG_DECIMAL, nullable=False, default=Decimal("0"))
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    transaction_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class HotWallet(Base):
    __tablename__ = "hot_wallet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(PG_DECIMAL, nullable=False, default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ColdWallet(Base):
    __tablename__ = "cold_wallet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(PG_DECIMAL, nullable=False, default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now())
