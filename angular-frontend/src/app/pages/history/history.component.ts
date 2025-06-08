import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { take } from 'rxjs';

// PrimeNG imports
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { ToolbarModule } from 'primeng/toolbar';
import { CardModule } from 'primeng/card';

import { HistoryService, TradeHistory } from '../../services/history.service';

interface FilterOptions {
  label: string;
  value: string;
}

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DropdownModule,
    CalendarModule,
    InputTextModule,
    TagModule,
    ToolbarModule,
    CardModule
  ],
  templateUrl: './history.component.html',
  styleUrls: []
})
export class HistoryComponent implements OnInit {
  loading = false;
  tradeHistory: TradeHistory[] = [];
  
  // Filters
  selectedCoin: string | null = null;
  startDate: Date | null = null;
  endDate: Date | null = null;
  selectedType: string | null = null;
  selectedResult: string | null = null;
  testnetMode: string | null = null;
  
  // Statistics
  tradingStats: any = null;
  dailySummary: any = null;

  coinOptions: FilterOptions[] = [
    { label: 'BTC/USDT', value: 'BTCUSDT' },
    { label: 'ETH/USDT', value: 'ETHUSDT' },
    { label: 'BNB/USDT', value: 'BNBUSDT' },
    { label: 'ADA/USDT', value: 'ADAUSDT' },
    { label: 'SOL/USDT', value: 'SOLUSDT' },
    { label: 'DOT/USDT', value: 'DOTUSDT' }
  ];

  typeOptions: FilterOptions[] = [
    { label: 'BUY', value: 'BUY' },
    { label: 'SELL', value: 'SELL' },
    { label: 'HOLD', value: 'HOLD' }
  ];

  resultOptions: FilterOptions[] = [
    { label: 'Profit', value: 'profit' },
    { label: 'Loss', value: 'loss' },
    { label: 'Failed Order', value: 'failed_order' },
    { label: 'Pending', value: 'pending' },
    { label: 'Breakeven', value: 'breakeven' }
  ];

  testnetOptions: FilterOptions[] = [
    { label: 'Testnet', value: 'true' },
    { label: 'Mainnet', value: 'false' }
  ];

  constructor(private historyService: HistoryService) {}

  ngOnInit(): void {
    this.loadTradeHistory();
    this.loadTradingStatistics();
    this.loadDailySummary();
  }

  applyFilters(): void {
    this.loadTradeHistory();
  }

  clearFilters(): void {
    this.selectedCoin = null;
    this.startDate = null;
    this.endDate = null;
    this.selectedType = null;
    this.selectedResult = null;
    this.testnetMode = null;
    this.loadTradeHistory();
  }

  exportData(): void {
    this.historyService.exportTradingHistoryToCsv(this.tradeHistory);
  }

  private loadTradeHistory(): void {
    this.loading = true;
    
    const startDateStr = this.startDate ? this.startDate.toISOString().split('T')[0] : undefined;
    const endDateStr = this.endDate ? this.endDate.toISOString().split('T')[0] : undefined;
    const testnetBool = this.testnetMode === 'true' ? true : this.testnetMode === 'false' ? false : undefined;

    this.historyService.getTradingHistory(
      this.selectedCoin || undefined,
      startDateStr,
      endDateStr,
      this.selectedResult || undefined,
      testnetBool,
      100
    )
    .pipe(take(1))
    .subscribe({
      next: (response) => {
        if (response.success) {
          this.tradeHistory = response.data.trades;
        } else {
          this.tradeHistory = [];
        }
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading trade history:', error);
        this.tradeHistory = [];
        this.loading = false;
      }
    });
  }

  private loadTradingStatistics(): void {
    this.historyService.getTradingStatistics(undefined, 30)
    .pipe(take(1))
    .subscribe({
      next: (response) => {
        if (response.success) {
          this.tradingStats = response.data;
        }
      },
      error: (error) => {
        console.error('Error loading trading statistics:', error);
      }
    });
  }

  private loadDailySummary(): void {
    const today = new Date().toISOString().split('T')[0];
    this.historyService.getDailySummary(today)
    .pipe(take(1))
    .subscribe({
      next: (response) => {
        if (response.success) {
          this.dailySummary = response.data;
        }
      },
      error: (error) => {
        console.error('Error loading daily summary:', error);
      }
    });
  }

  getTotalStats() {
    const stats = {
      totalTrades: this.tradeHistory.length,
      profitableTrades: 0,
      losingTrades: 0,
      failedOrders: 0,
      pendingTrades: 0,
      totalProfitUsd: 0,
      totalLossUsd: 0,
      netProfitUsd: 0,
      winRate: 0
    };

    this.tradeHistory.forEach(trade => {
      const result = trade.trade_result || trade.result;
      const profitUsd = trade.profit_loss_usd || 0;
      
      switch (result?.toLowerCase()) {
        case 'profit':
          stats.profitableTrades++;
          stats.totalProfitUsd += profitUsd;
          break;
        case 'loss':
          stats.losingTrades++;
          stats.totalLossUsd += Math.abs(profitUsd);
          break;
        case 'failed_order':
          stats.failedOrders++;
          break;
        case 'pending':
          stats.pendingTrades++;
          break;
      }
      
      stats.netProfitUsd += profitUsd;
    });

    const completedTrades = stats.profitableTrades + stats.losingTrades;
    stats.winRate = completedTrades > 0 ? (stats.profitableTrades / completedTrades) * 100 : 0;

    return stats;
  }

  getProfitClass(profit: number): string {
    if (profit > 0) return 'text-green-600 font-medium';
    if (profit < 0) return 'text-red-600 font-medium';
    return 'text-gray-600';
  }

  getScoreSeverity(score: number): 'success' | 'warning' | 'danger' | 'info' {
    if (score >= 80) return 'success';
    if (score >= 60) return 'info';
    if (score >= 40) return 'warning';
    return 'danger';
  }

  getResultSeverity(result: string | null | undefined): 'success' | 'warning' | 'danger' | 'info' {
    if (!result) return 'info';
    switch (result.toLowerCase()) {
      case 'profit': return 'success';
      case 'take_profit_hit': return 'success';
      case 'loss': return 'danger';
      case 'stop_loss_hit': return 'danger';
      case 'failed_order': return 'danger';
      case 'pending':
      case 'open': return 'warning';
      case 'breakeven': return 'info';
      default: return 'info';
    }
  }

  getResultDisplayText(result: string | null | undefined): string {
    if (!result) return 'PENDING';
    switch (result.toLowerCase()) {
      case 'profit': return 'PROFIT';
      case 'take_profit_hit': return 'PROFIT';
      case 'loss': return 'LOSS';
      case 'stop_loss_hit': return 'LOSS';
      case 'failed_order': return 'FAILED ORDER';
      case 'pending': return 'PENDING';
      case 'breakeven': return 'BREAKEVEN';
      default: return result.toUpperCase();
    }
  }

  getSignalTypeSeverity(signalType: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (signalType) {
      case 'BUY': return 'success';
      case 'SELL': return 'danger';
      case 'HOLD': return 'warning';
      default: return 'info';
    }
  }
}