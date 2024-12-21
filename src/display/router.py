from datetime import timedelta
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from src.database import Database, r
from src.config import REGISTRATION, VDS_DAYS, VDS_MAX_PAYED_DAYS, PAYMENT_TIME
from src.auth.utils import active_user, active_user_opt
from src.server.vds import vds_status
from src.server.utils import request_vds
from src.payment.payments import payment_request
from src.payment.utils import check_active_payment, check_payment_limit, xmr_course
from src.display.utils import templates, t_error, t_checkout, get_captcha_base64, draw_qrcode


async def index(request: Request):
    user = await active_user_opt(request)

    if user:
        async with Database() as db:
            servers = await db.fetchall("SELECT * FROM server WHERE user_id = ?", (user["id"],))

        active_servers = [server for server in servers if server["is_active"]]
    else:
        active_servers = None

    course = await xmr_course()

    async with Database() as db:
        vdss = await db.fetchall("SELECT * FROM vds")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "course": course,
        "vdss": vdss,
        "servers": active_servers
    })


async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


async def register(request: Request):
    if not REGISTRATION:
        return await t_error(request, 400, "Registration is disabled")

    captcha_id, captcha_base64 = await get_captcha_base64()

    return templates.TemplateResponse("register.html", {
        "request": request, "captcha_id": captcha_id, "captcha_base64": captcha_base64
    })


async def reset_password(request: Request):
    _ = await active_user(request)

    return templates.TemplateResponse("change-password.html", {"request": request})


async def delete_account(request: Request):
    _ = await active_user(request)

    return templates.TemplateResponse("delete-account.html", {"request": request})


async def dashboard(request: Request):
    user = await active_user(request)
    course = await xmr_course()

    async with Database() as db:
        servers = await db.fetchall("SELECT * FROM server WHERE user_id = ?", (user["id"],))

    active_servers = [server for server in servers if server["is_active"]]
    statuses = []

    if not active_servers:
        return RedirectResponse('/', status_code=301)

    for server in active_servers:
        async with Database() as db:
            node = await db.fetchone("SELECT * FROM node WHERE id = ?", (server["node_id"],))

        status = await vds_status(server["id"], node["ip"])

        if not status["ipv4"]:
            status["ipv4"] = '-'

        if not status["ipv6"]:
            status["ipv6"] = '-'

        statuses.append(status)

    servers_and_statuses = zip(active_servers, statuses)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "course": course,
        "servers_and_statuses": servers_and_statuses
    })


async def promo(request: Request):
    _ = await active_user(request)

    return templates.TemplateResponse("promo.html", {"request": request})


async def faq(request: Request):
    user = await active_user_opt(request)
    active_servers = []
    course = await xmr_course()

    if user:
        async with Database() as db:
            servers = await db.fetchall("SELECT * FROM server WHERE user_id = ?", (user["id"],))

        active_servers = [server for server in servers if server["is_active"]]

    return templates.TemplateResponse("faq.html", {
        "request": request,
        "user": user,
        "course": course,
        "servers": active_servers
    })


async def install(server_id: int, request: Request):
    _ = await active_user(request)

    return templates.TemplateResponse("install.html", {
        "request": request,
        "server_id": server_id
    })


async def vnc(server_id: int, request: Request):
    _ = await active_user(request)

    return templates.TemplateResponse("vnc.html", {
        "request": request,
        "server_id": server_id
    })


async def buy(product_id: int, request: Request):
    user = await active_user(request)

    # Check if user have active payment
    cap = await check_active_payment(user["id"])

    if cap:
        return await t_checkout(request, cap["qrcode"], cap["payment_uri"], cap["ttl"])

    # Check user's payment limit
    cpl = await check_payment_limit(user["id"])

    if cpl:
        return await t_error(request, 400, "You can make only 3 payment requests per day")

    server_id = await request_vds(product_id, user)

    # Make payment request and return it uri
    await r.set(f"inactive_server:{server_id}", server_id, ex=60 * PAYMENT_TIME)

    payment_data = await payment_request("buy", server_id)
    qrcode = await draw_qrcode(payment_data["payment_uri"])

    return await t_checkout(request, qrcode, payment_data["payment_uri"], payment_data["ttl"])


async def pay(server_id: int, request: Request):
    user = await active_user(request)

    # Check server
    async with Database() as db:
        server = await db.fetchone("SELECT * FROM server WHERE id = ?", (server_id,))

    if not server or server["user_id"] != user["id"]:
        return await t_error(request, 400, "Invalid server")
 
    # Check if user have active payment
    cap = await check_active_payment(user["id"])

    if cap:
        return await t_checkout(request, cap["qrcode"], cap["payment_uri"], cap["ttl"])

    # Check user's payment limit
    cpl = await check_payment_limit(user["id"])

    if cpl:
        return await t_error(request, 400, "You can make only 3 payment requests per day")

    # Check expiring date
    if server["end_at"] - server["start_at"] > timedelta(days=VDS_MAX_PAYED_DAYS - VDS_DAYS):
        return await t_error(request, 400, f"You can't pay for more than {VDS_MAX_PAYED_DAYS} days")

    # Make payment request and return it uri
    payment_data = await payment_request("pay", server_id)
    qrcode = await draw_qrcode(payment_data["payment_uri"])

    return await t_checkout(request, qrcode, payment_data["payment_uri"], payment_data["ttl"])


async def upgrademenu(server_id: int, request: Request):
    _ = await active_user(request)

    async with Database() as db:
        server = await db.fetchone("SELECT * FROM server WHERE id = ?", (server_id,))
        vdss = await db.fetchall("SELECT * FROM vds")

    vdss = [vds for vds in vdss if vds["id"] > server["vds_id"]]

    if not vdss:
        return await t_error(request, 400, "Your VDS is already fully upgraded")

    return templates.TemplateResponse("upgrade.html", {
        "request": request,
        "vdss": vdss,
        "server_id": server_id
    })


async def upgrade(server_id: int, product_id: int, request: Request):
    user = await active_user(request)

    # Check server
    async with Database() as db:
        server = await db.fetchone("SELECT * FROM server WHERE id = ?", (server_id,))

    if not server or not server["is_active"] or server["user_id"] != user["id"] or server["vds_id"] >= product_id:
        return await t_error(request, 400, "Invalid server")

    # Check if user have active payment
    cap = await check_active_payment(user["id"])

    if cap:
        return await t_checkout(request, cap["qrcode"], cap["payment_uri"], cap["ttl"])

    # Check user's payment limit
    cpl = await check_payment_limit(user["id"])

    if cpl:
        return await t_error(request, 400, "You can make only 3 payment requests per day")

    # Validate product id
    async with Database() as db:
        upgrade_vds = await db.fetchone("SELECT * FROM vds WHERE id = ?", (product_id,))

    if not upgrade_vds:
        return await t_error(request, 400, "This product doesn't exist")

    # Check availability of resources
    async with Database() as db:
        node = await db.fetchone("SELECT * FROM node WHERE id = ?", (server["node_id"],))
        server_vds = await db.fetchone("SELECT * FROM vds WHERE id = ?", (server["vds_id"],))
        nodes = await db.fetchall(
            "SELECT * FROM node WHERE cores_available >= ? AND ram_available >= ? AND disk_size_available >= ?",
            (upgrade_vds["cores"], upgrade_vds["ram"], upgrade_vds["disk_size"])
        )

    if nodes:
        if node in nodes:
            async with Database() as db:
                await db.execute(
                    "UPDATE node SET cores_available = ?, ram_available = ?, disk_size_available = ? WHERE id = ?",
                    (
                        node["cores_available"] - upgrade_vds["cores"] + server_vds["cores"],
                        node["ram_available"] - upgrade_vds["ram"] + server_vds["ram"],
                        node["disk_size_available"] - upgrade_vds["disk_size"] + server_vds["disk_size"],
                        server["node_id"]
                    )
                )
        else:
            dst_node = nodes[0]
            await r.set(f"node_to_migrate:{server_id}", dst_node["id"])

            async with Database() as db:
                await db.execute(
                    "UPDATE node SET cores_available = ?, ram_available = ?, disk_size_available = ? WHERE id = ?",
                    (
                        dst_node["cores_available"] - upgrade_vds["cores"] + server_vds["cores"],
                        dst_node["ram_available"] - upgrade_vds["ram"] + server_vds["ram"],
                        dst_node["disk_size_available"] - upgrade_vds["disk_size"] + server_vds["disk_size"],
                        dst_node["id"]
                    )
                )

        async with Database() as db:
            await db.execute("UPDATE server SET in_upgrade = 1 WHERE id = ?", (server["id"],))

        # Make payment request and return it uri
        await r.set(f"upgrade_server:{server_id}", server_id, ex=60 * PAYMENT_TIME)
        await r.set(f"unupgraded_server:{server_id}", upgrade_vds["id"])

        payment_data = await payment_request("upgrade", server_id, product_id)
        qrcode = await draw_qrcode(payment_data["payment_uri"])

        return await t_checkout(request, qrcode, payment_data["payment_uri"], payment_data["ttl"])
    else:
        return await t_error(request, 503, "We haven't available resources")


router = [
    Route("/", index, methods=["GET"]),
    Route("/login", login, methods=["GET"]),
    Route("/register", register, methods=["GET"]),
    Route("/reset-password", reset_password, methods=["GET"]),
    Route("/delete-account", delete_account, methods=["GET"]),
    Route("/dashboard", dashboard, methods=["GET"]),
    Route("/promo", promo, methods=["GET"]),
    Route("/faq", faq, methods=["GET"]),
    Route("/install/{server_id}", install, methods=["GET"]),
    Route("/vnc/{server_id}", vnc, methods=["GET"]),
    Route("/buy/{product_id}", buy, methods=["GET"]),
    Route("/pay/{server_id}", pay, methods=["GET"]),
    Route("/upgrademenu/{server_id}", upgrademenu, methods=["GET"]),
    Route("/upgrade/{server_id}", upgrade, methods=["GET"])
]
