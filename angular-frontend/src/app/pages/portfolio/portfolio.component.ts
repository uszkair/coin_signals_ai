import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { take } from 'rxjs';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';

import { PortfolioService, PortfolioStats, ProfitTimeline, CoinProfit } from '../../services/portfolio.service';

interface TimeframeOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-portfolio',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ChartModule,
    DropdownModule,
    ButtonModule,
    TableModule,
    TagModule
  ],
  templateUrl: './portfolio.component.html',
  styleUrls: []
})
export class PortfolioComponent implements OnInit {
  loading = false;
  selectedTimeframe = '30d';
  
  portfolioStats: PortfolioStats | null = null;
  profitTimeline: ProfitTimeline[] = [];
  coinProfits: CoinProfit[] = [];
  
  lineChartData: any = {};
  lineChartOptions: any = {};
  pieChartData: any = {};
  pieChartOptions: any = {};

  timeframeOptions: TimeframeOption[] = [
    { label: '7 nap', value: '7d' },
    { label: '30 nap', value: '30d' },
    { label: '90 nap', value: '90d' },
    { label: '1 év', value: '1y' }
  ];

  constructor(private portfolioService: PortfolioService) {
    this.initChartOptions();
  }

  ngOnInit(): void {
    this.loadPortfolioData();
  }

  onTimeframeChange(): void {
    this.loadPortfolioData();
  }

  refreshData(): void {
    this.loadPortfolioData();
  }

  private loadPortfolioData(): void {
    this.loading = true;
    
    this.portfolioService.getTradeStats(this.selectedTimeframe)
      .pipe(take(1))
      .subscribe({
        next: (data) => {
          this.portfolioStats = data.stats;
          this.profitTimeline = data.profit_timeline;
          this.coinProfits = data.coin_profits;
          
          this.updateCharts();
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading portfolio data:', error);
          this.loading = false;
        }
      });
  }

  private updateCharts(): void {
    this.updateLineChart();
    this.updatePieChart();
  }

  private updateLineChart(): void {
    const labels = this.profitTimeline.map(item => 
      new Date(item.date).toLocaleDateString('hu-HU', { month: 'short', day: 'numeric' })
    );
    const data = this.profitTimeline.map(item => item.cumulative_profit);

    this.lineChartData = {
      labels: labels,
      datasets: [
        {
          label: 'Kumulatív profit (%)',
          data: data,
          fill: false,
          borderColor: '#3b82f6',
          backgroundColor: '#3b82f6',
          tension: 0.4
        }
      ]
    };
  }

  private updatePieChart(): void {
    const labels = this.coinProfits.map(coin => coin.symbol);
    const data = this.coinProfits.map(coin => Math.abs(coin.profit_percent));
    const colors = [
      '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
      '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6b7280'
    ];

    this.pieChartData = {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: colors.slice(0, labels.length),
          borderWidth: 2,
          borderColor: '#ffffff'
        }
      ]
    };
  }

  private initChartOptions(): void {
    this.lineChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Dátum'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Profit (%)'
          }
        }
      }
    };

    this.pieChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'right'
        }
      }
    };
  }

  getProfitClass(profit: number): string {
    if (profit > 0) return 'text-green-600';
    if (profit < 0) return 'text-red-600';
    return 'text-gray-600';
  }

  getPerformanceLabel(profit: number): string {
    if (profit > 10) return 'Kiváló';
    if (profit > 5) return 'Jó';
    if (profit > 0) return 'Pozitív';
    if (profit > -5) return 'Gyenge';
    return 'Rossz';
  }

  getPerformanceSeverity(profit: number): 'success' | 'warning' | 'danger' | 'info' {
    if (profit > 5) return 'success';
    if (profit > 0) return 'info';
    if (profit > -5) return 'warning';
    return 'danger';
  }
}