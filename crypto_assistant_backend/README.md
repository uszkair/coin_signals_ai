# Crypto Assistant Backend

## 📘 Projekt dokumentáció

Ez a projekt egy kriptovaluta kereskedési asszisztens backend része, amely FastAPI-val készült.

### Funkciók

- Jelenlegi kereskedési jelzések generálása
- Kereskedési előzmények és backtesting
- Technikai indikátorok számítása
- Gyertyaformáció elemzés

## Telepítés és futtatás

### Előfeltételek
- Python 3.8+
- pip package manager
- PostgreSQL adatbázis (opcionális, TimescaleDB ajánlott)

### 1. Virtuális környezet létrehozása (ajánlott)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Függőségek telepítése
```bash
pip install -r requirements.txt
```

### 3. Környezeti változók beállítása
```bash
# Másold át a példa fájlt
cp .env.example .env

# Szerkeszd a .env fájlt a saját beállításaiddal
```

### 4. Adatbázis beállítása (opcionális)
```bash
# Ha használsz PostgreSQL/TimescaleDB-t
# Lásd: ../TIMESCALEDB_SETUP.md
```

### 5. Szerver indítása
```bash
# Fejlesztői mód (automatikus újraindítás)
uvicorn app.main:app --reload

# vagy specifikus host és port megadásával
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mód
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

A szerver elérhető lesz a `http://localhost:8000` címen.

### 6. API dokumentáció
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Elérhető parancsok

### Fejlesztés
```bash
# Szerver indítása fejlesztői módban
uvicorn app.main:app --reload

# Tesztek futtatása
pytest

# Tesztek futtatása verbose móddal
pytest -v
```

### Adatbázis migrációk (ha használod)
```bash
# Új migráció létrehozása
alembic revision --autogenerate -m "migration message"

# Migrációk futtatása
alembic upgrade head
```

## API Endpointok

### Szignálok
- `GET /api/signal/{symbol}?interval=1h&mode=swing` - Jelenlegi kereskedési szignál
- `GET /api/signals?symbols=BTCUSDT,ETHUSDT&interval=1h` - Több szignál egyszerre

### Kereskedési előzmények
- `GET /api/trade-history?coinPair=BTCUSDT&startDate=2024-05-01&endDate=2024-05-25` - Kereskedési előzmények

### Portfólió
- `GET /api/trade-stats?timeframe=30d` - Portfólió statisztikák

### Hírek
- `GET /api/news?symbol=BTCUSDT` - Hírek (fejlesztés alatt)

## Projekt struktúra
```
app/
├── main.py              # FastAPI alkalmazás belépési pont
├── database.py          # Adatbázis konfiguráció
├── models/              # Adatmodellek
│   ├── database_models.py
│   └── schema.py
├── routers/             # API route-ok
│   ├── signal.py
│   ├── history.py
│   ├── portfolio.py
│   └── news.py
├── services/            # Üzleti logika
│   ├── signal_engine.py
│   ├── candlestick_analyzer.py
│   ├── indicators.py
│   └── backtester.py
└── utils/               # Segédfunkciók
    └── price_data.py
```

## Környezeti változók (.env)
```
# Coinbase Advanced Trade API kulcsok
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret

# Coinbase API URL-ek
COINBASE_REST_API_URL=https://api.coinbase.com
COINBASE_WEBSOCKET_URL=wss://advanced-trade-ws.coinbase.com
COINBASE_SANDBOX_REST_API_URL=https://api.sandbox.coinbase.com
COINBASE_SANDBOX_WEBSOCKET_URL=wss://advanced-trade-ws.sandbox.coinbase.com

# Adatbázis (opcionális)
DATABASE_URL=postgresql://user:password@localhost/dbname

# Egyéb beállítások
DEBUG=True
LOG_LEVEL=INFO
```

## Hibakeresés

### Gyakori problémák
1. **Import hibák**: Ellenőrizd, hogy a virtuális környezet aktív-e
2. **Adatbázis kapcsolódási hiba**: Ellenőrizd a DATABASE_URL-t
3. **API kulcs hibák**: Ellenőrizd a Coinbase Advanced Trade API kulcsokat
   - Production API kulcs: https://www.coinbase.com/settings/api
   - Sandbox: Csak programból használható (nincs közvetlen UI)

### Logok
A szerver logjai a konzolon jelennek meg fejlesztői módban.

## Docker használat (opcionális)
```bash
# Ha van docker-compose.yml a projekt gyökerében
cd ..
docker-compose up backend
```

## Tesztelés
```bash
# Összes teszt futtatása
pytest

# Specifikus teszt fájl
pytest tests/test_signals.py

# Coverage riport
pytest --cov=app
```