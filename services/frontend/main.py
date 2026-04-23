from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
from jose import jwt
from config import settings

app = FastAPI(title="Frontend Service")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

async def parse_auth_body(request: Request):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    form = await request.form()
    return dict(form)

@app.post("/login")
async def login(request: Request):
    body = await parse_auth_body(request)
    username = body.get("username")
    password = body.get("password")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.GATEWAY_URL}/auth/login",
            json={"username": username, "password": password},
        )
        data = resp.json()
        if resp.status_code == 200:
            token = data["access_token"]
            if "application/json" in request.headers.get("content-type", ""):
                response = JSONResponse({"status": "ok"})
            else:
                response = RedirectResponse(url="/catalog", status_code=302)
            response.set_cookie(key="token", value=token, httponly=True)
            return response
        raise HTTPException(resp.status_code, data.get("detail", "Invalid credentials"))

@app.post("/register")
async def register(request: Request):
    body = await parse_auth_body(request)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.GATEWAY_URL}/auth/register",
            json={
                "username": body.get("username"),
                "email": body.get("email"),
                "password": body.get("password"),
            },
        )
        if resp.status_code == 200:
            return JSONResponse({"status": "ok"})
        data = resp.json()
        raise HTTPException(resp.status_code, data.get("detail", "Registration failed"))

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("token")
    return response

def get_token(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    return token

@app.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request, token: str = Depends(get_token)):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.GATEWAY_URL}/catalog/items", headers=headers)
        items = resp.json() if resp.status_code == 200 else []
    return templates.TemplateResponse(request, "catalog.html", {"request": request, "items": items})

@app.get("/collections", response_class=HTMLResponse)
async def collections(request: Request, token: str = Depends(get_token)):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.GATEWAY_URL}/collections", headers=headers)
        collection = resp.json() if resp.status_code == 200 else []
    return templates.TemplateResponse(request, "collections.html", {"request": request, "collection": collection})

@app.get("/exchange", response_class=HTMLResponse)
async def exchange_page(request: Request, token: str = Depends(get_token)):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.GATEWAY_URL}/exchange/trades", headers=headers)
        trades = resp.json() if resp.status_code == 200 else []
    return templates.TemplateResponse(request, "exchange.html", {"request": request, "trades": trades})

@app.get("/health")
def health():
    return {"status": "ok"}
