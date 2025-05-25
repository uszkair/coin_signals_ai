import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject, of } from 'rxjs';
import { catchError, retry, shareReplay, switchMap, tap, map, finalize, delay } from 'rxjs/operators';
import { PortfolioSummary } from '../models';

@Injectable({
  providedIn: 'root'
})
export class PortfolioService {
  private apiUrl = '/api';
  
  // Selected time period subject
  private periodSubject = new BehaviorSubject<'day' | 'week' | 'month' | 'year'>('month');
  
  // Loading state subject
  private loadingSubject = new BehaviorSubject<boolean>(false);
  
  // Expose as observables
  currentPeriod$ = this.periodSubject.asObservable();
  loading$ = this.loadingSubject.asObservable();
  
  // Portfolio data observable
  portfolioData$ = this.periodSubject.pipe(
    tap(() => this.loadingSubject.next(true)),
    switchMap(period => this.fetchPortfolioPerformance(period)),
    tap(() => this.loadingSubject.next(false)),
    shareReplay(1)
  );
  
  // Daily profit data for chart
  dailyProfitChartData$ = this.portfolioData$.pipe(
    map(data => this.prepareDailyProfitChartData(data)),
    shareReplay(1)
  );
  
  // Coin performance data for chart
  coinPerformanceChartData$ = this.portfolioData$.pipe(
    map(data => this.prepareCoinPerformanceChartData(data)),
    shareReplay(1)
  );

  constructor(private http: HttpClient) { }
  
  /**
   * Set the time period for portfolio data
   */
  setPeriod(period: 'day' | 'week' | 'month' | 'year'): void {
    this.periodSubject.next(period);
  }

  /**
   * Get portfolio summary data
   */
  getPortfolioSummary(): Observable<PortfolioSummary> {
    this.loadingSubject.next(true);
    
    return this.http.get<PortfolioSummary>(`${this.apiUrl}/portfolio/summary`)
      .pipe(
        retry(1),
        catchError(this.handleError),
        finalize(() => this.loadingSubject.next(false)),
        shareReplay(1)
      );
  }

  /**
   * Get portfolio performance for a specific time period
   */
  getPortfolioPerformance(period: 'day' | 'week' | 'month' | 'year' = 'month'): Observable<PortfolioSummary> {
    return this.fetchPortfolioPerformance(period);
  }
  
  /**
   * Fetch portfolio performance from API
   */
  private fetchPortfolioPerformance(period: 'day' | 'week' | 'month' | 'year'): Observable<PortfolioSummary> {
    return this.http.get<PortfolioSummary>(`${this.apiUrl}/portfolio/performance`, {
      params: { period }
    }).pipe(
      retry(1),
      catchError(this.handleError),
      shareReplay(1)
    );
  }
  
  /**
   * Prepare data for daily profit chart
   */
  private prepareDailyProfitChartData(data: PortfolioSummary): any {
    const dates = data.dailyProfits.map(item => item.date);
    const profits = data.dailyProfits.map(item => item.profit);
    
    return {
      labels: dates,
      datasets: [
        {
          label: 'Daily Profit (USD)',
          data: profits,
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          borderColor: '#3b82f6',
          borderWidth: 1
        }
      ]
    };
  }
  
  /**
   * Prepare data for coin performance chart
   */
  private prepareCoinPerformanceChartData(data: PortfolioSummary): any {
    const coinLabels = data.coinPerformance.map(item => item.symbol);
    const coinProfits = data.coinPerformance.map(item => item.profit);
    
    return {
      labels: coinLabels,
      datasets: [
        {
          label: 'Profit by Coin (USD)',
          data: coinProfits,
          backgroundColor: [
            '#3b82f6',
            '#8b5cf6',
            '#ec4899',
            '#f97316',
            '#eab308',
            '#22c55e',
            '#14b8a6',
            '#0ea5e9'
          ]
        }
      ]
    };
  }
  
  /**
   * Error handler for HTTP requests
   */
  private handleError(error: HttpErrorResponse) {
    let errorMessage = '';
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}