import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Signal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  pattern: string;
  trend: string;
  confidence: number;
  timestamp: string;
  reason: string;
}

export interface NewsItem {
  title: string;
  content: string;
  timestamp: string;
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
  symbol?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SignalService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getCurrentSignal(symbol: string, interval: string = '1h'): Observable<Signal> {
    return this.http.get<Signal>(`${this.apiUrl}/signal/${symbol}?interval=${interval}`);
  }

  getMultipleSignals(symbols: string[], interval: string = '1h'): Observable<Signal[]> {
    const symbolsParam = symbols.join(',');
    return this.http.get<Signal[]>(`${this.apiUrl}/signals?symbols=${symbolsParam}&interval=${interval}`);
  }

  getNews(symbol?: string): Observable<NewsItem[]> {
    const url = symbol 
      ? `${this.apiUrl}/news?symbol=${symbol}`
      : `${this.apiUrl}/news`;
    return this.http.get<NewsItem[]>(url);
  }
}