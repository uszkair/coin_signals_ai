import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DropdownModule } from 'primeng/dropdown';
import { MultiSelectModule } from 'primeng/multiselect';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ProgressBarModule } from 'primeng/progressbar';
import { TabViewModule } from 'primeng/tabview';
import { ChartModule } from 'primeng/chart';
import { TagModule } from 'primeng/tag';
import { MessageService } from 'primeng/api';

import { BacktestService, BacktestRequest, BacktestResult, BacktestDetails, DataStatus } from '../../services/backtest.service';

@Component({
  selector: 'app-backtest',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    CardModule,
    DropdownModule,
    MultiSelectModule,
    InputNumberModule,
    InputTextModule,
    TableModule,
    ToastModule,
    ProgressBarModule,
    TabViewModule,
    ChartModule,
    TagModule
  ],
  providers: [MessageService],
  templateUrl: './backtest.component.html'
})
export class BacktestComponent implements OnInit {
  // Data management
  availableSymbols: string[] = [];
  availableSymbolOptions: any[] = [];
  selectedSymbols: string[] = [];
  symbolsSource: string = '';
  symbolsDescription: string = '';
  dataStatuses: { [symbol: string]: DataStatus } = {};
  isDataFetching = false;
  isDataRefreshing = false;
  dataFetchProgress = 0;

  // Backtest configuration
  backtestSymbols: string[] = [];
  backtestConfig: BacktestRequest = {
    test_name: '',
    symbol: 'BTCUSDT',
    days_back: 365,
    min_confidence: 70,
    position_size: 100
  };

  // Results
  backtestResults: BacktestResult[] = [];
  selectedResult: BacktestDetails | null = null;
  isRunningBacktest = false;

  // Chart data
  equityChartData: any = null;
  equityChartOptions: any = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Equity Curve'
      }
    },
    scales: {
      y: {
        beginAtZero: false
      }
    }
  };

  constructor(
    private backtestService: BacktestService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.loadAvailableSymbols();
    this.loadBacktestResults();
  }

  loadAvailableSymbols() {
    this.backtestService.getAvailableSymbols().subscribe({
      next: (response) => {
        this.availableSymbols = response.symbols;
        this.symbolsSource = response.source || 'unknown';
        this.symbolsDescription = response.description || 'Elérhető szimbólumok';
        
        this.availableSymbolOptions = response.symbols.map(symbol => ({
          label: symbol,
          value: symbol
        }));
        
        // Select all available symbols by default since they are the exact ones used by the trading engine
        this.selectedSymbols = [...response.symbols];
        this.checkDataStatuses();
        
        // Show info about symbol source
        this.messageService.add({
          severity: 'info',
          summary: 'Szimbólumok betöltve',
          detail: `${response.symbols.length} szimbólum betöltve: ${this.symbolsDescription}`,
          life: 5000
        });
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: 'Nem sikerült betölteni a szimbólumokat'
        });
      }
    });
  }

  checkDataStatuses() {
    this.selectedSymbols.forEach(symbol => {
      this.backtestService.getDataStatus(symbol).subscribe({
        next: (status) => {
          this.dataStatuses[symbol] = status;
        },
        error: (error) => {
          console.error(`Error checking data status for ${symbol}:`, error);
        }
      });
    });
  }

  selectAllSymbols() {
    this.selectedSymbols = [...this.availableSymbols];
    this.checkDataStatuses();
    this.messageService.add({
      severity: 'info',
      summary: 'Információ',
      detail: `${this.selectedSymbols.length} szimbólum kiválasztva`
    });
  }

  clearAllSymbols() {
    this.selectedSymbols = [];
    this.dataStatuses = {};
    this.messageService.add({
      severity: 'info',
      summary: 'Információ',
      detail: 'Összes szimbólum törölve'
    });
  }

  useSelectedSymbolsForBacktest() {
    this.backtestSymbols = [...this.selectedSymbols];
    this.messageService.add({
      severity: 'success',
      summary: 'Siker',
      detail: `${this.backtestSymbols.length} szimbólum átmásolva backtesthez`
    });
  }

  fetchHistoricalData(forceRefresh: boolean = false) {
    if (this.selectedSymbols.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Figyelmeztetés',
        detail: 'Válassz ki legalább egy szimbólumot'
      });
      return;
    }

    // Set the appropriate loading state based on the operation
    if (forceRefresh) {
      this.isDataFetching = true;
    } else {
      this.isDataRefreshing = true;
    }
    this.dataFetchProgress = 0;

    const request = {
      symbols: this.selectedSymbols,
      days: 365,
      force_refresh: forceRefresh
    };

    const actionType = forceRefresh ? 'teljes újratöltése' : 'frissítése';
    
    this.backtestService.fetchHistoricalData(request).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Siker',
          detail: `Adatok ${actionType} elindítva ${this.selectedSymbols.length} szimbólumhoz`
        });
        
        // Simulate progress (since it's background task)
        this.simulateProgress();
      },
      error: (error) => {
        this.isDataFetching = false;
        this.isDataRefreshing = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: `Nem sikerült elindítani az adatok ${actionType}t`
        });
      }
    });
  }

  simulateProgress() {
    const interval = setInterval(() => {
      this.dataFetchProgress += 10;
      if (this.dataFetchProgress >= 100) {
        this.dataFetchProgress = 100;
        this.isDataFetching = false;
        this.isDataRefreshing = false;
        clearInterval(interval);
        this.checkDataStatuses(); // Refresh data statuses
        this.messageService.add({
          severity: 'info',
          summary: 'Információ',
          detail: 'Adatok letöltése befejeződött'
        });
      }
    }, 1000);
  }

  runBacktest() {
    if (!this.backtestConfig.test_name.trim()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Figyelmeztetés',
        detail: 'Add meg a teszt nevét'
      });
      return;
    }

    if (this.backtestSymbols.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Figyelmeztetés',
        detail: 'Válassz ki legalább egy szimbólumot backtesthez'
      });
      return;
    }

    this.isRunningBacktest = true;
    let completedTests = 0;
    const totalTests = this.backtestSymbols.length;

    this.messageService.add({
      severity: 'info',
      summary: 'Backtest indítása',
      detail: `${totalTests} szimbólum tesztelése megkezdődött...`
    });

    // Run backtest for each symbol
    this.backtestSymbols.forEach((symbol, index) => {
      const testConfig = {
        ...this.backtestConfig,
        symbol: symbol,
        test_name: `${this.backtestConfig.test_name} - ${symbol}`
      };

      this.backtestService.runBacktest(testConfig).subscribe({
        next: (response) => {
          completedTests++;
          this.messageService.add({
            severity: 'success',
            summary: 'Siker',
            detail: `${symbol} backtest befejezve (${completedTests}/${totalTests})`
          });

          // If this is the last test, finish up
          if (completedTests === totalTests) {
            this.isRunningBacktest = false;
            this.loadBacktestResults();
            this.messageService.add({
              severity: 'success',
              summary: 'Összes backtest kész',
              detail: `Mind a ${totalTests} szimbólum tesztelése befejeződött`
            });
          }
        },
        error: (error) => {
          completedTests++;
          this.messageService.add({
            severity: 'error',
            summary: 'Hiba',
            detail: `${symbol}: ${error.error?.detail || 'Hiba történt a backtest során'}`
          });

          // If this is the last test (even if failed), finish up
          if (completedTests === totalTests) {
            this.isRunningBacktest = false;
            this.loadBacktestResults();
          }
        }
      });
    });
  }

  loadBacktestResults() {
    this.backtestService.getBacktestResults().subscribe({
      next: (response) => {
        this.backtestResults = response.results;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: 'Nem sikerült betölteni a backtest eredményeket'
        });
      }
    });
  }

  viewBacktestDetails(backtestId: number) {
    this.backtestService.getBacktestDetails(backtestId).subscribe({
      next: (details) => {
        this.selectedResult = details;
        this.generateEquityChart(details);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: 'Nem sikerült betölteni a backtest részleteit'
        });
      }
    });
  }

  generateEquityChart(details: BacktestDetails) {
    // Generate equity curve from trades
    let equity = details.summary.position_size;
    const equityPoints = [equity];
    const labels = ['Start'];

    details.trades.forEach((trade, index) => {
      equity += trade.profit_usd;
      equityPoints.push(equity);
      labels.push(`Trade ${index + 1}`);
    });

    this.equityChartData = {
      labels: labels,
      datasets: [
        {
          label: 'Equity (USD)',
          data: equityPoints,
          borderColor: '#42A5F5',
          backgroundColor: 'rgba(66, 165, 245, 0.1)',
          fill: true,
          tension: 0.4
        }
      ]
    };
  }

  deleteBacktest(backtestId: number) {
    this.backtestService.deleteBacktest(backtestId).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Siker',
          detail: 'Backtest törölve'
        });
        this.loadBacktestResults();
        if (this.selectedResult?.summary.id === backtestId) {
          this.selectedResult = null;
        }
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: 'Nem sikerült törölni a backtest-et'
        });
      }
    });
  }

  getResultSeverity(result: string): string {
    switch (result) {
      case 'profit': return 'success';
      case 'loss': return 'danger';
      default: return 'info';
    }
  }

  getDataStatusSeverity(hasData: boolean): string {
    return hasData ? 'success' : 'danger';
  }

  getDataStatusText(hasData: boolean): string {
    return hasData ? 'Elérhető' : 'Hiányzik';
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  }

  formatPercent(value: number): string {
    return new Intl.NumberFormat('hu-HU', {
      style: 'percent',
      minimumFractionDigits: 2
    }).format(value / 100);
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('hu-HU');
  }
}