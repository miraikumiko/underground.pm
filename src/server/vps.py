import libvirt
from libvirt import libvirtError
from mako.template import Template
from src.logger import logger
from src.server.crud import (
    crud_read_server,
    crud_read_server_ips
)
from src.server.rpc import (
    rpc_get_available_cores_number,
    rpc_delete_vps
)


async def vps_create(server_id: int, os: str) -> str:
    try:
        server_addresses = await crud_read_server_ips()
        server = await crud_read_server(server_id)

        for server_address in server_addresses:
            available_cores = await rpc_get_available_cores_number(server_address)

            if available_cores <= server.cores:
                raise Exception("Doesn't have available cores")

            with libvirt.open(f"qemu+ssh://{server_address}/system") as conn:
                with open("src/server/xml/vps.xml", "r") as file:
                    template = Template(file.read())
                    xml = template.render(
                        server_id=server_id,
                        cores=server.cores,
                        ram=server.ram
                    )

                    conn.defineXML(xml)

                    await rpc_create_disk(server_address, str(server_id), server.disk_size)

                    return xml
    except Exception as e:
        logger.error(e)
        raise e


async def vps_delete(server_id: int):
    try:
        await rpc_delete_vps(server_id, "ip")
    except Exception as e:
        logger.error(e)
        raise e


async def vps_action(server_id: int, action: str) -> None:
    try:
        server = await crud_read_server(server_id)

        if server.active:
            async with libvirt.open(f"qemu+ssh://{server.ipv4}/system") as conn:
                vps = conn.lookupByName(str(server_id))

                if action == "on":
                    vps.create()
                elif action == "reboot":
                    vps.reboot()
                elif action == "off":
                    vps.destroy()
                elif action == "delete":
                    vps.destroy()
                    await vps_delete(str(server_id))
                else:
                    raise Exception("Invalid action")
    except Exception as e:
        logger.error(e)
        raise e


async def vps_status(server_id: int) -> str:
    server = await crud_read_server(server_id)

    with libvirt.open(f"qemu+ssh://{server.ipv4}/system") as conn:
        try:
            vps = conn.lookupByName(str(server_id))
            state, _ = vps.state()

            if state == libvirt.VIR_DOMAIN_RUNNING:
                return "on"
            elif state == libvirt.VIR_DOMAIN_REBOOT_SIGNAL:
                return "reboot"
            elif state == libvirt.VIR_DOMAIN_SHUTOFF:
                return "off"
            else:
                return "unknown"
        except libvirtError:
            return "uninstalled"
        except Exception as e:
            logger.error(e)
            return "unknown"
