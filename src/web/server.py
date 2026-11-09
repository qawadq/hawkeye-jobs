"""
FastAPI application server.

Desktop mode keeps the original localhost + per-launch token guard.
Hosted mode adds one private, password-protected dashboard with signed,
short-lived HttpOnly cookies. No multi-user accounts are created.
"""
import hashlib
import hmac
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from web.api import router

STATIC_DIR = Path(__file__).resolve().parent / "static"
EVENTS_PATH = "/api/events"
AUTH_STATUS_PATH = "/api/auth/status"
AUTH_LOGIN_PATH = "/api/auth/login"
AUTH_LOGOUT_PATH = "/api/auth/logout"
SESSION_TTL_SECONDS = 12 * 60 * 60
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_ATTEMPTS = 5

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self'; "
        "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
}


def _token_ok(request: Request, token: str) -> bool:
    supplied = request.headers.get("x-hawkeye-token")
    if supplied is None and request.url.path == EVENTS_PATH:
        supplied = request.query_params.get("token")
    return bool(supplied) and hmac.compare_digest(supplied.encode(), token.encode())


def _host_allowed(host_header: str | None, allowed_hosts: set) -> bool:
    try:
        host = (urlsplit("//" + (host_header or "")).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    if not host:
        return False
    for item in allowed_hosts:
        candidate = str(item).strip().lower().rstrip(".")
        if not candidate:
            continue
        if candidate.startswith(".") and host.endswith(candidate) and host != candidate[1:]:
            return True
        if host == candidate:
            return True
    return False


def _session_signature(issued: int, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), str(issued).encode("ascii"), hashlib.sha256).hexdigest()


def _valid_session(value: str | None, secret: str, now: int | None = None) -> bool:
    if not value:
        return False
    try:
        issued_text, supplied = value.split(".", 1)
        issued = int(issued_text)
    except (ValueError, TypeError):
        return False
    current = int(time.time()) if now is None else int(now)
    if issued > current + 60 or current - issued > SESSION_TTL_SECONDS:
        return False
    expected = _session_signature(issued, secret)
    return hmac.compare_digest(supplied, expected)


def create_app(
    *,
    token: str | None,
    allowed_hosts: set,
    services,
    static_dir: Path = STATIC_DIR,
    web_password: str | None = None,
    session_secret: str | None = None,
    cookie_secure: bool = True,
) -> FastAPI:
    remote_auth = web_password is not None or session_secret is not None
    if remote_auth:
        if not web_password or not session_secret:
            raise ValueError("Hosted authentication requires both web_password and session_secret")
        if len(web_password) < 12:
            raise ValueError("HAWKEYE_WEB_PASSWORD must contain at least 12 characters")
        if len(session_secret) < 32:
            raise ValueError("HAWKEYE_WEB_SESSION_SECRET must contain at least 32 characters")
    elif not token:
        raise ValueError("Local mode requires a per-launch API token")

    cookie_name = "__Host-hawkeye_session" if cookie_secure else "hawkeye_session"
    attempts: dict[str, deque] = defaultdict(deque)
    attempts_lock = threading.Lock()

    def authenticated(request: Request) -> bool:
        if not remote_auth:
            return False
        return _valid_session(request.cookies.get(cookie_name), session_secret)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.services = services
    app.state.hosted = remote_auth

    if remote_auth:
        @app.get(AUTH_STATUS_PATH)
        def auth_status(request: Request):
            return {"required": True, "authenticated": authenticated(request)}

        @app.post(AUTH_LOGIN_PATH)
        async def auth_login(request: Request):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            with attempts_lock:
                history = attempts[client_ip]
                while history and now - history[0] >= LOGIN_WINDOW_SECONDS:
                    history.popleft()
                retry_after = LOGIN_WINDOW_SECONDS - int(now - history[0]) if len(history) >= LOGIN_MAX_ATTEMPTS else 0
            if retry_after > 0:
                return JSONResponse({"error": "login_rate_limited"}, status_code=429,
                                    headers={"Retry-After": str(max(1, retry_after))})
            try:
                body = await request.json()
            except Exception:
                body = {}
            supplied = body.get("password", "") if isinstance(body, dict) else ""
            if not isinstance(supplied, str) or not hmac.compare_digest(supplied, web_password):
                with attempts_lock:
                    history = attempts[client_ip]
                    while history and now - history[0] >= LOGIN_WINDOW_SECONDS:
                        history.popleft()
                    history.append(now)
                return JSONResponse({"error": "invalid_password"}, status_code=401)
            with attempts_lock:
                attempts.pop(client_ip, None)
            issued = int(now)
            value = f"{issued}.{_session_signature(issued, session_secret)}"
            response = JSONResponse({"ok": True})
            response.set_cookie(
                cookie_name, value, max_age=SESSION_TTL_SECONDS, httponly=True,
                secure=cookie_secure, samesite="strict", path="/",
            )
            return response

        @app.post(AUTH_LOGOUT_PATH)
        def auth_logout():
            response = Response(status_code=204)
            response.delete_cookie(cookie_name, path="/", secure=cookie_secure, httponly=True,
                                   samesite="strict")
            return response

        @app.get("/healthz")
        def healthz():
            return {"ok": True}

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if remote_auth and not _host_allowed(request.headers.get("host"), allowed_hosts):
            response = JSONResponse({"error": "forbidden"}, status_code=403)
        elif not remote_auth and request.headers.get("host") not in allowed_hosts:
            response = JSONResponse({"error": "forbidden"}, status_code=403)
        elif remote_auth:
            public_paths = {
                "/", "/index.html", "/login.html", "/login.js", "/login.css", "/icon.svg",
                "/api/auth/status", "/api/auth/login", "/healthz",
            }
            public = path in public_paths
            is_authenticated = authenticated(request)
            if path == AUTH_LOGOUT_PATH and not is_authenticated:
                response = JSONResponse({"error": "authentication_required"}, status_code=401)
            elif path.startswith("/api/") and not public and not is_authenticated:
                response = JSONResponse({"error": "authentication_required"}, status_code=401)
            elif not path.startswith("/api/") and not public and not is_authenticated:
                response = JSONResponse({"error": "authentication_required"}, status_code=401)
            elif path in ("/", "/index.html") and not is_authenticated:
                response = FileResponse(Path(static_dir) / "login.html")
            else:
                response = await call_next(request)
        elif path.startswith("/api/") and not _token_ok(request, token):
            response = JSONResponse({"error": "forbidden"}, status_code=403)
        else:
            response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        errors = {}
        for err in exc.errors():
            loc = err.get("loc") or ()
            field = str(loc[-1]) if len(loc) > 1 else "body"
            errors[field] = "invalid"
        return JSONResponse({"errors": errors or {"body": "invalid"}}, status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        if isinstance(exc.detail, dict):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
        code = "not_found" if exc.status_code == 404 else f"http_{exc.status_code}"
        return JSONResponse({"error": code}, status_code=exc.status_code, headers=exc.headers)

    app.include_router(router, prefix="/api")
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    return app
