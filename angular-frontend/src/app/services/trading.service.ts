import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

export interface TradingAccount {
  account_info: any;
  trading_statistics: any;
  active_positions: any;
  trader_config: any;
}

export interface TradeRequest {
  symbol: string;
  interval?: string;
  position_size_usd?: number;
  force_execute?: boolean;
}

export interface TradeResult {
  success: boolean;
  data?: any;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class TradingService {
  private baseUrl = 'http://localhost:8000/api/trading';
  
  // Auto trading state
  private autoTradingSubject = new BehaviorSubject<boolean>(false);
  public autoTrading$ = this.autoTradingSubject.asObservable();

  constructor(private http: HttpClient) {
    // Load auto trading state from localStorage
    const savedState = localStorage.getItem('autoTrading');
    if (savedState !== null) {
      this.autoTradingSubject.next(JSON.parse(savedState));
    }
  }

  // Auto trading methods
  setAutoTrading(enabled: boolean): void {
    this.autoTradingSubject.next(enabled);
    localStorage.setItem('autoTrading', JSON.stringify(enabled));
  }

  getAutoTrading(): boolean {
    return this.autoTradingSubject.value;
  }

  // Account Management
  getAccountStatus(): Observable<{ success: boolean; data: TradingAccount }> {
    return this.http.get<{ success: boolean; data: TradingAccount }>(`${this.baseUrl}/account`);
  }

  testConnection(): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/test-connection`, {});
  }

  // Trading Operations
  executeTrade(tradeRequest: TradeRequest): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/execute`, tradeRequest);
  }

  executeSignalTrade(signal: any, positionSizeUsd?: number): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/execute-signal`, {
      signal,
      position_size_usd: positionSizeUsd
    });
  }

  // Position Management
  getActivePositions(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/positions`);
  }

  closePosition(positionId: string, reason: string = 'manual'): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/close-position`, {
      position_id: positionId,
      reason
    });
  }

  closeAllPositions(reason: string = 'manual_close_all'): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/close-all-positions`, { reason });
  }

  // Statistics and Risk
  getTradingStatistics(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/statistics`);
  }

  getRiskAssessment(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/risk-assessment`);
  }

  // Configuration
  getTradingConfig(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/config`);
  }

  updateTradingConfig(config: any): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/config`, config);
  }

  // Emergency
  emergencyStop(): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/emergency-stop`, {});
  }

  getWalletBalance(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/wallet-balance`);
  }
}