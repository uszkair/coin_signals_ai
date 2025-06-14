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

export interface PositionSizeConfig {
  mode: 'percentage' | 'fixed_usd';
  fixed_amount_usd?: number;
  max_percentage?: number;
}

export interface TradingEnvironment {
  testnet: boolean;
  environment: string;
  description: string;
  api_connected: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class TradingService {
  private baseUrl = 'http://localhost:8000/api/trading';
  private autoTradingUrl = 'http://localhost:8000/api/auto-trading';
  
  // Auto trading state
  private autoTradingSubject = new BehaviorSubject<boolean>(false);
  public autoTrading$ = this.autoTradingSubject.asObservable();

  constructor(private http: HttpClient) {
    // Load auto trading state from localStorage and sync with backend
    this.loadAutoTradingState();
  }

  private async loadAutoTradingState(): Promise<void> {
    try {
      // Get current state from backend
      const response = await this.getAutoTradingStatus().toPromise();
      if (response?.success) {
        const enabled = response.data.auto_trading_enabled;
        this.autoTradingSubject.next(enabled);
        localStorage.setItem('autoTrading', JSON.stringify(enabled));
      }
    } catch (error) {
      // Fallback to localStorage if backend is not available
      const savedState = localStorage.getItem('autoTrading');
      if (savedState !== null) {
        this.autoTradingSubject.next(JSON.parse(savedState));
      }
    }
  }

  // Auto trading methods
  setAutoTrading(enabled: boolean): Observable<TradeResult> {
    const endpoint = enabled ? 'enable' : 'disable';
    return this.http.post<TradeResult>(`${this.autoTradingUrl}/${endpoint}`, {});
  }

  getAutoTrading(): boolean {
    return this.autoTradingSubject.value;
  }

  updateAutoTradingState(enabled: boolean): void {
    this.autoTradingSubject.next(enabled);
    localStorage.setItem('autoTrading', JSON.stringify(enabled));
  }

  // Auto trading API methods
  getAutoTradingStatus(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.autoTradingUrl}/status`);
  }

  getAutoTradingSettings(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.autoTradingUrl}/settings`);
  }

  updateAutoTradingSettings(settings: any): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.autoTradingUrl}/settings`, settings);
  }

  getAutoTradingHistory(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.autoTradingUrl}/history`);
  }

  getAutoTradingPerformance(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.autoTradingUrl}/performance`);
  }


  autoTradingEmergencyStop(): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.autoTradingUrl}/emergency-stop`, {});
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

  // Get live Binance positions (including external positions)
  getLivePositions(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/live-positions`);
  }

  // Get only P&L data for live positions (for efficient updates)
  getLivePositionsPnlOnly(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/live-positions/pnl-only`);
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

  // Position Size Configuration
  getPositionSizeConfig(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/position-size-config`);
  }

  updatePositionSizeConfig(config: PositionSizeConfig): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/position-size-config`, config);
  }

  // Trading Environment (Testnet/Mainnet)
  getTradingEnvironment(): Observable<{ success: boolean; data: TradingEnvironment }> {
    return this.http.get<{ success: boolean; data: TradingEnvironment }>(`${this.baseUrl}/environment`);
  }

  switchTradingEnvironment(useTestnet: boolean): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/switch-environment`, {
      use_testnet: useTestnet
    });
  }

  getMinimumRequirements(): Observable<TradeResult> {
    return this.http.get<TradeResult>(`${this.baseUrl}/minimum-requirements`);
  }

  // Position Size Validation
  validatePositionSizeConfig(config: PositionSizeConfig): Observable<TradeResult> {
    return this.http.post<TradeResult>(`${this.baseUrl}/validate-position-size`, config);
  }
}