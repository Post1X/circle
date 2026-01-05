from enum import Enum

from pydantic import BaseModel


class WalletType(str, Enum):
    METAMASK = "metamask"
    PHANTOM = "phantom"
    TRON = "tron"


class WalletLinkRequest(BaseModel):
    address: str
    signature: str


class WalletResponse(BaseModel):
    id: int
    address: str
    network: str
    is_primary: bool


class WalletAttachRequest(BaseModel):
    wallet_address: str
    signature: str
    message: str


class WalletConnectRequest(BaseModel):
    address: str
    wallet_type: WalletType
    message: str
    signature: str


class TransferRequest(BaseModel):
    amount: float
    currency: str = "USDT"
