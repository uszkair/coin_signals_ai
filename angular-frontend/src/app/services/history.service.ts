import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TradeHistory {
  id?: string;
  symbol: string;
  timestamp: string;
  interval: string;
  entry_price: number;
  exit_price?: number;
  profit_percent?: number;
  stop_loss: number;
  take_profit: number;
  pattern?: string;
  score?: number;
  reason?: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  result?: string;
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
  // New methods for real Binance data
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

  exportBinanceTradesToCsv(data: any[]): void {
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
    link.download = 'binance-trade-history.csv';
    link.click();
    window.URL.revokeObjectURL(url);
  }
}