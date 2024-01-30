from fastapi import (
    FastAPI,
    APIRouter,
    Depends,
    UploadFile,
    HTTPException
)
from fastapi.responses import Response
from fastapi_cache.decorator import cache
from src.auth.utils import users
from src.user.models import User
from src.server.models import Server
from src.server.schemas import (
    ServerCreate,
    ServerUpdate,
    ServerAction,
    ServerCheckout
)
from src.server.schemas import ActiveServerCreate, ActiveServerUpdate
from src.server.crud import (
    crud_add_server,
    crud_get_servers,
    crud_get_server,
    crud_update_server,
    crud_delete_server,
    crud_add_active_server,
    crud_get_active_servers,
    crud_get_active_server,
    crud_update_active_server,
    crud_delete_active_server
)
from src.server.vps import (
    vps_server_on,
    vps_server_reboot,
    vps_server_off
)
from src.server.payments import (
    payment_checkout_with_xmr,
    payment_checkout_with_paypal
)
from src.server.utils import upload_iso
from src.logger import logger

router = APIRouter(
    prefix="/api/server",
    tags=["servers"]
)

active_user = users.current_user(active=True)
admin = users.current_user(active=True, superuser=True, verified=True)


@router.post("/add")
async def add_server(data: ServerCreate, user: User = Depends(admin)):
    try:
        await crud_add_server(data)

        return {
            "status": "success",
            "data": None,
            "details": "server info has been added"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.get("/all")
@cache(expire=3600)
async def get_servers():
    try:
        servers = await crud_get_servers()

        return {
            "status": "success",
            "data": servers,
            "details": "info of all servers"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.get("/{id}")
@cache(expire=3600)
async def get_server(id: int):
    try:
        server = await crud_get_server(id)

        return {
            "status": "success",
            "data": server,
            "details": "server info"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.post("/update/{id}")
async def update_server(id: int, data: ServerUpdate, user: User = Depends(admin)):
    try:
        await crud_update_server(id, data)

        return {
            "status": "success",
            "data": None,
            "details": f"server with id {id} has been updated"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.delete("/delete/{id}")
async def delete_server(id: int, user: User = Depends(admin)):
    try:
        await crud_delete_server(id)

        return {
            "status": "success",
            "data": None,
            "details": f"server with id {id} has been deleted"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.get("/active/me")
async def get_active_servers(user_id: int, user: User = Depends(active_user)):
    try:
        servers = await crud_get_active_servers(user_id)

        return {
            "status": "success",
            "data": servers,
            "details": f"info of all servers of user with id {id}"
        }
    except Exception:
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.get("/active/me/{id}")
async def get_active_server(id: int, user: User = Depends(active_user)):
    try:
        server = await crud_get_active_server(id)

        return {
            "status": "success",
            "data": server,
            "details": "user server info"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.patch("/active/me/{id}")
async def update_active_server(id: int, data: ActiveServerUpdate, user: User = Depends(active_user)):
    try:
        await crud_update_active_server(id, data)

        return {
            "status": "success",
            "data": None,
            "details": f"user server with id {id} has been updated"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.post("/active/upload/iso")
async def upload_iso_server(server_id: int, iso: UploadFile, user: User = Depends(active_user)):
    if iso.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "data": None,
            "details": "this is not .iso file"
        })
    try:
        await upload_iso(user.id, iso)

        return {
            "status": "success",
            "data": None,
            "details": "iso has been uploaded"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.post("/action")
async def action_of_server(data: ServerAction, user: User = Depends(active_user)):
    try:
        if data.action == "on":
            await vps_server_on(data.id)
        elif data.action == "reboot":
            await vps_server_reboot(data.id)
        elif data.action == "off":
            await vps_server_off(data.id)
        else:
            raise ValueError("invalid server action")

        return {
            "status": "success",
            "data": None,
            "details": f"server has been {data.action}"
        }
    except ValueError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "data": None,
            "details": e
        })
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.post("/buy")
async def buy_server(data: ServerCheckout, user: User = Depends(active_user)):
    try:
        if data.action == "xmr":
            await payment_checkout_with_xmr(data.server_id, user.id)
        elif data.action == "paypal":
            await payment_checkout_with_paypal(data.server_id, user.id)
        else:
            raise ValueError("invalid payment method")

        return {
            "status": "success",
            "data": None,
            "details": f"server has been bought with {data.method}"
        }
    except ValueError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "data": None,
            "details": e
        })
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


@router.post("/pay")
async def pay_server(data: ServerCheckout, user: User = Depends(active_user)):
    try:
        if data.action == "xmr":
            await payment_checkout_with_xmr(data.server_id, user.id)
        elif data.action == "paypal":
            await payment_checkout_with_paypal(data.server_id, user.id)
        else:
            raise ValueError("invalid payment method")

        return {
            "status": "success",
            "data": None,
            "details": f"server has been payed with {data.method}"
        }
    except ValueError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "data": None,
            "details": e
        })
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": "server error"
        })


def add_server_router(app: FastAPI):
    app.include_router(router)
