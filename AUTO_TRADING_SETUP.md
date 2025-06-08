# Automatikus Kereskedés Beállítási Útmutató

## 🚨 FONTOS FIGYELMEZTETÉS

**Az automatikus kereskedés valós pénzzel történik az éles Binance számládon!**
**Csak akkor használd, ha teljes mértékben megérted a kockázatokat!**

## 📋 Előfeltételek

### 1. Binance API Kulcsok Beállítása
Győződj meg róla, hogy a `.env` fájlban helyesen vannak beállítva:
```
BINANCE_API_KEY=your_real_api_key_here
BINANCE_API_SECRET=your_real_api_secret_here
```

### 2. API Kulcs Jogosultságok
A Binance API kulcsnak rendelkeznie kell:
- ✅ **Spot & Margin Trading** jogosultsággal
- ✅ **Read** jogosultsággal
- ❌ **Futures** jogosultság NEM szükséges (csak spot kereskedés)

### 3. IP Cím Engedélyezése
- Engedélyezd a szerver IP címét a Binance API beállításokban
- Vagy használj "Unrestricted" beállítást (kevésbé biztonságos)

## 🚀 Automatikus Kereskedés Aktiválása

### 1. Backend Indítása
```bash
cd crypto_assistant_backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Indítása
```bash
cd angular-frontend
npm start
```

### 3. Auto-Trading Bekapcsolása
1. Nyisd meg a dashboard-ot: http://localhost:4200
2. A fejlécben találod az **"Auto Trading"** kapcsolót
3. Kapcsold **BE** az automatikus kereskedést
4. Ellenőrizd hogy megjelenik a zöld "AKTÍV" státusz

## ⚙️ Automatikus Kereskedés Működése

### Monitoring Ciklus
- **Ellenőrzési gyakoriság**: 5 percenként
- **Figyelt szimbólumok**: BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, SOLUSDT
- **Minimum confidence**: 70%

### Szignál Generálás
1. **Technikai elemzés**: Gyertyaminták, trendek, RSI, MACD, Bollinger Bands
2. **AI/ML elemzés**: 23 feature-ös ML modell ensemble
3. **Kombinált döntés**: Technikai + AI eredmények átlagolása
4. **Risk management**: Napi limitek, pozíció méret ellenőrzés

### Automatikus Végrehajtás Feltételei
- ✅ Combined score > 0 (BUY) vagy < 0 (SELL)
- ✅ Confidence ≥ 70%
- ✅ Napi trade limit nem túllépve (max 10)
- ✅ Napi veszteség limit nem túllépve (max 5%)
- ✅ Nincs duplikált szignál (1 órán belül)
- ✅ AI és technikai elemzés nem mond ellent egymásnak

## 🛡️ Risk Management Beállítások

### Alapértelmezett Limitek
```
Max pozíció méret: 2% a portfólióból
Max napi kereskedések: 10
Napi veszteség limit: 5%
Minimum profit threshold: 0.5%
```

### Stop Loss és Take Profit
- **Stop Loss**: ATR * 0.5 távolságra
- **Take Profit**: Risk/Reward ratio 1:1.5
- **Automatikus pozíció zárás**: SL vagy TP elérésekor

## 📊 Monitoring és Ellenőrzés

### Real-time Státusz
- Dashboard fejléc: Auto-trading státusz
- Wallet egyenleg: Valós idejű frissítés
- Aktív pozíciók: Nyitott kereskedések listája

### API Endpoint-ok Ellenőrzéshez
```
GET /api/auto-trading/status - Auto-trading státusz
GET /api/auto-trading/history - Végrehajtott kereskedések
GET /api/auto-trading/performance - Teljesítmény metrikák
GET /api/trading/positions - Aktív pozíciók
GET /api/trading/wallet-balance - Wallet egyenleg
```

## 🚨 Vészhelyzeti Leállítás

### Frontend-ről
1. Dashboard fejléc: Auto-trading kapcsoló **KI**
2. Vagy használd az "Emergency Stop" gombot (ha van)

### API-ról
```bash
curl -X POST http://localhost:8000/api/auto-trading/emergency-stop
```

### Backend Leállítása
```bash
# Terminal-ban ahol a backend fut
Ctrl + C
```

## 📈 Teljesítmény Követés

### Napi Statisztikák
- Végrehajtott kereskedések száma
- Napi P&L (profit/loss)
- Aktív pozíciók száma
- Risk level (LOW/MEDIUM/HIGH)

### Hosszú Távú Tracking
- Összes auto-trading kereskedés
- Win rate (nyerő kereskedések aránya)
- Átlagos profit/veszteség
- Maximum drawdown

## ⚠️ Fontos Megjegyzések

### Kockázatok
- **Valós pénz**: Minden kereskedés valós USDT/BTC/ETH-vel történik
- **Piaci volatilitás**: Hirtelen árváltozások veszteségeket okozhatnak
- **Technikai hibák**: Szoftver vagy hálózati hibák befolyásolhatják a kereskedést
- **API limitek**: Binance API rate limitek befolyásolhatják a működést

### Ajánlások
- **Kezdj kis összeggel**: Tesztelj először kis pozíció méretekkel
- **Figyelj a limiteket**: Állíts be alacsony napi veszteség limiteket
- **Rendszeres ellenőrzés**: Nézd meg naponta a teljesítményt
- **Backup terv**: Legyen kéznél a vészhelyzeti leállítás módja

### Jogi Nyilatkozat
- **Saját felelősség**: A kereskedés minden kockázata a felhasználót terheli
- **Nincs garancia**: A szoftver nem garantál profitot
- **Tesztelés**: Alaposan teszteld testnet-en mielőtt éles használatba veszed

## 🔧 Hibaelhárítás

### Gyakori Problémák

#### "Auto-trading nem indul el"
- Ellenőrizd a Binance API kulcsokat
- Győződj meg róla hogy a backend fut
- Nézd meg a browser console-t hibákért

#### "API kulcs hibák"
- Ellenőrizd az API kulcs jogosultságokat
- Győződj meg róla hogy az IP cím engedélyezett
- Teszteld a kapcsolatot: `/api/trading/test-connection`

#### "Nem hajtódnak végre kereskedések"
- Ellenőrizd a szignál confidence szinteket
- Nézd meg a napi limiteket
- Győződj meg róla hogy vannak megfelelő szignálok

### Log Fájlok
- Backend logok: Terminal output ahol a backend fut
- Frontend logok: Browser Developer Tools Console
- Auto-trading logok: Backend terminal-ban "Auto-trading" prefix-szel

## 📞 Támogatás

Ha problémába ütközöl:
1. Ellenőrizd ezt az útmutatót
2. Nézd meg a log fájlokat
3. Teszteld a Binance API kapcsolatot
4. Használd a vészhelyzeti leállítást ha szükséges

**Emlékezz: Az automatikus kereskedés komoly kockázatokkal jár. Csak akkor használd, ha teljes mértékben megérted a működését és elfogadod a kockázatokat!**