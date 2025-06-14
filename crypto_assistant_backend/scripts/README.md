# Scripts és Maintenance Eszközök

Ez a mappa tartalmazza az alkalmazás karbantartási, teszt és segédeszközeit.

## 📁 Fájl Kategorizálás

### 🔧 **Scripts mappába tartozó fájlok:**

#### 🗄️ Adatbázis Karbantartás
- `clear_all_trading_history.py` - Teljes kereskedési előzmények törlése
- `clear_trading_data.py` - Kereskedési adatok törlése  
- `clear_trading_data_auto.py` - Automatikus adattörlés
- `quick_signal_check.py` - Gyors adatbázis állapot ellenőrzés
- `cleanup_unused_signals.py` - Nem kereskedett signalok törlése

#### 🔧 Migráció és Setup
- `create_database.py` - Adatbázis létrehozás
- `run_migration.py` - Adatbázis migrációk futtatása
- `run_settings_migration.py` - Beállítások migrációja
- `run_clear.py` - Törlési műveletek futtatása

#### 🧪 Tesztek
- `test_live_positions.py` - Live pozíciók API teszt (✅ már áthelyezve)
- `test_settings_api.py` - Beállítások API teszt
- `compare_positions.py` - Pozíciók összehasonlítása

### 📂 **Főkönyvtárban maradó fájlok:**

#### ⚙️ Konfigurációs fájlok
- `auto_trading_settings.json` - Auto-trading beállítások
- `requirements.txt` - Python függőségek
- `README.md` - Projekt dokumentáció

#### 🗃️ Adatbázis fájlok
- `crypto_signals.db` - SQLite adatbázis fájl (ha használt)

## 🚀 Használati útmutató

### Adatbázis karbantartás
```bash
# Gyors állapot ellenőrzés
python scripts/quick_signal_check.py

# Nem használt signalok törlése (dry-run)
python scripts/cleanup_unused_signals.py --dry-run

# Teljes előzmények törlése
python scripts/clear_all_trading_history.py
```

### Tesztek futtatása
```bash
# Live pozíciók API teszt
python scripts/test_live_positions.py

# Beállítások API teszt
python scripts/test_settings_api.py
```

### Migrációk
```bash
# Adatbázis setup
python scripts/create_database.py

# Migrációk futtatása
python scripts/run_migration.py
```

## ⚠️ Figyelmeztetések

- **Adattörlő szkriptek**: Mindig készíts biztonsági mentést!
- **Tesztek**: Csak fejlesztési környezetben futtasd
- **Migrációk**: Ellenőrizd az adatbázis állapotát előtte

## 📋 TODO - Fájlok áthelyezése

A következő fájlokat kell még áthelyezni a scripts mappába:

```bash
# Áthelyezendő fájlok:
move clear_all_trading_history.py scripts/
move clear_trading_data.py scripts/
move clear_trading_data_auto.py scripts/
move compare_positions.py scripts/
move create_database.py scripts/
move quick_signal_check.py scripts/
move run_clear.py scripts/
move run_migration.py scripts/
move run_settings_migration.py scripts/
move test_settings_api.py scripts/
```

**Megtartandó a főkönyvtárban:**
- `auto_trading_settings.json`
- `requirements.txt` 
- `README.md`
- `crypto_signals.db`