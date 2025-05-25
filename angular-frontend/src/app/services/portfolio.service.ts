import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PortfolioStats {
  total_profit_percent: number;
  profitable_trades: number;
  total_trades: number;
  loss_trades: number;
  best_coin: string;
  worst_coin: string;
  win_rate: number;
  avg_profit_per_trade: number;
}

export interface ProfitTimeline {
  date: string;
  cumulative_profit: number;
  daily_profit: number;
}

export interface CoinProfit {
  symbol: string;
  profit_percent: number;
  trade_count: number;
  win_rate: number;
}

@Injectable({
  providedIn: 'root'
})
export class PortfolioService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getTradeStats(timeframe: string = '30d'): Observable<{
    stats: PortfolioStats;
    profit_timeline: ProfitTimeline[];
    coin_profits: CoinProfit[];
  }> {
    return this.http.get<{
      stats: PortfolioStats;
      profit_timeline: ProfitTimeline[];
      coin_profits: CoinProfit[];
    }>(`${this.apiUrl}/trade-stats?timeframe=${timeframe}`);
  }
}