import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TradeHistory {
  id: string;
  symbol: string;
  timestamp: string;
  interval: string;
  entry_price: number;
  exit_price?: number;
  profit_percent?: number;
  stop_loss: number;
  take_profit: number;
  pattern: string;
  score: number;
  reason: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  status: 'OPEN' | 'CLOSED' | 'STOPPED';
}

@Injectable({
  providedIn: 'root'
})
export class HistoryService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getTradeHistory(
    coinPair?: string, 
    startDate?: string, 
    endDate?: string,
    type?: string
  ): Observable<TradeHistory[]> {
    let params = new URLSearchParams();
    
    if (coinPair) params.append('coinPair', coinPair);
    if (startDate) params.append('startDate', startDate);
    if (endDate) params.append('endDate', endDate);
    if (type) params.append('type', type);

    const queryString = params.toString();
    const url = queryString 
      ? `${this.apiUrl}/trade-history?${queryString}`
      : `${this.apiUrl}/trade-history`;
      
    return this.http.get<TradeHistory[]>(url);
  }

  exportToCsv(data: TradeHistory[]): void {
    const headers = [
      'Symbol', 'Timestamp', 'Interval', 'Entry Price', 'Exit Price', 
      'Profit %', 'Stop Loss', 'Take Profit', 'Pattern', 'Score', 'Reason'
    ];
    
    const csvContent = [
      headers.join(','),
      ...data.map(row => [
        row.symbol,
        row.timestamp,
        row.interval,
        row.entry_price,
        row.exit_price || '',
        row.profit_percent || '',
        row.stop_loss,
        row.take_profit,
        row.pattern,
        row.score,
        `"${row.reason}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `trade-history-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  }
}