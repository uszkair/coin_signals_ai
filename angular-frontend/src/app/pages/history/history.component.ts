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

  constructor(private historyService: HistoryService) {}

  ngOnInit(): void {
    this.loadTradeHistory();
  }

  applyFilters(): void {
    this.loadTradeHistory();
  }

  clearFilters(): void {
    this.selectedCoin = null;
    this.startDate = null;
    this.endDate = null;
    this.selectedType = null;
    this.loadTradeHistory();
  }

  exportData(): void {
    this.historyService.exportToCsv(this.tradeHistory);
  }

  private loadTradeHistory(): void {
    this.loading = true;
    
    const startDateStr = this.startDate ? this.startDate.toISOString().split('T')[0] : undefined;
    const endDateStr = this.endDate ? this.endDate.toISOString().split('T')[0] : undefined;

    this.historyService.getTradeHistory(
      this.selectedCoin || undefined,
      startDateStr,
      endDateStr,
      this.selectedType || undefined
    )
    .pipe(take(1))
    .subscribe({
      next: (history) => {
        this.tradeHistory = history;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading trade history:', error);
        this.loading = false;
      }
    });
  }

  getTotalStats() {
    const stats = {
      totalTrades: this.tradeHistory.length,
      profitableTrades: 0,
      losingTrades: 0,
      totalProfit: 0,
      totalLoss: 0,
      netProfit: 0,
      winRate: 0
    };

    this.tradeHistory.forEach(trade => {
      if (trade.profit_percent !== null && trade.profit_percent !== undefined) {
        if (trade.profit_percent > 0) {
          stats.profitableTrades++;
          stats.totalProfit += trade.profit_percent;
        } else if (trade.profit_percent < 0) {
          stats.losingTrades++;
          stats.totalLoss += Math.abs(trade.profit_percent);
        }
        stats.netProfit += trade.profit_percent;
      }
    });

    stats.winRate = stats.totalTrades > 0 ? (stats.profitableTrades / stats.totalTrades) * 100 : 0;

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
      case 'take_profit_hit': return 'success';
      case 'stop_loss_hit': return 'danger';
      case 'pending':
      case 'open': return 'warning';
      default: return 'info';
    }
  }

  getResultDisplayText(result: string | null | undefined): string {
    if (!result) return 'PENDING';
    switch (result.toLowerCase()) {
      case 'take_profit_hit': return 'PROFIT';
      case 'stop_loss_hit': return 'LOSS';
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