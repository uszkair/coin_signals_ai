from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import signal, history, news, portfolio

app = FastAPI(title="Crypto Trading Assistant API")

# CORS beállítások (React frontend localhost:5173-hoz)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerek regisztrálása
app.include_router(signal.router, prefix="/api/signal", tags=["Signal"])
app.include_router(signal.router, prefix="/api/signals", tags=["Signals"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(history.router, prefix="/api", tags=["Trade History"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Crypto Trading Assistant API running."}
