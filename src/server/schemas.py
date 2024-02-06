from pydantic import BaseModel, IPvAnyAddress, FilePath
from datetime import datetime


class ServerCreate(BaseModel):
    cores: int
    ram: int
    disk: int
    traffic: int
    location: str
    avaible: bool
    price: float


class ServerRead(BaseModel):
    cores: int
    ram: int
    disk: int
    traffic: int
    location: str
    avaible: bool
    price: float


class ServerUpdate(BaseModel):
    cores: int
    ram: int
    disk: int
    traffic: int
    location: str
    avaible: bool
    price: float


class ActiveServerCreate(BaseModel):
    user_id: int
    server_id: int
    ipv4: IPvAnyAddress
    ipv6: IPvAnyAddress
    xml: str
    start_at: datetime
    end_at: datetime


class ActiveServerRead(BaseModel):
    user_id: int
    server_id: int
    ipv4: IPvAnyAddress
    ipv6: IPvAnyAddress
    xml: str
    start_at: datetime
    end_at: datetime


class ActiveServerUpdate(BaseModel):
    id: int
    user_id: int
    server_id: int
    ipv4: IPvAnyAddress
    ipv6: IPvAnyAddress
    xml: str
    start_at: datetime
    end_at: datetime


class ActiveServerBuy(BaseModel):
    server_id: int
    month: int
    method: str


class ActiveServerPay(BaseModel):
    active_server_id: int
    month: int
    method: str


class ActiveServerAction(BaseModel):
    active_server_id: int
    action: str
