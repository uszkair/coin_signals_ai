# Crypto Trading Assistant UI

An Angular-based frontend for an AI-powered Crypto Trading Dashboard.

## Features

- **Dashboard**: View current trading signals, price charts, and latest news
- **Trading History**: Track past trades and performance with filtering options
- **Portfolio**: Analyze your trading performance with charts and statistics

## Tech Stack

- Angular 19+
- PrimeNG UI Components
- SCSS for styling
- Chart.js for data visualization
- TradingView widget for interactive charts
- Responsive design for mobile and desktop

## Prerequisites

- Node.js (v18 or higher)
- npm (v9 or higher)

## Installation

1. Clone the repository
2. Navigate to the project directory:
   ```
   cd crypto-trading-ui
   ```
3. Install dependencies:
   ```
   npm install
   ```

## Development Server

Run the development server:

```
npm start
```

Navigate to `http://localhost:4200/` in your browser. The application will automatically reload if you change any of the source files.

## Backend API

The application is designed to work with a FastAPI backend running at `http://localhost:8000/api`. Make sure the backend server is running for the application to function properly.

API endpoints used:

- `/api/signal/current` - Get current trading signal
- `/api/signal/history` - Get recent signal history
- `/api/news` - Get latest news for a symbol
- `/api/history` - Get trading history with filters
- `/api/portfolio/summary` - Get portfolio summary data

## Building for Production

To build the application for production:

```
npm run build
```

The build artifacts will be stored in the `dist/` directory.

## Project Structure

- `src/app/models` - TypeScript interfaces for data models
- `src/app/services` - API services for data fetching
- `src/app/components` - Reusable UI components
- `src/app/pages` - Main application pages

## Future Enhancements (v2)

- User authentication and login
- Binance API integration for real-time trading
- Mobile push notifications
- Signal replay functionality
- Dark/light theme toggle

## License

MIT
