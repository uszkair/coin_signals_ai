import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TradeHistory {
  id?: string;
  signal_id?: number;
  symbol: string;
  timestamp: string;
  interval: string;
  entry_price: number;
  exit_price?: number;
  profit_percent?: number;
  profit_loss_usd?: number;
  profit_loss_percentage?: number;
  stop_loss: number;
  take_profit: number;
  pattern?: string;
  score?: number;
  confidence?: number;
  reason?: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  result?: string;
  trade_result?: string;
  main_order_id?: string;
  stop_loss_order_id?: string;
  take_profit_order_id?: string;
  quantity?: number;
  position_size_usd?: number;
  failure_reason?: string;
  entry_time?: string;
  exit_time?: string;
  testnet_mode?: boolean;
  created_at?: string;
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
      'Symbol', 'Signal', 'Timestamp', 'Interval', 'Entry Price', 'Exit Price',
      'Profit %', 'Stop Loss', 'Take Profit', 'Pattern', 'Score', 'Reason', 'Result'
    ];
    
    const csvContent = [
      headers.join(','),
      ...data.map(row => [
        row.symbol,
        row.signal,
        row.timestamp,
        row.interval,
        row.entry_price,
        row.exit_price || '',
        row.profit_percent || '',
        row.stop_loss,
        row.take_profit,
        row.pattern || '',
        row.score || '',
        `"${row.reason || ''}"`,
        row.result || ''
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
  // New methods for real Coinbase data
  getRealTradeHistory(symbol?: string, limit: number = 100): Observable<{success: boolean, data: {trades: any[], count: number}}> {
    let params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (symbol) params.append('symbol', symbol);
    
    const queryString = params.toString();
    const url = `${this.apiUrl}/trading/trade-history?${queryString}`;
    
    return this.http.get<{success: boolean, data: {trades: any[], count: number}}>(url);
  }

  getRealOrderHistory(symbol?: string, limit: number = 100): Observable<any> {
    let params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (symbol) params.append('symbol', symbol);
    
    const queryString = params.toString();
    const url = `${this.apiUrl}/trading/order-history?${queryString}`;
    
    return this.http.get<any>(url);
  }

  getWalletBalance(): Observable<{success: boolean, data: {total_balance_usdt: number, balances: any[], account_type: string, can_trade: boolean, testnet: boolean}}> {
    return this.http.get<{success: boolean, data: {total_balance_usdt: number, balances: any[], account_type: string, can_trade: boolean, testnet: boolean}}>(`${this.apiUrl}/trading/wallet-balance`);
  }

  exportCoinbaseTradesToCsv(data: any[]): void {
    const headers = [
      'Timestamp', 'Symbol', 'Side', 'Price', 'Quantity', 'Commission',
      'Commission Asset', 'Trade ID', 'Order ID', 'Quote Qty'
    ];
    
    const csvContent = [
      headers.join(','),
      ...data.map(row => [
        row.timestamp,
        row.symbol,
        row.signal,
        row.entry_price,
        row.quantity,
        row.commission,
        row.commission_asset,
        row.trade_id,
        row.order_id,
        row.quote_qty
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'coinbase-trade-history.csv';
    link.click();
    window.URL.revokeObjectURL(url);
  }

  // New methods for trading history with order results
  getTradingHistory(
    symbol?: string,
    startDate?: string,
    endDate?: string,
    tradeResult?: string,
    testnetMode?: boolean,
    limit: number = 100
  ): Observable<{success: boolean, data: {trades: TradeHistory[], count: number, filters: any}}> {
    let params = new URLSearchParams();
    
    if (symbol) params.append('symbol', symbol);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (tradeResult) params.append('trade_result', tradeResult);
    if (testnetMode !== undefined) params.append('testnet_mode', testnetMode.toString());
    params.append('limit', limit.toString());

    const queryString = params.toString();
    const url = `${this.apiUrl}/trading/history?${queryString}`;
    
    return this.http.get<{success: boolean, data: {trades: TradeHistory[], count: number, filters: any}}>(url);
  }

  getTradingStatistics(
    symbol?: string,
    days: number = 30,
    testnetMode?: boolean
  ): Observable<{success: boolean, data: any}> {
    let params = new URLSearchParams();
    
    if (symbol) params.append('symbol', symbol);
    params.append('days', days.toString());
    if (testnetMode !== undefined) params.append('testnet_mode', testnetMode.toString());

    const queryString = params.toString();
    const url = `${this.apiUrl}/trading/history/statistics?${queryString}`;
    
    return this.http.get<{success: boolean, data: any}>(url);
  }

  getDailySummary(
    date?: string,
    testnetMode?: boolean
  ): Observable<{success: boolean, data: any}> {
    let params = new URLSearchParams();
    
    if (date) params.append('date', date);
    if (testnetMode !== undefined) params.append('testnet_mode', testnetMode.toString());

    const queryString = params.toString();
    const url = `${this.apiUrl}/trading/history/daily-summary?${queryString}`;
    
    return this.http.get<{success: boolean, data: any}>(url);
  }

  exportTradingHistoryToCsv(data: TradeHistory[]): void {
    const headers = [
      'Symbol', 'Signal', 'Entry Time', 'Exit Time', 'Entry Price', 'Exit Price',
      'Quantity', 'Position Size USD', 'Profit/Loss USD', 'Profit/Loss %',
      'Trade Result', 'Main Order ID', 'Stop Loss', 'Take Profit',
      'Pattern', 'Confidence', 'Failure Reason', 'Testnet Mode'
    ];
    
    const csvContent = [
      headers.join(','),
      ...data.map(row => [
        row.symbol,
        row.signal,
        row.entry_time || row.timestamp,
        row.exit_time || '',
        row.entry_price,
        row.exit_price || '',
        row.quantity || '',
        row.position_size_usd || '',
        row.profit_loss_usd || '',
        row.profit_loss_percentage || '',
        row.trade_result || row.result || '',
        row.main_order_id || '',
        row.stop_loss,
        row.take_profit,
        row.pattern || '',
        row.confidence || '',
        `"${row.failure_reason || ''}"`,
        row.testnet_mode || false
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `trading-history-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  deleteTrade(tradeId: number): Observable<{ success: boolean; message?: string; error?: string }> {
    return this.http.delete<{ success: boolean; message?: string; error?: string }>(
      `${this.apiUrl}/trading/history/${tradeId}`
    );
  }

  clearAllHistory(testnetOnly: boolean = true): Observable<{ success: boolean; message?: string; deleted_count?: number; error?: string }> {
    let params = new URLSearchParams();
    params.append('testnet_only', testnetOnly.toString());

    const queryString = params.toString();
    const url = `${this.apiUrl}/trading/history/clear-all?${queryString}`;
    
    return this.http.delete<{ success: boolean; message?: string; deleted_count?: number; error?: string }>(url);
  }
}