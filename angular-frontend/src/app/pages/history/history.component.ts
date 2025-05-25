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

  getStatusSeverity(status: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (status) {
      case 'CLOSED': return 'success';
      case 'OPEN': return 'info';
      case 'STOPPED': return 'danger';
      default: return 'info';
    }
  }
}