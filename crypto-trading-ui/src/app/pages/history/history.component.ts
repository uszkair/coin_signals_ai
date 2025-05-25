import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { ChipModule } from 'primeng/chip';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { HistoryService, SignalService } from '../../services';
import { TradeHistoryFilter, TradeHistoryItem, TradeHistoryResponse } from '../../models';

import { Observable, Subject } from 'rxjs';
import { takeUntil, map } from 'rxjs/operators';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    DropdownModule,
    CalendarModule,
    ButtonModule,
    InputTextModule,
    ChipModule,
    TagModule,
    TooltipModule,
    ProgressSpinnerModule
  ],
  templateUrl: './history.component.html',
  styleUrl: './history.component.scss'
})
export class HistoryComponent implements OnInit, OnDestroy {
  // Trade history data
  tradeHistory$: Observable<TradeHistoryResponse>;
  
  // Loading state
  loading$: Observable<boolean>;
  
  // Filter options
  symbols$: Observable<string[]>;
  patternTypes: string[] = ['All Patterns', 'Hammer', 'Doji', 'Engulfing', 'Morning Star', 'Evening Star'];
  resultTypes: { label: string, value: string }[] = [
    { label: 'All Results', value: 'all' },
    { label: 'Profit', value: 'profit' },
    { label: 'Loss', value: 'loss' }
  ];
  
  // Current filter
  currentFilter$: Observable<TradeHistoryFilter>;
  
  // Local filter for UI binding
  filter: TradeHistoryFilter = {
    symbol: undefined,
    dateFrom: undefined,
    dateTo: undefined,
    patternType: undefined,
    resultType: 'all',
    page: 1,
    pageSize: 10
  };
  
  // Component destroy subject for cleanup
  private destroy$ = new Subject<void>();

  constructor(
    private historyService: HistoryService,
    private signalService: SignalService
  ) {
    // Initialize observables
    this.tradeHistory$ = this.historyService.tradeHistory$;
    this.loading$ = this.historyService.loading$;
    this.currentFilter$ = this.historyService.currentFilter$;
    
    // Initialize symbols with 'All Coins' option
    this.symbols$ = this.signalService.getAvailableSymbols().pipe(
      map(symbols => ['All Coins', ...symbols])
    );
  }

  ngOnInit(): void {
    // Subscribe to current filter from service
    this.currentFilter$
      .pipe(takeUntil(this.destroy$))
      .subscribe(filter => {
        this.filter = { ...filter };
      });
      
    // Initial data load
    this.historyService.updateFilter(this.filter);
  }
  
  ngOnDestroy(): void {
    // Clean up subscriptions
    this.destroy$.next();
    this.destroy$.complete();
  }

  onPageChange(event: any): void {
    this.historyService.updateFilter({
      page: event.page + 1,
      pageSize: event.rows
    });
  }

  applyFilters(): void {
    // Convert filter values
    const updatedFilter: TradeHistoryFilter = {
      ...this.filter,
      page: 1,
      symbol: this.filter.symbol === 'All Coins' ? undefined : this.filter.symbol,
      patternType: this.filter.patternType === 'All Patterns' ? undefined : this.filter.patternType
    };
    
    this.historyService.updateFilter(updatedFilter);
  }

  resetFilters(): void {
    this.filter = {
      symbol: undefined,
      dateFrom: undefined,
      dateTo: undefined,
      patternType: undefined,
      resultType: 'all',
      page: 1,
      pageSize: 10
    };
    
    this.historyService.resetFilter();
  }

  exportToCsv(): void {
    // Convert filter values
    const filter: TradeHistoryFilter = {
      ...this.filter,
      symbol: this.filter.symbol === 'All Coins' ? undefined : this.filter.symbol,
      patternType: this.filter.patternType === 'All Patterns' ? undefined : this.filter.patternType
    };
    
    this.historyService.exportToCsv(filter).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trade-history-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (error) => console.error('Error exporting to CSV:', error)
    });
  }
  
  trackByTradeId(index: number, trade: TradeHistoryItem): string {
    return trade.id;
  }

  getProfitClass(profit?: number): string {
    if (!profit) return '';
    return profit > 0 ? 'profit-positive' : 'profit-negative';
  }

  getStatusSeverity(status: string): string {
    switch (status) {
      case 'open':
        return 'info';
      case 'closed':
        return 'success';
      case 'cancelled':
        return 'danger';
      default:
        return 'warning';
    }
  }
}