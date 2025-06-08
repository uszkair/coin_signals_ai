# Pozíció Méret Beállítások Útmutató

## 🎯 Áttekintés

Az alkalmazás most már teljes pozíció méret konfigurációval rendelkezik, amely lehetővé teszi a kereskedési összegek pontos beállítását mind manuális, mind automatikus kereskedéshez.

## 📍 Hol Találod a Beállításokat

### Frontend - Beállítások Oldal
- **URL**: http://localhost:4200/settings
- **Menü**: Sidebar → "Beállítások" (fogaskerék ikon)
- **Fül**: "Pozíció Méret" tab

### Beállítási Lehetőségek

#### 1. **Százalékos Mód** (Alapértelmezett)
- **Működés**: A portfólió százaléka alapján számítja a pozíció méretet
- **Beállítás**: 0.1% - 10% között
- **Alapértelmezett**: 2% (minden kereskedés max 2%-ot használ)
- **Példa**: $1000 portfólió, 2% = $20 per kereskedés

#### 2. **Fix USD Mód**
- **Működés**: Minden kereskedéshez ugyanaz a fix összeg
- **Beállítás**: $1 - $10,000 között
- **Példa**: $100 fix összeg minden kereskedéshez

## 🔧 Backend API Endpoint-ok

### Pozíció Méret Konfiguráció
```
GET  /api/trading/position-size-config     # Jelenlegi beállítások
POST /api/trading/position-size-config     # Beállítások frissítése
```

### Kockázatkezelési Beállítások
```
GET  /api/trading/config                   # Trading konfiguráció
POST /api/trading/config                   # Trading konfiguráció frissítése
```

## 📊 Beállítási Kategóriák

### 1. **Pozíció Méret Beállítások**
- **Mód választás**: Százalékos vagy Fix USD
- **Százalékos**: Maximum portfólió százalék
- **Fix USD**: Konkrét dollár összeg
- **Valós idejű számítás**: Példa összegek a jelenlegi portfólió alapján

### 2. **Kockázatkezelési Beállítások**
- **Napi trade limit**: Maximum kereskedések száma naponta (1-100)
- **Napi veszteség limit**: Maximum napi veszteség százalékban (0.1%-50%)
- **Maximum pozíció méret**: Portfólió százalékos limit (0.1%-20%)

### 3. **Jelenlegi Beállítások Áttekintés**
- **Aktív konfiguráció**: Jelenleg érvényes beállítások
- **Portfólió információ**: Wallet egyenleg és számított összegek
- **Frissítés**: Beállítások újratöltése

## 🚀 Használat

### Manuális Kereskedéshez
1. Menj a **Beállítások** oldalra
2. **Pozíció Méret** tab
3. Válaszd ki a módot (százalékos/fix USD)
4. Állítsd be az összeget
5. **Mentés**

### Automatikus Kereskedéshez
- Az auto-trading automatikusan használja a beállított pozíció méretet
- **Százalékos mód**: Confidence alapján finomhangolás
- **Fix USD mód**: Mindig ugyanaz az összeg

## ⚙️ Technikai Részletek

### Backend Implementáció
- **BinanceTrader osztály**: Pozíció méret számítás
- **Auto-trading scheduler**: Beállítások integrációja
- **API validáció**: Biztonságos értékhatárok

### Frontend Komponensek
- **SettingsComponent**: Teljes beállítási felület
- **TradingService**: API kommunikáció
- **Real-time számítások**: Azonnali visszajelzés

## 📈 Példa Forgatókönyvek

### Konzervatív Kereskedő
- **Mód**: Százalékos
- **Beállítás**: 1% maximum
- **$5000 portfólió**: $50 per kereskedés

### Agresszív Kereskedő
- **Mód**: Százalékos
- **Beállítás**: 5% maximum
- **$5000 portfólió**: $250 per kereskedés

### Fix Összegű Kereskedő
- **Mód**: Fix USD
- **Beállítás**: $200 fix
- **Minden kereskedés**: Pontosan $200

## 🛡️ Biztonsági Funkciók

### Validációk
- **Minimum/Maximum értékek**: Biztonságos tartományok
- **Portfólió ellenőrzés**: Nem lehet többet kereskedni mint ami van
- **Kockázati figyelmeztetések**: Magas kockázat jelzése

### Risk Management Integráció
- **Napi limitek**: Automatikus leállítás limitek elérésekor
- **Veszteség védelem**: Maximum napi veszteség limit
- **Pozíció méret védelem**: Maximum pozíció méret korlátozás

## 🔄 Frissítések és Szinkronizáció

### Real-time Frissítés
- **Wallet egyenleg**: Automatikus frissítés
- **Számított összegek**: Azonnali újraszámítás
- **Backend szinkronizáció**: Beállítások mentése

### Beállítások Perzisztencia
- **Backend tárolás**: Beállítások mentése adatbázisba
- **Auto-trading integráció**: Automatikus használat
- **Újraindítás után**: Beállítások megmaradnak

## 📞 Támogatás

### Gyakori Problémák
1. **Beállítások nem mentődnek**: Ellenőrizd a backend kapcsolatot
2. **Érvénytelen értékek**: Tartsd be a megadott tartományokat
3. **Számítások nem frissülnek**: Frissítsd a wallet egyenleget

### Debug Információ
- **Browser Console**: Hibák és API hívások
- **Backend Logs**: Pozíció méret számítások
- **API Response**: Beállítások mentési eredmények

## 🎉 Összefoglalás

A pozíció méret beállítások teljes kontrollt biztosítanak a kereskedési összegek felett:

✅ **Rugalmas módok**: Százalékos és fix USD opciók
✅ **Real-time számítások**: Azonnali visszajelzés
✅ **Biztonságos validáció**: Védelem a hibás beállítások ellen
✅ **Auto-trading integráció**: Automatikus használat
✅ **Kockázatkezelés**: Teljes risk management integráció
✅ **Felhasználóbarát UI**: Intuitív beállítási felület

Most már teljes kontrollt gyakorolhatsz a kereskedési összegek felett, mind manuális, mind automatikus kereskedés esetén!