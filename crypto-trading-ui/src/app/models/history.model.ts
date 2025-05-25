export interface TradeHistoryItem {
  id: string;
  symbol: string;
  interval: string;
  entryTime: Date;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  exitTime?: Date;
  exitPrice?: number;
  profit?: number;
  profitPercentage?: number;
  pattern: string;
  score: number; // 1-10 scale indicating signal strength
  reason: string;
  status: 'open' | 'closed' | 'cancelled';
}

export interface TradeHistoryResponse {
  trades: TradeHistoryItem[];
  totalCount: number;
  totalProfit: number;
  totalProfitPercentage: number;
  winRate: number;
}

export interface TradeHistoryFilter {
  symbol?: string;
  dateFrom?: Date;
  dateTo?: Date;
  patternType?: string;
  resultType?: 'profit' | 'loss' | 'all';
  page: number;
  pageSize: number;
}