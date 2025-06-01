import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, take, interval } from 'rxjs';

// PrimeNG imports
import { DropdownModule } from 'primeng/dropdown';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TimelineModule } from 'primeng/timeline';
import { ChartModule } from 'primeng/chart';
import { ToastModule } from 'primeng/toast';
import { InputSwitchModule } from 'primeng/inputswitch';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { MessageService } from 'primeng/api';
import { ConfirmationService } from 'primeng/api';

import { SignalService, Signal, NewsItem } from '../../services/signal.service';
import { WebSocketService } from '../../services/websocket.service';
import { TradingViewWidgetComponent } from '../../components/trading-view-widget/trading-view-widget.component';

interface FilterOption {
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
    ToastModule,
    InputSwitchModule,
    ConfirmDialogModule,
    DialogModule,
    TradingViewWidgetComponent
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private refreshInterval$ = new Subject<void>();
  
  // Loading and connection
  loading = false;
  connectionStatus: 'connected' | 'disconnected' = 'connected';
  autoRefresh = true;
  
  // Signals data
  allSignals: Signal[] = [];
  filteredSignals: Signal[] = [];
  selectedSignal: Signal | null = null;
  
  // Chart modal
  showChartModal = false;
  
  // Filters
  selectedSymbolFilter: string | null = null;
  selectedSignalFilter: string | null = null;
  selectedConfidenceFilter: string | null = null;
  
  // Filter options
  symbolOptions: FilterOption[] = [
    { label: 'BTC/USDT', value: 'BTCUSDT' },
    { label: 'ETH/USDT', value: 'ETHUSDT' },
    { label: 'BNB/USDT', value: 'BNBUSDT' },
    { label: 'ADA/USDT', value: 'ADAUSDT' },
    { label: 'SOL/USDT', value: 'SOLUSDT' },
    { label: 'DOT/USDT', value: 'DOTUSDT' }
  ];

  signalTypeOptions: FilterOption[] = [
    { label: 'BUY', value: 'BUY' },
    { label: 'SELL', value: 'SELL' },
    { label: 'HOLD', value: 'HOLD' }
  ];

  confidenceOptions: FilterOption[] = [
    { label: 'Magas (80%+)', value: 'high' },
    { label: 'Közepes (60-79%)', value: 'medium' },
    { label: 'Alacsony (<60%)', value: 'low' }
  ];

  constructor(
    private signalService: SignalService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private webSocketService: WebSocketService
  ) {}

  ngOnInit(): void {
    this.loadSignals();
    this.startAutoRefresh();
    this.setupWebSocketConnection();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.refreshInterval$.next();
    this.refreshInterval$.complete();
  }

  // Auto-refresh functionality
  toggleAutoRefresh(): void {
    if (this.autoRefresh) {
      this.startAutoRefresh();
    } else {
      this.stopAutoRefresh();
    }
  }

  private startAutoRefresh(): void {
    this.stopAutoRefresh();
    if (this.autoRefresh) {
      interval(30000) // Refresh every 30 seconds
        .pipe(takeUntil(this.refreshInterval$))
        .subscribe(() => {
          this.loadSignals(true); // Silent refresh
        });
    }
  }

  private stopAutoRefresh(): void {
    this.refreshInterval$.next();
  }

  // Data loading
  private loadSignals(silent: boolean = false): void {
    if (!silent) {
      this.loading = true;
    }
    
    // Load signals for all symbols to populate the list
    const symbols = this.symbolOptions.map(option => option.value);
    this.signalService.getMultipleSignals(symbols, '1h')
      .pipe(take(1))
      .subscribe({
        next: (signals) => {
          // Sort by timestamp descending (newest first)
          this.allSignals = signals.sort((a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          );
          this.applyFilters();
          this.connectionStatus = 'connected';
          this.loading = false;
          
          // Auto-select first signal if none selected
          if (this.filteredSignals.length > 0 && !this.selectedSignal) {
            this.selectedSignal = this.filteredSignals[0];
          }
          
          if (!silent && signals.length > 0) {
            this.showNewSignalNotification(signals[0]);
          }
        },
        error: (error) => {
          console.error('Error loading signals:', error);
          this.connectionStatus = 'disconnected';
          this.loading = false;
          this.messageService.add({
            severity: 'error',
            summary: 'Hiba',
            detail: 'Nem sikerült betölteni a szignálokat'
          });
        }
      });
  }

  // Load single signal for faster chart display
  private loadSingleSignal(symbol: string): void {
    this.signalService.getCurrentSignal(symbol, '1h')
      .pipe(take(1))
      .subscribe({
        next: (signal) => {
          // Update or add the signal to the list
          const existingIndex = this.allSignals.findIndex(s => s.symbol === symbol);
          if (existingIndex >= 0) {
            this.allSignals[existingIndex] = signal;
          } else {
            this.allSignals.unshift(signal);
          }
          
          // Re-sort and filter
          this.allSignals.sort((a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          );
          this.applyFilters();
        },
        error: (error) => {
          console.error(`Error loading signal for ${symbol}:`, error);
        }
      });
  }

  // Filtering
  applyFilters(): void {
    this.filteredSignals = this.allSignals.filter(signal => {
      // Symbol filter
      if (this.selectedSymbolFilter && signal.symbol !== this.selectedSymbolFilter) {
        return false;
      }
      
      // Signal type filter
      if (this.selectedSignalFilter && signal.signal !== this.selectedSignalFilter) {
        return false;
      }
      
      // Confidence filter
      if (this.selectedConfidenceFilter) {
        const confidence = signal.confidence;
        switch (this.selectedConfidenceFilter) {
          case 'high':
            if (confidence < 80) return false;
            break;
          case 'medium':
            if (confidence < 60 || confidence >= 80) return false;
            break;
          case 'low':
            if (confidence >= 60) return false;
            break;
        }
      }
      
      return true;
    });

    // Auto-select first signal after filtering
    if (this.filteredSignals.length > 0) {
      // If current selection is not in filtered results, select first
      if (!this.selectedSignal || !this.filteredSignals.includes(this.selectedSignal)) {
        this.selectedSignal = this.filteredSignals[0];
      }
    } else {
      this.selectedSignal = null;
    }
  }

  // Signal selection
  onSignalSelect(event: any): void {
    this.selectedSignal = event.data;
  }

  selectSignal(signal: Signal): void {
    this.selectedSignal = signal;
  }

  // UI helper methods
  getRowClass(signal: Signal): string {
    const baseClass = 'border-l-4 ';
    const confidence = signal.confidence;
    
    if (confidence >= 80) {
      return baseClass + 'border-green-500 bg-green-50 dark:bg-green-900/10';
    } else if (confidence >= 60) {
      return baseClass + 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10';
    } else {
      return baseClass + 'border-red-500 bg-red-50 dark:bg-red-900/10';
    }
  }

  getSignalSeverity(signal: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (signal) {
      case 'BUY': return 'success';
      case 'SELL': return 'danger';
      case 'HOLD': return 'warning';
      default: return 'info';
    }
  }

  getConfidenceBarClass(confidence: number): string {
    if (confidence >= 80) {
      return 'bg-green-500';
    } else if (confidence >= 60) {
      return 'bg-yellow-500';
    } else {
      return 'bg-red-500';
    }
  }

  getConfidenceText(confidence: number): string {
    if (confidence >= 80) {
      return 'Erős';
    } else if (confidence >= 60) {
      return 'Közepes';
    } else {
      return 'Gyenge';
    }
  }

  // Calculation methods
  calculateRiskReward(signal: Signal): string {
    const risk = Math.abs(signal.entry_price - signal.stop_loss);
    const reward = Math.abs(signal.take_profit - signal.entry_price);
    const ratio = reward / risk;
    return `1:${ratio.toFixed(2)}`;
  }

  calculatePotentialLoss(signal: Signal): number {
    return Math.abs(signal.entry_price - signal.stop_loss);
  }

  calculatePotentialProfit(signal: Signal): number {
    return Math.abs(signal.take_profit - signal.entry_price);
  }

  // Trading actions
  executeTrade(action: 'BUY' | 'SELL', signal: Signal): void {
    this.confirmationService.confirm({
      message: `Biztosan ${action === 'BUY' ? 'vásárolni' : 'eladni'} szeretnéd a ${signal.symbol}-t ${signal.entry_price} áron?`,
      header: 'Kereskedés megerősítése',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        // Here you would implement the actual trading logic
        this.messageService.add({
          severity: 'success',
          summary: 'Kereskedés végrehajtva',
          detail: `${action} parancs elküldve: ${signal.symbol} @ $${signal.entry_price}`
        });
      }
    });
  }


  showChart(signal: Signal): void {
    this.selectedSignal = signal;
    this.showChartModal = true;
    
    // Load fresh data for the selected symbol to ensure chart has latest data
    this.loadSingleSignal(signal.symbol);
  }

  // Notifications
  private showNewSignalNotification(signal: Signal): void {
    this.messageService.add({
      severity: this.getSignalSeverity(signal.signal) === 'success' ? 'success' : 'warn',
      summary: 'Új szignál érkezett!',
      detail: `${signal.symbol}: ${signal.signal} @ $${signal.entry_price}`,
      life: 5000
    });
  }

  // WebSocket connection setup
  private setupWebSocketConnection(): void {
    // Listen to connection status changes
    this.webSocketService.connectionStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        this.connectionStatus = status === 'connected' ? 'connected' : 'disconnected';
      });

    // Listen to new signals
    this.webSocketService.onSignalUpdate()
      .pipe(takeUntil(this.destroy$))
      .subscribe(newSignal => {
        this.handleNewSignal(newSignal);
      });

    // Listen to notifications
    this.webSocketService.onNotification()
      .pipe(takeUntil(this.destroy$))
      .subscribe(notification => {
        this.messageService.add({
          severity: notification.severity || 'info',
          summary: notification.title || 'Értesítés',
          detail: notification.message,
          life: notification.life || 5000
        });
      });
  }

  private handleNewSignal(newSignal: Signal): void {
    // Add timestamp if not present
    if (!newSignal.timestamp) {
      newSignal.timestamp = new Date().toISOString();
    }

    // Check if signal already exists (avoid duplicates)
    const existingIndex = this.allSignals.findIndex(s => 
      s.symbol === newSignal.symbol && 
      s.timestamp === newSignal.timestamp
    );

    if (existingIndex === -1) {
      // Add new signal to the beginning of the array
      this.allSignals.unshift(newSignal);
      
      // Keep only last 100 signals to prevent memory issues
      if (this.allSignals.length > 100) {
        this.allSignals = this.allSignals.slice(0, 100);
      }
      
      // Reapply filters
      this.applyFilters();
      
      // Show notification
      this.showNewSignalNotification(newSignal);
      
      // Auto-select if no signal is currently selected
      if (!this.selectedSignal) {
        this.selectedSignal = newSignal;
      }
    }
  }
}