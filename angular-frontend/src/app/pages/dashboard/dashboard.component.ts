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
import { ToastModule } from 'primeng/toast';
import { InputSwitchModule } from 'primeng/inputswitch';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { ProgressBarModule } from 'primeng/progressbar';
import { SkeletonModule } from 'primeng/skeleton';
import { AccordionModule } from 'primeng/accordion';
import { DividerModule } from 'primeng/divider';
import { MessageService } from 'primeng/api';
import { ConfirmationService } from 'primeng/api';

import { SignalService, Signal } from '../../services/signal.service';
import { WebSocketService } from '../../services/websocket.service';
import { AIService, AIInsight } from '../../services/ai.service';
import { TradingViewWidgetComponent } from '../../components/trading-view-widget/trading-view-widget.component';
import { TradingService } from '../../services/trading.service';
import { AiMlService, AISignal } from '../../services/ai-ml.service';

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
    ToastModule,
    InputSwitchModule,
    ConfirmDialogModule,
    DialogModule,
    ProgressBarModule,
    SkeletonModule,
    AccordionModule,
    DividerModule,
    TradingViewWidgetComponent,
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
  selectedSignalAIAnalysis: AIInsight | null = null;
  selectedSignalAIML: AISignal | null = null;
  loadingAIAnalysis = false;
  loadingAIML = false;
  
  // Chart modal
  showChartModal = false;
  chartLocked = false; // Flag to prevent auto-selection when chart is open
  
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
    private webSocketService: WebSocketService,
    private aiService: AIService,
    private tradingService: TradingService,
    private aiMlService: AiMlService
  ) {}

  ngOnInit(): void {
    this.loadSignals();
    this.startAutoRefresh();
    this.setupWebSocketConnection();
    this.selectedSignal = this.filteredSignals[0];
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
          
          // Auto-select first signal if none selected (only if chart is not locked)
          if (!this.chartLocked && this.filteredSignals.length > 0 && !this.selectedSignal) {
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
  }

  selectSignal(signal: Signal): void {
    this.selectedSignal = signal;
    // Don't load AI analysis separately since decision factors are already in the signal
    this.loadingAIAnalysis = false;
    this.selectedSignalAIAnalysis = null;
    
    // Load AI/ML analysis for the selected signal
    this.loadAIMLAnalysis(signal);
  }

  loadAIMLAnalysis(signal: Signal): void {
    this.loadingAIML = true;
    this.selectedSignalAIML = null;
    
    this.aiMlService.getAISignal(signal.symbol, '1h').subscribe({
      next: (response) => {
        this.loadingAIML = false;
        if (response.success) {
          this.selectedSignalAIML = response.data;
        }
      },
      error: (error) => {
        this.loadingAIML = false;
        console.error('Error loading AI/ML analysis:', error);
      }
    });
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
      header: 'Automatikus Kereskedés Megerősítése',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.executeAutomaticTrade(signal);
      }
    });
  }

  executeAutomaticTrade(signal: Signal): void {
    this.loading = true;
    
    this.tradingService.executeSignalTrade(signal).subscribe({
      next: (result) => {
        this.loading = false;
        
        if (result.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Kereskedés Végrehajtva',
            detail: `${signal.signal} pozíció megnyitva: ${signal.symbol} @ $${signal.entry_price}`,
            life: 10000
          });
          
          // Show trade details
          if (result.data?.position_id) {
            this.messageService.add({
              severity: 'info',
              summary: 'Pozíció Részletek',
              detail: `Pozíció ID: ${result.data.position_id}, Várható profit: $${result.data.expected_profit?.toFixed(2) || 'N/A'}`,
              life: 15000
            });
          }
        } else {
          this.messageService.add({
            severity: 'warn',
            summary: 'Kereskedés Sikertelen',
            detail: result.data?.error || 'Ismeretlen hiba történt',
            life: 10000
          });
        }
      },
      error: (error) => {
        this.loading = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Kereskedési Hiba',
          detail: 'Nem sikerült végrehajtani a kereskedést: ' + error.message,
          life: 10000
        });
      }
    });
  }

  // Quick trade with current signal
  quickTrade(signal: Signal): void {
    this.confirmationService.confirm({
      message: `Gyors kereskedés: ${signal.signal} ${signal.symbol} @ $${signal.entry_price}?\n\nEz azonnal végrehajtja a kereskedést a jelenlegi piaci áron.`,
      header: 'Gyors Kereskedés',
      icon: 'pi pi-bolt',
      acceptLabel: 'Végrehajtás',
      rejectLabel: 'Mégse',
      accept: () => {
        this.tradingService.executeTrade({
          symbol: signal.symbol,
          interval: '1h',
          force_execute: true
        }).subscribe({
          next: (result) => {
            if (result.success) {
              this.messageService.add({
                severity: 'success',
                summary: 'Gyors Kereskedés Sikeres',
                detail: `${result.data?.signal_used?.signal} pozíció megnyitva`,
                life: 8000
              });
            } else {
              this.messageService.add({
                severity: 'error',
                summary: 'Gyors Kereskedés Sikertelen',
                detail: result.data?.trade_result?.error || 'Hiba történt',
                life: 8000
              });
            }
          },
          error: (error) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Kereskedési Hiba',
              detail: error.message,
              life: 8000
            });
          }
        });
      }
    });
  }

  // AI/ML Helper Methods
  getAISignalSeverity(aiSignal: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (aiSignal) {
      case 'BUY': return 'success';
      case 'SELL': return 'danger';
      case 'HOLD': return 'warning';
      default: return 'info';
    }
  }

  getAIConfidenceClass(confidence: number): string {
    if (confidence > 80) return 'text-green-600 dark:text-green-400';
    if (confidence > 60) return 'text-blue-600 dark:text-blue-400';
    if (confidence > 40) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  }

  getRiskScoreClass(riskScore: number): string {
    if (riskScore > 80) return 'text-red-600 dark:text-red-400';
    if (riskScore > 60) return 'text-orange-600 dark:text-orange-400';
    if (riskScore > 40) return 'text-yellow-600 dark:text-yellow-400';
    if (riskScore > 20) return 'text-green-600 dark:text-green-400';
    return 'text-blue-600 dark:text-blue-400';
  }

  getMarketRegimeIcon(regime: string): string {
    switch (regime) {
      case 'TRENDING': return 'pi pi-arrow-up-right';
      case 'RANGING': return 'pi pi-arrows-h';
      case 'VOLATILE': return 'pi pi-exclamation-triangle';
      default: return 'pi pi-question-circle';
    }
  }

  formatProbabilities(probabilities: any): string {
    if (!probabilities) return 'N/A';
    return `BUY: ${(probabilities.buy * 100).toFixed(1)}%, SELL: ${(probabilities.sell * 100).toFixed(1)}%, HOLD: ${(probabilities.hold * 100).toFixed(1)}%`;
  }


  showChart(signal: Signal): void {
    this.selectedSignal = signal;
    this.showChartModal = true;
    this.chartLocked = true; // Lock the selection to prevent auto-changes
  }

  closeChart(): void {
    this.showChartModal = false;
    this.chartLocked = false; // Unlock selection when chart is closed
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
      
      // Auto-select if no signal is currently selected (only if chart is not locked)
      if (!this.chartLocked && !this.selectedSignal) {
        this.selectedSignal = newSignal;
      }
    }
  }

  // Make Math available in template
  Math = Math;

  // Helper methods for AI analysis display
  getAISentimentColor(sentiment: number): string {
    if (sentiment > 0.3) return 'text-green-600';
    if (sentiment < -0.3) return 'text-red-600';
    return 'text-gray-600';
  }

  getAIConfidenceColor(confidence: number): string {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  }

  getRiskScoreColor(risk: number): string {
    if (risk <= 30) return 'text-green-600';
    if (risk <= 60) return 'text-yellow-600';
    return 'text-red-600';
  }

  // Helper methods for safe access to decision factors
  getDecisionFactorSignal(factorName: keyof NonNullable<Signal['decision_factors']>): string {
    const signal = (this.selectedSignal?.decision_factors as any)?.[factorName]?.signal || 'NEUTRAL';
    return signal === 'NEUTRAL' ? 'Semleges' : signal;
  }

  getDecisionFactorWeight(factorName: keyof NonNullable<Signal['decision_factors']>): number {
    return (this.selectedSignal?.decision_factors as any)?.[factorName]?.weight || 0;
  }

  getDecisionFactorReasoning(factorName: keyof NonNullable<Signal['decision_factors']>): string {
    return (this.selectedSignal?.decision_factors as any)?.[factorName]?.reasoning || 'Nincs adat';
  }

  getDecisionFactorValue(factorName: 'rsi_analysis' | 'macd_analysis'): number {
    return (this.selectedSignal?.decision_factors as any)?.[factorName]?.value || 0;
  }

  getDecisionFactorName(): string {
    return this.selectedSignal?.decision_factors?.candlestick_pattern?.name || 'Nincs';
  }

  getDecisionFactorScore(): number {
    return this.selectedSignal?.decision_factors?.candlestick_pattern?.score || 0;
  }

  getDecisionFactorTrend(): string {
    return this.selectedSignal?.decision_factors?.trend_analysis?.trend || 'N/A';
  }

  getDecisionFactorStrength(): string {
    return this.selectedSignal?.decision_factors?.momentum_strength?.strength || 'N/A';
  }

  getDecisionFactorSeverity(factorName: keyof NonNullable<Signal['decision_factors']>): string {
    const signal = this.getDecisionFactorSignal(factorName);
    return signal === 'BUY' ? 'success' : signal === 'SELL' ? 'danger' : 'secondary';
  }

  getDecisionFactorWeightClass(factorName: keyof NonNullable<Signal['decision_factors']>): string {
    const weight = this.getDecisionFactorWeight(factorName);
    return weight > 0 ? 'text-green-600' : weight < 0 ? 'text-red-600' : 'text-gray-600';
  }

  getDecisionFactorWeightDisplay(factorName: keyof NonNullable<Signal['decision_factors']>): string {
    const weight = this.getDecisionFactorWeight(factorName);
    if (weight === 0) return 'Nincs hatás';
    return `${weight > 0 ? '+' : ''}${weight} pont`;
  }

  getSignalStrengthText(totalScore: number): string {
    const absScore = Math.abs(totalScore);
    if (totalScore > 0) {
      return `BUY Erősség: ${absScore}/7`;
    } else if (totalScore < 0) {
      return `SELL Erősség: ${absScore}/7`;
    } else {
      return 'Semleges (0/7)';
    }
  }

  getSignalStrengthClass(totalScore: number): string {
    if (totalScore >= 3) return 'text-green-700 dark:text-green-400';
    if (totalScore >= 1) return 'text-green-600 dark:text-green-500';
    if (totalScore <= -3) return 'text-red-700 dark:text-red-400';
    if (totalScore <= -1) return 'text-red-600 dark:text-red-500';
    return 'text-gray-600 dark:text-gray-400';
  }
}