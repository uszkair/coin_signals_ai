export interface PortfolioSummary {
  totalProfit: number;
  totalProfitPercentage: number;
  totalTrades: number;
  winRate: number;
  topPerformingCoin: {
    symbol: string;
    profit: number;
    profitPercentage: number;
  };
  dailyProfits: {
    date: string;
    profit: number;
  }[];
  coinPerformance: {
    symbol: string;
    profit: number;
    profitPercentage: number;
    trades: number;
  }[];
  tradeSummary: {
    symbol: string;
    trades: number;
    wins: number;
    losses: number;
    profit: number;
    profitPercentage: number;
    averageHoldTime: number; // in hours
  }[];
}