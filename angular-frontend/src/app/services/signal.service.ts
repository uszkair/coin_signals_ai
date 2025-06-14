import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface DecisionFactor {
  signal: 'BUY' | 'SELL' | 'NEUTRAL';
  reasoning: string;
  weight: number;
  [key: string]: any;
}

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
  interval?: string;
  decision_factors?: {
    candlestick_pattern: DecisionFactor & { name: string; score: number };
    trend_analysis: DecisionFactor & { trend: string };
    momentum_strength: DecisionFactor & { strength: string };
    rsi_analysis: DecisionFactor & { value: number };
    macd_analysis: DecisionFactor & { value: number };
    volume_analysis: DecisionFactor;
    support_resistance: DecisionFactor;
    ai_ml_analysis: DecisionFactor & {
      ai_signal: string;
      ai_confidence: number;
      risk_score: number
    };
  };
  total_score?: number;
}


@Injectable({
  providedIn: 'root'
})
export class SignalService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getMultipleSignals(symbols: string[], interval: string = '1h'): Observable<Signal[]> {
    const symbolsParam = symbols.join(',');
    return this.http.get<Signal[]>(`${this.apiUrl}/signals/?symbols=${symbolsParam}&interval=${interval}`);
  }

  getCurrentSignal(symbol: string, interval: string = '1h', saveToDb: boolean = true): Observable<Signal> {
    return this.http.get<Signal>(`${this.apiUrl}/signals/current?symbol=${symbol}&interval=${interval}&save_to_db=${saveToDb}`);
  }

}