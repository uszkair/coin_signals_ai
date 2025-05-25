import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject, combineLatest } from 'rxjs';
import { catchError, retry, shareReplay, switchMap, map, tap, finalize } from 'rxjs/operators';
import { TradeHistoryFilter, TradeHistoryResponse } from '../models';

@Injectable({
  providedIn: 'root'
})
export class HistoryService {
  private apiUrl = '/api';
  
  // Current filter subject
  private filterSubject = new BehaviorSubject<TradeHistoryFilter>({
    page: 1,
    pageSize: 10,
    resultType: 'all'
  });
  
  // Loading state subject
  private loadingSubject = new BehaviorSubject<boolean>(false);
  
  // Expose as observables
  currentFilter$ = this.filterSubject.asObservable();
  loading$ = this.loadingSubject.asObservable();
  
  // Trade history observable
  tradeHistory$ = this.filterSubject.pipe(
    switchMap(filter => this.fetchTradeHistory(filter)),
    shareReplay(1)
  );

  constructor(private http: HttpClient) { }
  
  /**
   * Update filter and trigger new data fetch
   */
  updateFilter(filter: Partial<TradeHistoryFilter>): void {
    const currentFilter = this.filterSubject.getValue();
    this.filterSubject.next({ ...currentFilter, ...filter });
  }
  
  /**
   * Reset filter to defaults
   */
  resetFilter(): void {
    this.filterSubject.next({
      page: 1,
      pageSize: 10,
      resultType: 'all'
    });
  }

  /**
   * Get trading history with optional filters
   */
  getTradeHistory(filter: TradeHistoryFilter): Observable<TradeHistoryResponse> {
    return this.fetchTradeHistory(filter);
  }
  
  /**
   * Fetch trade history from API
   */
  private fetchTradeHistory(filter: TradeHistoryFilter): Observable<TradeHistoryResponse> {
    this.loadingSubject.next(true);
    
    let params = this.buildParams(filter);

    return this.http.get<TradeHistoryResponse>(`${this.apiUrl}/history`, { params })
      .pipe(
        retry(1),
        catchError(this.handleError),
        tap(() => this.loadingSubject.next(false)),
        finalize(() => this.loadingSubject.next(false))
      );
  }

  /**
   * Export trade history to CSV
   */
  exportToCsv(filter: TradeHistoryFilter): Observable<Blob> {
    let params = this.buildParams(filter);

    return this.http.get(`${this.apiUrl}/history/export`, {
      params,
      responseType: 'blob'
    }).pipe(
      catchError(this.handleError)
    );
  }
  
  /**
   * Build HTTP params from filter
   */
  private buildParams(filter: TradeHistoryFilter): HttpParams {
    let params = new HttpParams()
      .set('page', filter.page.toString())
      .set('pageSize', filter.pageSize.toString());

    if (filter.symbol) {
      params = params.set('symbol', filter.symbol);
    }

    if (filter.dateFrom) {
      params = params.set('dateFrom', filter.dateFrom.toISOString());
    }

    if (filter.dateTo) {
      params = params.set('dateTo', filter.dateTo.toISOString());
    }

    if (filter.patternType) {
      params = params.set('patternType', filter.patternType);
    }

    if (filter.resultType && filter.resultType !== 'all') {
      params = params.set('resultType', filter.resultType);
    }
    
    return params;
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