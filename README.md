# 📘 Felhasználói Felület Funkcionális Specifikáció – Crypto Trading Assistant

## 📁 Menüpontok

---

## 🧭 1. **Dashboard**

### 📊 Fő funkciók:
- **Interaktív Chart megjelenítés** (TradingView vagy saját gyertya chart):
  - Választható coin párok (pl. BTCUSDT, ETHUSDT, stb.)
  - Választható idővonal: 1m, 5m, 15m, 1h, 4h, 1d
  - Overlay: szignál nyilak (BUY/SELL), SL/TP vonalak

- **Főbb hírek szekció**:
  - Kripto hírek RSS feedből vagy API-ból
  - Minden hír pontozva jelenik meg (pl. 0–5 skálán), megbízhatóság vagy hatás alapján
  - Színkód: erőteljes hír (piros/zöld), gyenge hír (szürke)

- **Elmúlt 24 óra szignáljai** adott coin párokra:
  - Kis kártyákban vagy listában jelennek meg
  - Push értesítések (ha engedélyezve van a felhasználónál)
  - Jelzés: mikor volt BUY/SELL, melyik coin, milyen idővonalon

### 🛠 Bővítési javaslatok:
- „Értesítési preferenciák” beállítása: mikor kér push-t
- Kiemelt hírek hangelemzéssel (AI kulcsszó-kiemelés)
- Szignálok animált visszajátszása (Replay gomb)

---

## 📈 2. **Trading History**

### 📅 Időtáv:
- Alapértelmezett: **1 hónap**
- Bővíthető: dátumtartomány választóval

### 📋 Táblázatos nézet mezői:
- Belépési időpont
- Coin pár (pl. BTCUSDT)
- Idősáv (1h, 4h stb.)
- Belépési ár
- Stop Loss ár
- Take Profit ár
- Kilépési pont és kilépés ideje
- Profit vagy veszteség értéke (%) és USD-ben
- Rövid magyarázat: **belépés oka** (pl. "RSI 30 alatt + Hammer minta")

### 🔍 Szűrési lehetőségek:
- Coin pár szerint
- Dátumtartomány szerint
- Jelzés típusa (BUY/SELL)
- Eredmény típusa (TP/SL)
- Min. profit/score szerint

### 📤 Export lehetőség:
- CSV / XLS / PDF formátumban
- Automatikus jelentés generálás

### 📌 Bővítési ötlet:
- Vizsgálati mód: "Mi történt volna, ha belépek?" – missed opportunity overlay (vizuális visszateszt)
- Szignál megbízhatóság vizualizálása (confidence szint színnel vagy ikonokkal)
- Trade-replay: egy trade lejátszása gyertyánként animációval (idővonal slider)

---

## 💼 3. **Portfolio**

### 📊 Eredmény vizualizáció:
- **Diagramok:** napi profit, drawdown, win-rate, cumulative PnL
- **Heatmap:** mely coinpárok hozták a legtöbb nyereséget

### 🧾 Összefoglaló panel (Summary):
- Összes bevétel / veszteség (USD-ben és %-ban)
- Legjobb és legrosszabb trade
- Tradelések darabszáma, átlageredmény trade-enként
- Legaktívabb coin párok

### 📈 Bővítési ötletek:
- AI javaslat: mely coinpárokat kereskedted jól / rosszul
- "Mi lett volna ha" szimuláció (kihagyott szignálok hatása)
- Reálidejű portfólió követés (API csatlakozás Coinbase accounthoz – későbbi fázisban)
- Trade célkitűzések, célmegtartás (pl. heti 5% profit cél, vizualizálva)

---

Ez a struktúra lehetővé teszi, hogy a felhasználó **teljes képet kapjon múltbeli döntéseiről, napi szintű helyzetéről, és támaszkodhasson valós és AI-értékelt adatokra** a további lépésekhez.
