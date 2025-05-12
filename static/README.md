# Crypto Trading Assistant Frontend

This is the frontend for the Crypto Trading Assistant application, built with React, Vite, and Tailwind CSS.

## Features

- Dashboard with real-time trading signals
- TradingView chart integration
- Multiple timeframe analysis
- Swing and scalping trading modes
- Signal history tracking
- Customizable settings

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Setup

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Build for production:

```bash
npm run build
```

## Project Structure

- `src/components/` - Reusable UI components
- `src/pages/` - Page components
- `src/hooks/` - Custom React hooks
- `src/assets/` - Static assets

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `/api/signal/{symbol}` - Get trading signal for a specific symbol
- `/api/signal-mtf/{symbol}` - Get multi-timeframe trading signal
- `/api/signals` - Get trading signals for multiple symbols
- `/api/marketdata/{symbol}` - Get market data with indicators
- `/api/symbols` - Get list of watched symbols
- `/api/history/{date}` - Get signal history for a specific date

## Development

To run the frontend in development mode with hot-reloading:

```bash
npm run dev
```

The development server will start at http://localhost:5173 and will proxy API requests to the backend at http://localhost:8000.