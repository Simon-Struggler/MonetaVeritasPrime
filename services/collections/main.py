from fastapi import FastAPI
from api import collections
from database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Collections Service")
app.include_router(collections.router)

@app.get("/health")
def health():
    return {"status": "ok"}