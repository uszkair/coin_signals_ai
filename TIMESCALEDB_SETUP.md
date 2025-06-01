# TimescaleDB Setup Guide

Ez az útmutató segít beállítani a TimescaleDB-t Docker-rel a crypto signals alkalmazáshoz.

## 🚀 Gyors Indítás

### 1. Docker Compose Indítása
```bash
# TimescaleDB és pgAdmin indítása
docker-compose up -d

# Logok ellenőrzése
docker-compose logs -f timescaledb
```

### 2. Backend Függőségek Telepítése
```bash
cd crypto_assistant_backend
pip install -r requirements.txt
```

### 3. Environment Fájl Beállítása
```bash
# Másold át a példa fájlt
cp .env.example .env

# Szerkeszd szükség szerint (alapértelmezett értékek működnek)
```

### 4. Backend Indítása
```bash
# A crypto_assistant_backend mappában
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Adatbázis Elérés

### TimescaleDB Kapcsolat
- **Host**: localhost
- **Port**: 5432
- **Database**: crypto_signals
- **Username**: crypto_user
- **Password**: crypto_password123

### pgAdmin Web Interface
- **URL**: http://localhost:8080
- **Email**: admin@crypto.local
- **Password**: admin123

## 🗄️ Adatbázis Struktúra

### Fő Táblák

#### 1. signals (Hypertable)
```sql
-- Signal adatok time-series optimalizációval
SELECT * FROM signals ORDER BY created_at DESC LIMIT 10;
```

#### 2. signal_performance (Hypertable)
```sql
-- Signal teljesítmény tracking
SELECT * FROM signal_performance WHERE result = 'profit';
```

#### 3. price_history (Hypertable)
```sql
-- Árfolyam történet backtesting-hez
SELECT * FROM price_history WHERE symbol = 'BTCUSDT' ORDER BY timestamp DESC;
```

### Analytics Views

#### Óránkénti Statisztikák
```sql
SELECT * FROM signals_hourly_stats 
WHERE hour >= NOW() - INTERVAL '24 hours';
```

#### Napi Statisztikák
```sql
SELECT * FROM signals_daily_stats 
WHERE day >= NOW() - INTERVAL '7 days';
```

## 🔧 Hasznos Lekérdezések

### Elmúlt 24 óra signáljai
```sql
SELECT symbol, signal_type, confidence, created_at 
FROM signals 
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### Legjobb teljesítményű signálok
```sql
SELECT s.symbol, s.signal_type, s.confidence, sp.profit_percentage
FROM signals s
JOIN signal_performance sp ON s.id = sp.signal_id
WHERE sp.result = 'profit'
ORDER BY sp.profit_percentage DESC
LIMIT 10;
```

### Symbol statisztikák
```sql
SELECT 
    symbol,
    COUNT(*) as total_signals,
    AVG(confidence) as avg_confidence,
    COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_signals,
    COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_signals
FROM signals 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY symbol
ORDER BY total_signals DESC;
```

## 🚨 Troubleshooting

### Docker Problémák
```bash
# Konténerek újraindítása
docker-compose down
docker-compose up -d

# Adatok törlése (VIGYÁZAT!)
docker-compose down -v
```

### Kapcsolódási Problémák
```bash
# Adatbázis elérhetőség tesztelése
docker exec -it crypto_signals_timescaledb psql -U crypto_user -d crypto_signals -c "SELECT version();"
```

### Backend Hibák
```bash
# Python függőségek újratelepítése
pip install -r requirements.txt --force-reinstall

# Adatbázis kapcsolat tesztelése
python -c "
from app.database import async_engine
import asyncio
async def test():
    async with async_engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection OK')
asyncio.run(test())
"
```

## 📈 Teljesítmény Optimalizáció

### Indexek Ellenőrzése
```sql
-- Aktív indexek listája
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('signals', 'signal_performance', 'price_history');
```

### Chunk Információk
```sql
-- TimescaleDB chunk-ok állapota
SELECT * FROM timescaledb_information.chunks;
```

### Retention Policy Ellenőrzése
```sql
-- Adatmegőrzési szabályok
SELECT * FROM timescaledb_information.jobs;
```

## 🔄 Backup & Restore

### Backup Készítése
```bash
# Teljes adatbázis backup
docker exec crypto_signals_timescaledb pg_dump -U crypto_user crypto_signals > backup.sql

# Csak signals tábla
docker exec crypto_signals_timescaledb pg_dump -U crypto_user -t signals crypto_signals > signals_backup.sql
```

### Restore
```bash
# Backup visszaállítása
docker exec -i crypto_signals_timescaledb psql -U crypto_user crypto_signals < backup.sql
```

## 🎯 API Endpoints

A backend futása után elérhető endpoints:

- **GET /api/signals?symbols=BTCUSDT,ETHUSDT** - Aktuális signálok
- **GET /api/signal/BTCUSDT** - Egy symbol signálja
- **GET /api/signal/history/BTCUSDT** - Signal történet
- **GET /api/signal/stats/BTCUSDT** - Symbol statisztikák
- **GET /api/signal/stats/all** - Összes statisztika

## 📱 Frontend Integráció

A frontend automatikusan használja az új database-alapú API-kat. Nincs szükség frontend módosításra.

## ✅ Ellenőrzés

1. **Docker**: `docker-compose ps` - minden szolgáltatás fut
2. **Database**: pgAdmin-ban kapcsolódás sikeres
3. **Backend**: `curl http://localhost:8000/api/signals?symbols=BTCUSDT`
4. **Frontend**: Dashboard betöltődik és mutatja a signálokat

Most már van egy teljes értékű TimescaleDB alapú crypto signals rendszered! 🚀