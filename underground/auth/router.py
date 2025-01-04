from uuid import uuid4
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from starlette.exceptions import HTTPException
from underground.config import REGISTRATION, TOKEN_EXPIRY_DAYS
from underground.database import r, execute, fetchone, fetchall
from underground.auth.utils import active_user


async def login(request: Request):
    form = await request.form()
    password = form.get("password")

    if not password:
        raise HTTPException(400, "The field password is required")

    # Check password
    user = await fetchone("SELECT * FROM user WHERE password = ?", (password,))

    if not user:
        raise HTTPException(401, "Invalid password")

    # Delete other auth tokens
    cursor = 0

    while True:
        cursor, keys = await r.scan(cursor, match=f"{user['id']}:auth:*", count=100)

        for key in keys:
            await r.delete(key)

        if cursor == 0:
            break

    # Create auth token
    cursor = 0

    while True:
        token = uuid4()
        cursor, keys = await r.scan(cursor, match=f"*:auth:{token}", count=100)

        if not keys:
            break

    await r.set(f"{user['id']}:auth:{token}", user["id"], ex=86400 * TOKEN_EXPIRY_DAYS)

    # Login
    servers = await fetchall("SELECT * FROM server WHERE user_id = ?", (user["id"],))
    url = '/' if not servers else "/dashboard"

    return RedirectResponse(url, 301, {
        "Content-Type": "application/x-www-form-urlencoded",
        "set-cookie": f"auth={token}; HttpOnly; Path=/; SameSite=lax; Max-Age={86400 * TOKEN_EXPIRY_DAYS};"
    })


async def register(request: Request):
    if not REGISTRATION:
        raise HTTPException(403, "Registration is disabled")

    form = await request.form()
    password1 = form.get("password1")
    password2 = form.get("password2")

    # Check password
    if not password1 or not password2:
        raise HTTPException(400, "The fields password1 and password2 are required")

    if len(password1) not in range(8, 21):
        raise HTTPException(400, "The password length must be 8-20 characters")

    if password1 != password2:
        raise HTTPException(400, "Passwords don't match")

    # Check user
    user = await fetchone("SELECT * FROM user WHERE password = ?", (password1,))

    if user:
        raise HTTPException(409, "User already exist")

    # Registration
    user_id = await execute("INSERT INTO user (password) VALUES (?)", (password1,))

    # Create token
    cursor = 0

    while True:
        token = uuid4()
        cursor, keys = await r.scan(cursor, match=f"*:auth:{token}", count=100)

        if not keys:
            break

    await r.set(f"{user_id}:auth:{token}", user_id, ex=86400 * TOKEN_EXPIRY_DAYS)

    return RedirectResponse('/', 301, {
        "Content-Type": "application/x-www-form-urlencoded",
        "set-cookie": f"auth={token}; HttpOnly; Path=/; SameSite=lax; Max-Age={86400 * TOKEN_EXPIRY_DAYS};"
    })


async def logout(request: Request):
    _ = await active_user(request)

    return RedirectResponse('/', 301, {
        "Content-Type": "application/x-www-form-urlencoded",
        "set-cookie": 'auth=""; HttpOnly; Max-Age=0; Path=/; SameSite=lax;'
    })


auth_router = [
    Route("/login", login, methods=["POST"]),
    Route("/register", register, methods=["POST"]),
    Route("/logout", logout, methods=["POST"])
]
