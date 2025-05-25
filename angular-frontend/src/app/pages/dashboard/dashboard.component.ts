import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, take } from 'rxjs';

// PrimeNG imports
import { DropdownModule } from 'primeng/dropdown';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TimelineModule } from 'primeng/timeline';
import { ChartModule } from 'primeng/chart';
import { ToastModule } from 'primeng/toast';

import { SignalService, Signal, NewsItem } from '../../services/signal.service';

interface CoinOption {
  label: string;
  value: string;
}

interface IntervalOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DropdownModule,
    CardModule,
    ButtonModule,
    TableModule,
    TagModule,
    TimelineModule,
    ChartModule,
    ToastModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: []
})
export class DashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  loading = false;
  selectedCoin = 'BTCUSDT';
  selectedInterval = '1h';
  
  currentSignal: Signal | null = null;
  recentSignals: Signal[] = [];
  news: NewsItem[] = [];

  coinOptions: CoinOption[] = [
    { label: 'BTC/USDT', value: 'BTCUSDT' },
    { label: 'ETH/USDT', value: 'ETHUSDT' },
    { label: 'BNB/USDT', value: 'BNBUSDT' },
    { label: 'ADA/USDT', value: 'ADAUSDT' },
    { label: 'SOL/USDT', value: 'SOLUSDT' },
    { label: 'DOT/USDT', value: 'DOTUSDT' }
  ];

  intervalOptions: IntervalOption[] = [
    { label: '1 perc', value: '1m' },
    { label: '5 perc', value: '5m' },
    { label: '15 perc', value: '15m' },
    { label: '1 óra', value: '1h' },
    { label: '4 óra', value: '4h' },
    { label: '1 nap', value: '1d' }
  ];

  constructor(private signalService: SignalService) {}

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onCoinChange(): void {
    this.loadCurrentSignal();
  }

  onIntervalChange(): void {
    this.loadCurrentSignal();
  }

  refreshData(): void {
    this.loadData();
  }

  private loadData(): void {
    this.loadCurrentSignal();
    this.loadRecentSignals();
    this.loadNews();
  }

  private loadCurrentSignal(): void {
    this.loading = true;
    this.signalService.getCurrentSignal(this.selectedCoin, this.selectedInterval)
      .pipe(take(1))
      .subscribe({
        next: (signal) => {
          this.currentSignal = signal;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading current signal:', error);
          this.loading = false;
        }
      });
  }

  private loadRecentSignals(): void {
    const symbols = this.coinOptions.map(option => option.value);
    this.signalService.getMultipleSignals(symbols, this.selectedInterval)
      .pipe(take(1))
      .subscribe({
        next: (signals) => {
          this.recentSignals = signals.slice(0, 10); // Show last 10 signals
        },
        error: (error) => {
          console.error('Error loading recent signals:', error);
        }
      });
  }

  private loadNews(): void {
    this.signalService.getNews(this.selectedCoin)
      .pipe(take(1))
      .subscribe({
        next: (news) => {
          this.news = news.slice(0, 5); // Show last 5 news items
        },
        error: (error) => {
          console.error('Error loading news:', error);
        }
      });
  }

  getSignalSeverity(signal: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (signal) {
      case 'BUY': return 'success';
      case 'SELL': return 'danger';
      case 'HOLD': return 'warning';
      default: return 'info';
    }
  }

  getImpactSeverity(impact: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (impact) {
      case 'HIGH': return 'danger';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'info';
      default: return 'info';
    }
  }
}