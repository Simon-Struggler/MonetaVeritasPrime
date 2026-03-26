from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
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
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.GATEWAY_URL}/auth/login", json={"username": username, "password": password})
        if resp.status_code == 200:
            data = resp.json()
            token = data["access_token"]
            response = RedirectResponse(url="/catalog", status_code=302)
            response.set_cookie(key="token", value=token, httponly=True)
            return response
        else:
            raise HTTPException(401, "Invalid credentials")

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
    return templates.TemplateResponse("catalog.html", {"request": request, "items": items})

@app.get("/collections", response_class=HTMLResponse)
async def collections(request: Request, token: str = Depends(get_token)):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.GATEWAY_URL}/collections", headers=headers)
        collection = resp.json() if resp.status_code == 200 else []
    return templates.TemplateResponse("collections.html", {"request": request, "collection": collection})

@app.get("/exchange", response_class=HTMLResponse)
async def exchange_page(request: Request, token: str = Depends(get_token)):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.GATEWAY_URL}/exchange/trades", headers=headers)
        trades = resp.json() if resp.status_code == 200 else []
    return templates.TemplateResponse("exchange.html", {"request": request, "trades": trades})

@app.get("/health")
def health():
    return {"status": "ok"}
