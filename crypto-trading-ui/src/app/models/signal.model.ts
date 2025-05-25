export interface Signal {
  id: string;
  symbol: string;
  interval: string;
  timestamp: Date;
  type: 'BUY' | 'SELL' | 'HOLD';
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  trend: string;
  confidence: number;
  pattern?: string;
  reason?: string;
}

export interface CurrentSignal extends Signal {
  indicators?: {
    name: string;
    value: number;
    interpretation: string;
  }[];
}

export interface SignalHistory {
  signals: Signal[];
  totalCount: number;
}