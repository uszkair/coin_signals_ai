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
  dataStatuses: { [symbol: string]: DataStatus } = {};
  isDataFetching = false;
  dataFetchProgress = 0;

  // Backtest configuration
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
        this.availableSymbolOptions = response.symbols.map(symbol => ({
          label: symbol,
          value: symbol
        }));
        this.selectedSymbols = response.symbols.slice(0, 5); // Select first 5 by default
        this.checkDataStatuses();
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

  fetchHistoricalData() {
    if (this.selectedSymbols.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Figyelmeztetés',
        detail: 'Válassz ki legalább egy szimbólumot'
      });
      return;
    }

    this.isDataFetching = true;
    this.dataFetchProgress = 0;

    const request = {
      symbols: this.selectedSymbols,
      days: 365
    };

    this.backtestService.fetchHistoricalData(request).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Siker',
          detail: `Adatok letöltése elindítva ${this.selectedSymbols.length} szimbólumhoz`
        });
        
        // Simulate progress (since it's background task)
        this.simulateProgress();
      },
      error: (error) => {
        this.isDataFetching = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: 'Nem sikerült elindítani az adatok letöltését'
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

    this.isRunningBacktest = true;

    this.backtestService.runBacktest(this.backtestConfig).subscribe({
      next: (response) => {
        this.isRunningBacktest = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Siker',
          detail: 'Backtest sikeresen lefutott'
        });
        this.loadBacktestResults();
        this.viewBacktestDetails(response.backtest_id);
      },
      error: (error) => {
        this.isRunningBacktest = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: error.error?.detail || 'Hiba történt a backtest futtatása során'
        });
      }
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