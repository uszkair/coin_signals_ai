import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ChartModule } from 'primeng/chart';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { PortfolioService } from '../../services';
import { PortfolioSummary } from '../../models';

import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-portfolio',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    TableModule,
    ChartModule,
    DropdownModule,
    ButtonModule,
    ProgressSpinnerModule
  ],
  templateUrl: './portfolio.component.html',
  styleUrl: './portfolio.component.scss'
})
export class PortfolioComponent implements OnInit, OnDestroy {
  // Portfolio data
  portfolioSummary$: Observable<PortfolioSummary>;
  
  // Chart data
  dailyProfitChartData$: Observable<any>;
  coinPerformanceChartData$: Observable<any>;
  
  // Loading state
  loading$: Observable<boolean>;
  
  // Chart options
  chartOptions = {
    plugins: {
      legend: {
        position: 'bottom'
      }
    },
    responsive: true,
    maintainAspectRatio: false
  };
  
  // Time period filter
  timePeriods = [
    { label: 'Last 7 Days', value: 'week' },
    { label: 'Last 30 Days', value: 'month' },
    { label: 'Last Year', value: 'year' }
  ];
  selectedPeriod = 'month';
  
  // Component destroy subject for cleanup
  private destroy$ = new Subject<void>();

  constructor(private portfolioService: PortfolioService) {
    // Initialize observables
    this.portfolioSummary$ = this.portfolioService.portfolioData$;
    this.dailyProfitChartData$ = this.portfolioService.dailyProfitChartData$;
    this.coinPerformanceChartData$ = this.portfolioService.coinPerformanceChartData$;
    this.loading$ = this.portfolioService.loading$;
  }

  ngOnInit(): void {
    // Subscribe to current period from service
    this.portfolioService.currentPeriod$
      .pipe(takeUntil(this.destroy$))
      .subscribe(period => {
        this.selectedPeriod = period;
      });
      
    // Set initial period
    this.portfolioService.setPeriod(this.selectedPeriod as any);
  }
  
  ngOnDestroy(): void {
    // Clean up subscriptions
    this.destroy$.next();
    this.destroy$.complete();
  }

  onPeriodChange(): void {
    this.portfolioService.setPeriod(this.selectedPeriod as any);
  }

  getProfitClass(profit: number): string {
    return profit >= 0 ? 'profit-positive' : 'profit-negative';
  }
  
  trackBySymbol(index: number, item: any): string {
    return item.symbol;
  }
}