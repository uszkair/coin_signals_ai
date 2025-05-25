import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ChipModule } from 'primeng/chip';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { SignalService, NewsService } from '../../services';
import { CurrentSignal, Signal, NewsItem } from '../../models';
import { TradingViewWidgetComponent } from '../../components/trading-view-widget/trading-view-widget.component';

import { Observable, Subject, combineLatest, of } from 'rxjs';
import { takeUntil, tap, switchMap, map, catchError } from 'rxjs/operators';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DropdownModule,
    CardModule,
    ButtonModule,
    ChipModule,
    TableModule,
    TagModule,
    ProgressSpinnerModule,
    TradingViewWidgetComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {
  // Selected values
  selectedSymbol: string = 'BTCUSDT';
  selectedInterval: string = '1h';
  
  // Available options
  symbols$: Observable<string[]> = of([]);
  intervals: string[] = ['1m', '5m', '15m', '1h', '4h', '1d'];
  
  // Data streams
  currentSignal$: Observable<CurrentSignal>;
  recentSignals$: Observable<Signal[]>;
  news$: Observable<NewsItem[]>;
  
  // Loading states
  loading$ = {
    symbols: false,
    signal: false,
    history: false,
    news: false
  };
  
  // Component destroy subject for cleanup
  private destroy$ = new Subject<void>();

  constructor(
    private signalService: SignalService,
    private newsService: NewsService
  ) {
    // Initialize observables
    this.symbols$ = this.signalService.getAvailableSymbols().pipe(
      catchError(() => of([]))
    );
    this.currentSignal$ = this.signalService.currentSignal$;
    this.news$ = this.newsService.currentSymbolNews$.pipe(
      map(response => response.news)
    );
    
    // Recent signals observable
    this.recentSignals$ = this.signalService.currentSymbol$.pipe(
      switchMap(symbol =>
        this.signalService.getSignalHistory(symbol, 1).pipe(
          map(history => history.signals)
        )
      )
    );
  }

  ngOnInit(): void {
    // Subscribe to current symbol/interval from service
    this.signalService.currentSymbol$
      .pipe(takeUntil(this.destroy$))
      .subscribe(symbol => {
        this.selectedSymbol = symbol;
      });
      
    this.signalService.currentInterval$
      .pipe(takeUntil(this.destroy$))
      .subscribe(interval => {
        this.selectedInterval = interval;
      });
  }
  
  ngOnDestroy(): void {
    // Clean up subscriptions
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSymbolChange(): void {
    this.signalService.setSymbol(this.selectedSymbol);
  }

  onIntervalChange(): void {
    this.signalService.setInterval(this.selectedInterval);
  }

  getSignalTypeClass(type: string): string {
    switch (type) {
      case 'BUY':
        return 'signal-buy';
      case 'SELL':
        return 'signal-sell';
      default:
        return 'signal-hold';
    }
  }

  getSentimentClass(sentiment: string): string {
    switch (sentiment) {
      case 'positive':
        return 'sentiment-positive';
      case 'negative':
        return 'sentiment-negative';
      default:
        return 'sentiment-neutral';
    }
  }
  
  trackBySignalId(index: number, signal: Signal): string {
    return signal.id;
  }
  
  trackByNewsId(index: number, news: NewsItem): string {
    return news.id;
  }
}