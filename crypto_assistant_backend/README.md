# Crypto Assistant Backend

## 📘 Projekt dokumentáció

Ez a projekt egy kriptovaluta kereskedési asszisztens backend része, amely FastAPI-val készült.

### Funkciók

- Jelenlegi kereskedési jelzések generálása
- Kereskedési előzmények és backtesting
- Technikai indikátorok számítása
- Gyertyaformáció elemzés

### Telepítés

```bash
pip install -r requirements.txt
```

### Futtatás

```bash
uvicorn app.main:app --reload
```

### API Endpointok

- `/api/signal` - Jelenlegi kereskedési jelzések
- `/api/history` - Kereskedési előzmények
- `/api/news` - Hírek (későbbre tervezve)
- `/api/portfolio` - Portfólió kezelés (későbbre tervezve)