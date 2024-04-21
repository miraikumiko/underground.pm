from src.crud import crud_create, crud_reads, crud_read, crud_update, crud_delete
from src.server.models import Server, ServerIP, IPv4, IPv6
from src.server.schemas import (
    ServerCreate,
    ServerRead,
    ServerUpdate,
    IPv4Addr,
    IPv6Addr
)


async def crud_create_server(schema: ServerCreate) -> int:
    server_id = await crud_create(Server, schema)

    return server_id


async def crud_read_servers(user_id: int = None) -> list[ServerRead]:
    if user_id is None:
        servers = await crud_reads(Server)
    else:
        servers = await crud_reads(Server, attr1=Server.user_id, attr2=user_id)

    return servers


async def crud_read_server(server_id: int) -> ServerRead:
    server = await crud_read(Server, attr1=Server.id, attr2=server_id)

    return server


async def crud_update_server(schema: ServerUpdate, server_id: int) -> None:
    await crud_update(Server, schema, attr1=Server.id, attr2=server_id)


async def crud_delete_server(server_id: int) -> None:
    await crud_delete(Server, attr1=Server.id, attr2=server_id)


async def crud_delete_servers(user_id: int) -> None:
    await crud_delete(Server, attr1=Server.user_id, attr2=user_id)


async def crud_read_server_ips() -> list[str]:
    nodes_ips = await crud_reads(ServerIP)

    return nodes_ips


async def crud_read_ipv4s(available: bool = None) -> list[IPv4Addr]:
    if available is None:
        ipv4 = await crud_reads(IPv4)
    else:
        ipv4 = await crud_reads(IPv4, attr1=IPv4.available, attr2=available)

    return ipv4


async def crud_update_ipv4(schema: IPv4Addr, ip: str) -> None:
    await crud_update(IPv4, schema, attr1=IPv4.ip, attr2=ip)


async def crud_read_ipv6s(available: bool = None) -> list[IPv6Addr]:
    if available is None:
        ipv6 = await crud_reads(IPv6)
    else:
        ipv6 = await crud_reads(IPv6, attr1=IPv6.available, attr2=available)

    return ipv6


async def crud_update_ipv6(schema: IPv6Addr, ip: str) -> None:
    await crud_update(IPv6, schema, attr1=IPv6.ip, attr2=ip)
