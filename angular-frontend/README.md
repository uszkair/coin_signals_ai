# Coin Signals AI - Frontend

Angular 17+ frontend alkalmazás AI-alapú kereskedési szignálokhoz.

## Technológiai stack

- **Angular 17+** - Modern Angular framework
- **PrimeNG** - UI komponens könyvtár
- **Tailwind CSS** - Utility-first CSS framework
- **RxJS** - Reaktív programozás
- **TypeScript** - Típusos JavaScript

## Funkciók

### 1. Dashboard (/dashboard)
- Coinpár kiválasztó dropdown
- Időintervallum beállítás (1m, 5m, 15m, 1h, 4h, 1d)
- Jelenlegi szignálkártya (BUY/SELL/HOLD)
- Entry price, SL/TP, Pattern, Trend, Confidence megjelenítés
- Elmúlt 24 óra szignáljai táblázat
- Hírek timeline

### 2. Történeti kereskedés (/history)
- Kereskedési előzmények táblázata
- Szűrők: coin, dátum, típus
- Export CSV funkcionalitás
- Részletes profit/veszteség adatok

### 3. Portfólió (/portfolio)
- Összesítő kártyák
- Profit idővonalon (line chart)
- Profit coinonként (pie chart)
- Részletes teljesítmény táblázat

## Telepítés és futtatás

### Előfeltételek
- Node.js 18+
- npm vagy yarn (ajánlott: yarn)

### 1. Projekt klónozása
```bash
git clone <repository-url>
cd angular-frontend
```

### 2. Függőségek telepítése
```bash
# Yarn használatával (ajánlott)
yarn install

# vagy npm használatával
npm install
```

### 3. Fejlesztői szerver indítása
```bash
# Yarn használatával
yarn start

# vagy npm használatával
npm start

# vagy Angular CLI-vel közvetlenül
ng serve
```

Az alkalmazás elérhető lesz a `http://localhost:4200` címen.

### 4. Elérhető parancsok

#### Fejlesztés
```bash
# Fejlesztői szerver indítása
yarn start
# vagy
npm start

# Fejlesztői szerver indítása watch móddal
yarn watch
# vagy
npm run watch
```

#### Build és tesztelés
```bash
# Production build
yarn build
# vagy
npm run build

# Unit tesztek futtatása
yarn test
# vagy
npm test
```

#### Angular CLI parancsok
```bash
# Új komponens generálása
ng generate component components/my-component --standalone

# Új szolgáltatás generálása
ng generate service services/my-service

# Angular CLI segítség
ng help
```

## API integráció

A frontend a következő backend API végpontokat használja:

- `GET /api/signal/{symbol}?interval=1h&mode=swing` - Jelenlegi szignál
- `GET /api/signals?symbols=BTCUSDT,ETHUSDT&interval=1h` - Több szignál
- `GET /api/news?symbol=BTCUSDT` - Hírek
- `GET /api/trade-history?coinPair=BTCUSDT&startDate=2024-05-01&endDate=2024-05-25` - Kereskedési előzmények
- `GET /api/trade-stats?timeframe=30d` - Portfólió statisztikák

## Projekt struktúra

```
src/
├── app/
│   ├── components/          # Újrafelhasználható komponensek
│   │   └── sidebar/         # Navigációs sidebar
│   ├── pages/               # Oldal komponensek
│   │   ├── dashboard/       # Dashboard oldal
│   │   ├── history/         # Történeti kereskedés
│   │   └── portfolio/       # Portfólió áttekintés
│   ├── services/            # Angular szolgáltatások
│   │   ├── signal.service.ts    # Szignál API hívások
│   │   ├── history.service.ts   # Történeti adatok
│   │   └── portfolio.service.ts # Portfólió adatok
│   ├── app.component.ts     # Fő alkalmazás komponens
│   ├── app.config.ts        # Alkalmazás konfiguráció
│   └── app.routes.ts        # Routing konfiguráció
├── environments/            # Környezeti változók
├── styles.scss             # Globális stílusok
└── index.html              # Fő HTML fájl
```

## Stílus útmutató

- **Csak Tailwind CSS** osztályokat használj, ne írj egyedi SCSS fájlokat
- PrimeNG komponenseket kombinálj Tailwind osztályokkal
- Dark mode támogatás beépítve
- Responsive design minden oldalon

## Fejlesztési útmutató

### Új komponens hozzáadása
```bash
ng generate component components/my-component --standalone
```

### Új szolgáltatás hozzáadása
```bash
ng generate service services/my-service
```

### Új oldal hozzáadása
1. Hozz létre új komponenst a `pages/` mappában
2. Add hozzá a route-ot az `app.routes.ts` fájlhoz
3. Add hozzá a navigációt a sidebar komponenshez

## Környezeti változók

### Development (environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

### Production (environment.prod.ts)
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://your-api-domain.com/api'
};
```

## Hibakeresés

### Gyakori problémák

1. **API kapcsolódási hiba**: Ellenőrizd, hogy a backend fut-e a megfelelő porton
2. **CORS hiba**: Állítsd be a CORS-t a backend oldalon
3. **PrimeNG stílus problémák**: Ellenőrizd, hogy a PrimeNG CSS fájlok be vannak-e töltve

### Logok
A fejlesztői konzolban láthatod az API hívások eredményeit és esetleges hibákat.

## Tesztelés

```bash
# Unit tesztek futtatása
npm test

# E2E tesztek futtatása
npm run e2e
```

## Deployment

### Netlify/Vercel
```bash
npm run build
# A dist/ mappa tartalmát töltsd fel
```

### Docker
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist/coin-signals-frontend /usr/share/nginx/html
```

## Hozzájárulás

1. Fork-old a repository-t
2. Hozz létre egy feature branch-et
3. Commitold a változtatásokat
4. Push-old a branch-et
5. Nyiss egy Pull Request-et

## Licenc

MIT License