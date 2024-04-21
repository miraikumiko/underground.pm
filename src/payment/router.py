from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, JSONResponse
from datetime import datetime, timedelta
from src.database import r
from src.logger import logger
from src.config import PRICE_CPU, PRICE_RAM, PRICE_DISK, PRICE_IPV4
from src.payment.schemas import Pay
from src.payment.payments import payment_request
from src.payment.utils import xmr_course
from src.server.schemas import ServerCreate, Specs, IPv4Addr, IPv6Addr
from src.server.crud import (
    crud_create_server,
    crud_read_server,
    crud_read_ipv4s,
    crud_update_ipv4,
    crud_read_ipv6s,
    crud_update_ipv6
)
from src.user.models import User
from src.auth.utils import active_user

router = APIRouter(prefix="/api/payment", tags=["payments"])


@router.post("/buy")
async def buy(data: Specs, user: User = Depends(active_user)):
    # Check user's active payments
    payment_uri = await r.get(f"payment_uri:{user.id}")

    if payment_uri is not None:
        ttl = await r.ttl(f"payment_uri:{user.id}")

        return JSONResponse({
            "payment_uri": payment_uri,
            "ttl": ttl,
            "detail": "You already have payment"
        }, status_code=203)

    # Validate specs
    if data.cores not in (1, 2, 4, 8):
        raise HTTPException(status_code=400, detail="Invalid cores count")

    if data.ram not in (1024, 2048, 4096, 8192):
        raise HTTPException(status_code=400, detail="Invalid ram count")

    if data.disk_size not in (32, 64, 128, 256, 512, 1024):
        raise HTTPException(status_code=400, detail="Invalid disk size")

    if data.month not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        raise HTTPException(status_code=400, detail="Invalid month count")

    if data.ipv4:
        ipv4s = await crud_read_ipv4s(True)

        if not ipv4s:
            raise HTTPException(
                status_code=400,
                detail="Haven't available IPv4 addresses"
            )

        ipv4 = ipv4s[0]
        await crud_update_ipv4(IPv4Addr(available=False), ipv4)
    else:
        ipv4 = None

    # Make payment request and return it uri
    server_schema = ServerCreate(
        cores=data.cores,
        ram=data.ram,
        disk_type="ssd",
        disk_size=data.disk_size,
        traffic=1,
        location="Spain",
        ipv4=ipv4,
        ipv6=None,
        start_at=datetime.utcnow(),
        end_at=datetime.now() + timedelta(days=30 * data.month),
        active=False,
        user_id=user.id
    )

    server_id = await crud_create_server(server_schema)

    payment_data = {
        "user_id": user.id,
        "server_id": server_id,
        "month": data.month
    }

    amount = (
        (1 / data.cores * PRICE_CPU) +
        (1024 / data.ram * PRICE_RAM) +
        (32 / data.disk_size * PRICE_DISK) +
        (data.ipv4 if PRICE_IPV4 else 0)
    ) * data.month

    payment_uri = await payment_request(payment_data, float(amount))
    ttl = await r.ttl(f"payment_uri:{user.id}")

    return {"payment_uri": payment_uri, "ttl": ttl}


@router.post("/pay")
async def pay(data: Pay, user: User = Depends(active_user)):
    # Check user's active payments
    payment_uri = await r.get(f"payment_uri:{user.id}")

    if payment_uri is not None:
        ttl = await r.ttl(f"payment_uri:{user.id}")

        return JSONResponse({
            "payment_uri": payment_uri,
            "ttl": ttl,
            "detail": "You already have payment"
        }, status_code=203)

    # Validate params
    if data.month < 1 or data.month > 12:
        raise HTTPException(status_code=400, detail="Invalid month count")

    # Make payment request and return it uri
    server = await crud_read_server(data.server_id)

    if server is None:
        raise HTTPException(status_code=400)

    payment_data = {
        "user_id": user.id,
        "server_id": data.server_id,
        "month": data.month
    }

    amount = (
        (1 / server.cores * PRICE_CPU) +
        (1024 / server.ram * PRICE_RAM) +
        (32 / server.disk_size * PRICE_DISK) +
        (server.ipv4 is not None if PRICE_IPV4 else 0)
    ) * data.month

    payment_uri = await payment_request(payment_data, float(amount))
    ttl = await r.ttl(f"payment_uri:{user.id}")

    return {"payment_uri": payment_uri, "ttl": ttl}


@router.post("/close")
async def close(user: User = Depends(active_user)):
    payment_uri = await r.get(f"payment_uri:{user.id}")

    if payment_uri is not None:
        await r.delete(f"payment_uri:{user.id}")
        return Response(status_code=204)
    else:
        return "You haven't active payments"


@router.get("/prices")
async def checkout():
    return {
        "cpu": PRICE_CPU,
        "ram": PRICE_RAM,
        "disk": PRICE_DISK,
        "ipv4": PRICE_IPV4,
        "xmr": await xmr_course()
    }
