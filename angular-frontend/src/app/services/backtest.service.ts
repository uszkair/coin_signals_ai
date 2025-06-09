import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface BacktestRequest {
  test_name: string;
  symbol: string;
  days_back: number;
  min_confidence: number;
  position_size: number;
}

export interface DataFetchRequest {
  symbols: string[];
  days: number;
}

export interface BacktestResult {
  id: number;
  test_name: string;
  symbol: string;
  interval: string;
  start_date: string;
  end_date: string;
  min_confidence: number;
  position_size: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  total_profit_usd: number;
  total_profit_percent: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio?: number;
  created_at: string;
}

export interface BacktestTrade {
  id: number;
  symbol: string;
  signal_type: string;
  entry_price: number;
  exit_price?: number;
  stop_loss?: number;
  take_profit?: number;
  confidence: number;
  pattern?: string;
  entry_time: string;
  exit_time?: string;
  profit_usd: number;
  profit_percent: number;
  result: string;
}

export interface BacktestDetails {
  summary: BacktestResult;
  trades: BacktestTrade[];
}

export interface DataStatus {
  symbol: string;
  has_data: boolean;
  data_points: number;
  date_range: {
    start?: string;
    end?: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class BacktestService {
  private apiUrl = `${environment.apiUrl}/backtest`;

  constructor(private http: HttpClient) {}

  // Fetch historical data from Binance
  fetchHistoricalData(request: DataFetchRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/fetch-data`, request);
  }

  // Check data status for a symbol
  getDataStatus(symbol: string): Observable<DataStatus> {
    return this.http.get<DataStatus>(`${this.apiUrl}/data-status/${symbol}`);
  }

  // Run a backtest
  runBacktest(request: BacktestRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/run`, request);
  }

  // Get all backtest results
  getBacktestResults(): Observable<{ results: BacktestResult[] }> {
    return this.http.get<{ results: BacktestResult[] }>(`${this.apiUrl}/results`);
  }

  // Get detailed backtest results
  getBacktestDetails(backtestId: number): Observable<BacktestDetails> {
    return this.http.get<BacktestDetails>(`${this.apiUrl}/results/${backtestId}`);
  }

  // Delete a backtest
  deleteBacktest(backtestId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/results/${backtestId}`);
  }

  // Get available symbols
  getAvailableSymbols(): Observable<{ symbols: string[] }> {
    return this.http.get<{ symbols: string[] }>(`${this.apiUrl}/symbols`);
  }

  // Health check
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }
}