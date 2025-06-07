import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Signal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  entry_price: number;
  current_price: number;  // Real-time current price
  stop_loss: number;
  take_profit: number;
  pattern: string;
  trend: string;
  confidence: number;
  timestamp: string;
  reason?: string;
  score?: number;
}


@Injectable({
  providedIn: 'root'
})
export class SignalService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getMultipleSignals(symbols: string[], interval: string = '1h'): Observable<Signal[]> {
    const symbolsParam = symbols.join(',');
    return this.http.get<Signal[]>(`${this.apiUrl}/signals?symbols=${symbolsParam}&interval=${interval}`);
  }

}