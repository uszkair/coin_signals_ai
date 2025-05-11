from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS engedélyezés Angular frontendhez
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # vagy ["*"] fejlesztéshez
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... a további endpointok, például:
from services.market_data import get_coin_signal_multi_timeframe

@app.get("/signal-mtf/{symbol}")
async def signal_mtf(symbol: str):
    return await get_coin_signal_multi_timeframe(symbol)
