from pydantic import BaseModel


class Buy(BaseModel):
    cores: int
    ram: int
    disk_size: int
    month: int


class Pay(BaseModel):
    server_id: int
    month: int


class Upgrade(BaseModel):
    server_id: int
    cores: int
    ram: int
    disk_size: int
