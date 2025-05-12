SPECIFIKÁCIÓ – AI-alapú kriptokereskedési asszisztens alkalmazás
🎯 Célja
Létrehozni egy saját használatra optimalizált, de később termékként is értékesíthető, Python alapú AI-asszisztenst, amely:

különböző kriptopénz-párokat elemez,

technikai és fundamentális adatok alapján ad vételi / eladási / tartási jelzést,

vizuálisan modern, jól áttekinthető, reszponzív frontend felületen mutatja az adatokat,

időzített vagy manuális módon figyeli a piacot,

elősegíti skalpolást, swing és hosszútávú kereskedést egyaránt,

támogatja a későbbi kereskedés-automatizálást és SaaS modell kialakítását.

🧩 Alkalmazás architektúra
Backend: Python, FastAPI, ta, pandas, httpx, apscheduler

Frontend: React (Vite), Tailwind CSS, TradingView chart widget

Adatforrás: Binance API (klines, symbol info), CoinGecko / RSS hírek (később)

AI (később): LSTM / Random Forest modellek tanítása historikus adatokon

Adatstruktúra: JSON / CSV jelzésnaplózás, SQLite opcionálisan

🛠️ Fejlesztendő fő funkciók
🔁 1. Piaci adatok lekérése
Coin-párok listája (BTCUSDT, ETHUSDT, stb.)

Adatok több idősíkon: 1m, 5m, 15m, 1h, 4h, 1d

API: /marketdata/{symbol}?interval=1h

📊 2. Technikai indikátor számítás
RSI, EMA (20, 50), MACD, Bollinger Bands, Stochastic RSI

Signal logika: ha RSI < 30 és ár > EMA20 → BUY

Signal output struktúra:

json
Másolás
Szerkesztés
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "price": 43250.23,
  "rsi": 27.4,
  "ema20": 43180.12,
  "signal": "BUY",
  "entry": 43250.0,
  "stop_loss": 42900.0,
  "take_profit": 43900.0
}
📈 3. Frontend dashboard
Coin-választó (dropdown vagy kereső)

TradingView chart integráció

Idősík választó (1m, 5m, 1h, 1d)

Jelzések kártyákban: BUY / SELL / HOLD színekkel

Részletek gomb: RSI, MACD, kilépési pontok megtekintése

Realtime frissítés (1 percenként)

🧮 4. Scalp és swing mód elkülönítése
UI választó: “Scalping mode” vs. “Swing mode”

Backend logika kétféle feltételrendszerrel dolgozik

📬 5. Értesítések
Toast/jelzés frontend oldalon

Később: e-mail webhook vagy mobil push (opcionális)

🗞 6. Fundamentális hírek beépítése (később)
RSS vagy CoinGecko/NewsAPI hírfigyelés

NLP vagy ChatGPT/Claude elemzés alapján: pozitív/negatív hatás

📤 7. Jelzések naplózása
Backend menti JSON vagy CSV fájlba minden lekérést

UI-ban megjeleníthető a múltbeli jelzések listája

🧪 8. Backtesting modul (később)
Historikus adatok alapján újra játszható szimuláció

Eredmény: találati arány, profit szimuláció

🚫 Korlátok a jelenlegi verzióban
Kereskedési automatizálás: nincs (manuális döntéshozatal marad)

User login, több felhasználós SaaS: későbbi fázisban

AI előrejelző modell: külön lépésben integráljuk

💡 Javasolt első MVP lépések
✅ Backend API: marketdata + signal endpoint

✅ Frontend React dashboard: coin selection + jelzések

🔜 TradingView chart + timeframe választó

🔜 Entry/stop/profit értékek visszaküldése és megjelenítése

🔜 Jelzésnaplózás és CSV export

inditó parancsok:
AI: uvicorn main:app --reload