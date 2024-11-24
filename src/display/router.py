import base64
from random import choice, randint
from datetime import timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from captcha.image import ImageCaptcha
from src.database import r
from src.config import REGISTRATION, PRODUCTS
from src.user.models import User
from src.auth.utils import active_user, active_user_opt
from src.server.crud import crud_read_servers, crud_read_server
from src.server.vps import vps_status
from src.server.utils import request_vps
from src.payment.payments import payment_request
from src.payment.utils import check_active_payment, check_payment_limit, draw_qrcode, xmr_course
from src.display.utils import templates, t_error

router = APIRouter()


@router.get("/")
async def index(request: Request, user: User = Depends(active_user_opt)):
    course = await xmr_course()

    if user is not None:
        servers = await crud_read_servers(user.id)
        servers = [server for server in servers if server.is_active]
    else:
        servers = None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "server": servers,
        "course": course,
        "products": PRODUCTS["vps"]
    })


@router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register")
async def register(request: Request):
    if not REGISTRATION:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "msg1": "Bad Request",
            "msg2": "Registration is disabled"
        })

    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    text = ''.join(choice(chars) for _ in range(randint(5, 7)))
    captcha_id = randint(10000000, 99999999)

    image = ImageCaptcha(width=218, height=50)
    captcha = base64.b64encode(image.generate(text).getvalue()).decode("utf-8")

    await r.set(f"captcha:{captcha_id}", text, ex=90)

    return templates.TemplateResponse("register.html", {
        "request": request, "captcha_id": captcha_id, "captcha": captcha
    })


@router.get("/reset-password")
async def change_password(request: Request, _: User = Depends(active_user)):
    return templates.TemplateResponse("change-password.html", {"request": request})


@router.get("/delete-account")
async def delete_account(request: Request, _: User = Depends(active_user)):
    return templates.TemplateResponse("delete-account.html", {"request": request})


@router.get("/dashboard")
async def dashboard(request: Request, user: User = Depends(active_user)):
    course = await xmr_course()
    servers = await crud_read_servers(user.id)
    servers = [server for server in servers if server.is_active]

    if not servers:
        return RedirectResponse('/', status_code=301)

    statuses = [await vps_status(server.id) for server in servers]
    servers_and_statuses = zip(servers, statuses)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "course": course,
        "servers_and_statuses": servers_and_statuses
    })


@router.get("/promo")
async def promo(request: Request, _: User = Depends(active_user)):
    return templates.TemplateResponse("promo.html", {"request": request})


@router.get("/blog")
async def blog(request: Request, user: User = Depends(active_user_opt)):
    course = await xmr_course()

    return templates.TemplateResponse("blog.html", {
        "request": request,
        "user": user,
        "course": course
    })


@router.get("/buy/{product_id}")
async def buy(product_id: int, request: Request, user: User = Depends(active_user)):
    # Check if user have active payment
    cap = await check_active_payment(user.id)

    if cap is not None:
        return templates.TemplateResponse("checkout.html", {
            "request": request,
            "qrcode": cap["qrcode"],
            "uri": cap["payment_uri"],
            "ttl": cap["ttl"]
        })

    # Check user's payment limit
    cpl = await check_payment_limit(user.id)

    if cpl:
        return await t_error(request, 400, "You can make only 3 payment requests per day")

    server_id = await request_vps(product_id, user)

    # Make payment request and return it uri
    await r.set(f"inactive_server:{server_id}", server_id, ex=900)

    payment_data = await payment_request("buy", server_id)
    qrcode = await draw_qrcode(payment_data["payment_uri"])

    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "qrcode": qrcode,
        "uri": payment_data["payment_uri"],
        "ttl": payment_data["ttl"]
    })


@router.get("/pay/{server_id}")
async def pay(server_id: int, request: Request, user: User = Depends(active_user)):
    # Check server
    server = await crud_read_server(server_id)

    if server is None or server.user_id != user.id:
        return await t_error(request, 400, "Invalid server")
 
    # Check if user have active payment
    cap = await check_active_payment(user.id)

    if cap is not None:
        return templates.TemplateResponse("checkout.html", {
            "request": request,
            "qrcode": cap["qrcode"],
            "uri": cap["payment_uri"],
            "ttl": cap["ttl"]
        })

    # Check user's payment limit
    cpl = await check_payment_limit(user.id)

    if cpl:
        return await t_error(request, 400, "You can make only 3 payment requests per day")

    # Check expiring date
    server = await crud_read_server(server_id)

    if server.end_at - server.start_at > timedelta(days=10):
        return await t_error(request, 400, "You can't pay for more than 40 days")

    # Make payment request and return it uri
    payment_data = await payment_request("pay", server_id)
    qrcode = await draw_qrcode(payment_data["payment_uri"])

    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "qrcode": qrcode,
        "uri": payment_data["payment_uri"],
        "ttl": payment_data["ttl"]
    })


@router.get("/upgrademenu/{server_id}")
async def upgrade(server_id: int, request: Request, _: User = Depends(active_user)):
    server = await crud_read_server(server_id)
    products = {key: value for key, value in PRODUCTS["vps"].items() if int(key) > server.vps_id}

    return templates.TemplateResponse("upgrade.html", {
        "request": request,
        "products": products,
        "server_id": server_id
    })


@router.get("/install/{server_id}")
async def install(server_id: int, request: Request, _: User = Depends(active_user)):
    return templates.TemplateResponse("install.html", {
        "request": request,
        "server_id": server_id
    })


@router.get("/vnc/{server_id}")
async def vnc(server_id: int, request: Request, _: User = Depends(active_user)):
    return templates.TemplateResponse("vnc.html", {
        "request": request,
        "server_id": server_id
    })
