import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { take, takeUntil, Subject, interval } from 'rxjs';

// PrimeNG imports
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { ToolbarModule } from 'primeng/toolbar';
import { CardModule } from 'primeng/card';
import { TabViewModule } from 'primeng/tabview';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';

import { HistoryService, TradeHistory } from '../../services/history.service';
import { TradingService } from '../../services/trading.service';

interface LivePosition {
  symbol: string;
  position_side: string;
  position_amt: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  pnl_percentage: number;
  stop_loss_price?: number;
  take_profit_price?: number;
  position_type: string;
  leverage?: number;
  margin_type?: string;
  update_time?: number;
}

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
    CardModule,
    TabViewModule,
    ProgressSpinnerModule,
    TooltipModule,
    ConfirmDialogModule,
    ToastModule
  ],
  templateUrl: './history.component.html',
  styleUrls: []
})
export class HistoryComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  loading = false;
  tradeHistory: TradeHistory[] = [];
  
  // Live Positions
  livePositions: LivePosition[] = [];
  loadingLivePositions = false;
  livePositionsError: string | null = null;
  lastPositionsUpdate: Date | null = null;
  loadingClosePosition: string | null = null;
  
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

  constructor(
    private historyService: HistoryService,
    private tradingService: TradingService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadTradeHistory();
    this.loadTradingStatistics();
    this.loadDailySummary();
    this.loadLivePositions();
    this.startSmartPnlRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
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

  // Live Positions Methods
  private loadLivePositions(): void {
    this.loadingLivePositions = true;
    this.livePositionsError = null;
    
    this.tradingService.getLivePositions()
      .pipe(take(1))
      .subscribe({
        next: (response) => {
          this.loadingLivePositions = false;
          if (response.success) {
            this.livePositions = response.data.positions || [];
            // Additional frontend sorting to ensure consistent order
            this.sortLivePositions();
            this.lastPositionsUpdate = new Date();
            this.livePositionsError = null;
            
            // Immediately update with fresh P&L data for perfect sync
            setTimeout(() => {
              this.updatePositionsPnl();
            }, 100); // Small delay to ensure positions are loaded
          } else {
            this.livePositions = [];
            this.livePositionsError = response.error || 'Failed to load live positions';
          }
        },
        error: (error) => {
          this.loadingLivePositions = false;
          this.livePositions = [];
          this.livePositionsError = 'Network error loading live positions';
          console.error('Error loading live positions:', error);
        }
      });
  }

  private startSmartPnlRefresh(): void {
    // Smart P&L refresh: only update changing values every 1 second for better sync
    interval(1000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.updatePositionsPnl();
      });
  }

  private updatePositionsPnl(): void {
    // Only update P&L data and exit prices to avoid visual disruption
    this.tradingService.getLivePositionsPnlOnly()
      .pipe(take(1))
      .subscribe({
        next: (response) => {
          if (response.success && response.data.pnl_updates) {
            // Update only P&L values and exit prices in existing positions
            response.data.pnl_updates.forEach((update: any) => {
              const existingPosition = this.livePositions.find(pos => pos.symbol === update.symbol);
              if (existingPosition) {
                // Force update with fresh Binance data - ensure perfect sync
                existingPosition.mark_price = update.mark_price;
                existingPosition.unrealized_pnl = update.unrealized_pnl; // Direct from Binance API
                existingPosition.pnl_percentage = update.pnl_percentage; // Calculated from Binance P&L
                existingPosition.stop_loss_price = update.stop_loss_price;
                existingPosition.take_profit_price = update.take_profit_price;
                existingPosition.update_time = update.update_time;
              }
            });
            this.lastPositionsUpdate = new Date();
            
            // Log for debugging sync issues
            console.log('P&L updated from Binance:', response.data.pnl_updates.length, 'positions');
          } else {
            console.warn('No P&L updates received from Binance API');
          }
        },
        error: (error) => {
          console.error('Error updating P&L:', error);
          // Fallback to full refresh if P&L-only fails
          this.loadLivePositions();
        }
      });
  }

  refreshLivePositions(): void {
    this.loadLivePositions();
  }

  forceSyncWithBinance(): void {
    // Force immediate sync with Binance by clearing any cache and refreshing
    this.loadingLivePositions = true;
    this.livePositionsError = null;
    
    // First get fresh P&L data
    this.tradingService.getLivePositionsPnlOnly()
      .pipe(take(1))
      .subscribe({
        next: (pnlResponse) => {
          if (pnlResponse.success && pnlResponse.data.pnl_updates) {
            // Update P&L immediately
            pnlResponse.data.pnl_updates.forEach((update: any) => {
              const existingPosition = this.livePositions.find(pos => pos.symbol === update.symbol);
              if (existingPosition) {
                existingPosition.mark_price = update.mark_price;
                existingPosition.unrealized_pnl = update.unrealized_pnl;
                existingPosition.pnl_percentage = update.pnl_percentage;
                existingPosition.stop_loss_price = update.stop_loss_price;
                existingPosition.take_profit_price = update.take_profit_price;
                existingPosition.update_time = update.update_time;
              }
            });
            
            this.messageService.add({
              severity: 'success',
              summary: 'Szinkronizáció sikeres',
              detail: `${pnlResponse.data.pnl_updates.length} pozíció frissítve a Binance adatokkal`,
              life: 3000
            });
          }
          
          // Then refresh full positions to ensure complete sync
          this.loadLivePositions();
        },
        error: (error) => {
          this.loadingLivePositions = false;
          this.messageService.add({
            severity: 'error',
            summary: 'Szinkronizációs hiba',
            detail: 'Nem sikerült szinkronizálni a Binance-szel',
            life: 5000
          });
          console.error('Force sync error:', error);
        }
      });
  }

  emergencyStopAllPositions(): void {
    this.confirmationService.confirm({
      message: 'Biztosan le szeretnéd zárni az ÖSSZES pozíciót és leállítani a kereskedést? Ez a művelet visszafordíthatatlan!',
      header: 'Összes pozíció lezárása',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Igen, lezárom mind',
      rejectLabel: 'Mégse',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.loadingLivePositions = true;
        
        this.tradingService.emergencyStop()
          .pipe(take(1))
          .subscribe({
            next: (response) => {
              this.loadingLivePositions = false;
              if (response.success) {
                this.messageService.add({
                  severity: 'success',
                  summary: 'Sikeres leállítás',
                  detail: 'Összes pozíció lezárva és kereskedés leállítva.',
                  life: 5000
                });
                // Frissítjük a pozíciókat
                this.loadLivePositions();
              } else {
                this.messageService.add({
                  severity: 'error',
                  summary: 'Hiba történt',
                  detail: response.error || 'Ismeretlen hiba a leállítás során',
                  life: 5000
                });
              }
            },
            error: (error) => {
              this.loadingLivePositions = false;
              this.messageService.add({
                severity: 'error',
                summary: 'Hiba történt',
                detail: error.message || 'Ismeretlen hiba a leállítás során',
                life: 5000
              });
              console.error('Emergency stop error:', error);
            }
          });
      }
    });
  }

  getPositionSideSeverity(side: string): 'success' | 'danger' {
    return side === 'BUY' ? 'success' : 'danger';
  }

  getPositionPnlClass(pnl: number): string {
    if (pnl > 0) return 'text-green-600 font-bold';
    if (pnl < 0) return 'text-red-600 font-bold';
    return 'text-gray-600';
  }

  getPositionPnlPercentageClass(percentage: number): string {
    if (percentage > 0) return 'text-green-600 font-medium';
    if (percentage < 0) return 'text-red-600 font-medium';
    return 'text-gray-600';
  }

  getTotalUnrealizedPnl(): number {
    return this.livePositions.reduce((total, pos) => total + pos.unrealized_pnl, 0);
  }

  getTotalPositionValue(): number {
    return this.livePositions.reduce((total, pos) => total + (pos.position_amt * pos.entry_price), 0);
  }

  getLivePositionsStats() {
    const stats = {
      totalPositions: this.livePositions.length,
      longPositions: this.livePositions.filter(p => p.position_side === 'BUY').length,
      shortPositions: this.livePositions.filter(p => p.position_side === 'SELL').length,
      totalUnrealizedPnl: this.getTotalUnrealizedPnl(),
      totalPositionValue: this.getTotalPositionValue(),
      profitablePositions: this.livePositions.filter(p => p.unrealized_pnl > 0).length,
      losingPositions: this.livePositions.filter(p => p.unrealized_pnl < 0).length
    };
    
    return stats;
  }

  private sortLivePositions(): void {
    // Sort positions by update_time (newest first) - represents position creation/modification time
    this.livePositions.sort((a, b) => {
      const timeA = a.update_time || 0;
      const timeB = b.update_time || 0;
      return timeB - timeA; // Newest first
    });
  }

  getExpectedReturn(position: LivePosition): { usd: number, percentage: number } | null {
    // Várható hozam számítása a take profit ár alapján
    if (!position.take_profit_price || !position.entry_price || !position.position_amt) {
      return null;
    }

    const priceDifference = position.take_profit_price - position.entry_price;
    const expectedReturnUsd = Math.abs(priceDifference * position.position_amt);
    const expectedReturnPercentage = (priceDifference / position.entry_price) * 100;

    return {
      usd: expectedReturnUsd,
      percentage: Math.abs(expectedReturnPercentage)
    };
  }

  getExpectedReturnClass(expectedReturn: { usd: number, percentage: number } | null): string {
    if (!expectedReturn) return 'text-gray-400';
    return 'text-green-600 font-medium';
  }

  closePosition(symbol: string): void {
    this.confirmationService.confirm({
      message: `Biztosan le szeretnéd zárni a ${symbol} pozíciót? Ez a művelet azonnal lezárja a pozíciót a jelenlegi piaci áron.`,
      header: 'Pozíció lezárása',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Igen, lezárom',
      rejectLabel: 'Mégse',
      accept: () => {
        this.loadingClosePosition = symbol;
        
        this.tradingService.closePositionBySymbol(symbol, 'manual_close')
          .pipe(take(1))
          .subscribe({
            next: (response) => {
              this.loadingClosePosition = null;
              if (response.success) {
                this.messageService.add({
                  severity: 'success',
                  summary: 'Sikeres lezárás',
                  detail: `${symbol} pozíció sikeresen lezárva! Order ID: ${response.data?.order_id || 'N/A'}`,
                  life: 5000
                });
                // Frissítjük a pozíciókat
                this.loadLivePositions();
              } else {
                this.messageService.add({
                  severity: 'error',
                  summary: 'Hiba történt',
                  detail: response.error || 'Ismeretlen hiba a pozíció lezárásakor',
                  life: 5000
                });
              }
            },
            error: (error) => {
              this.loadingClosePosition = null;
              this.messageService.add({
                severity: 'error',
                summary: 'Hiba történt',
                detail: error.message || 'Ismeretlen hiba a pozíció lezárásakor',
                life: 5000
              });
              console.error('Close position error:', error);
            }
          });
      }
    });
  }
}