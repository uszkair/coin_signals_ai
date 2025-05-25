import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, of, BehaviorSubject } from 'rxjs';
import { catchError, retry, shareReplay, tap, map, switchMap } from 'rxjs/operators';
import { CurrentSignal, Signal, SignalHistory } from '../models';

@Injectable({
  providedIn: 'root'
})
export class SignalService {
  private apiUrl = '/api';
  
  // Cache for symbols and intervals
  private symbolsCache$: Observable<string[]> | null = null;
  private intervalsCache$: Observable<string[]> | null = null;
  
  // Current selected symbol and interval
  private currentSymbolSubject = new BehaviorSubject<string>('BTCUSDT');
  private currentIntervalSubject = new BehaviorSubject<string>('1h');
  
  // Expose as observables
  currentSymbol$ = this.currentSymbolSubject.asObservable();
  currentInterval$ = this.currentIntervalSubject.asObservable();
  
  // Combined signal observable
  currentSignal$ = this.createCurrentSignalObservable();

  constructor(private http: HttpClient) { }

  /**
   * Set current symbol
   */
  setSymbol(symbol: string): void {
    this.currentSymbolSubject.next(symbol);
  }
  
  /**
   * Set current interval
   */
  setInterval(interval: string): void {
    this.currentIntervalSubject.next(interval);
  }
  
  /**
   * Create an observable that updates when symbol or interval changes
   */
  private createCurrentSignalObservable(): Observable<CurrentSignal> {
    return this.currentSymbolSubject.pipe(
      switchMap(symbol =>
        this.currentIntervalSubject.pipe(
          switchMap(interval => this.fetchCurrentSignal(symbol, interval))
        )
      )
    );
  }

  /**
   * Get the current signal for a specific symbol and interval
   */
  getCurrentSignal(symbol: string, interval: string): Observable<CurrentSignal> {
    return this.fetchCurrentSignal(symbol, interval);
  }
  
  /**
   * Fetch current signal from API
   */
  private fetchCurrentSignal(symbol: string, interval: string): Observable<CurrentSignal> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('interval', interval);

    return this.http.get<CurrentSignal>(`${this.apiUrl}/signal/current`, { params })
      .pipe(
        retry(2),
        catchError(this.handleError),
        shareReplay(1)
      );
  }

  /**
   * Get signal history for a specific symbol and time period
   */
  getSignalHistory(symbol: string, days: number): Observable<SignalHistory> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('days', days.toString());

    return this.http.get<SignalHistory>(`${this.apiUrl}/signal/history`, { params })
      .pipe(
        retry(1),
        catchError(this.handleError),
        shareReplay(1)
      );
  }

  /**
   * Get available symbols for trading
   */
  getAvailableSymbols(): Observable<string[]> {
    if (!this.symbolsCache$) {
      this.symbolsCache$ = this.http.get<string[]>(`${this.apiUrl}/signal/symbols`)
        .pipe(
          retry(3),
          catchError(this.handleError),
          shareReplay(1)
        );
    }
    return this.symbolsCache$;
  }

  /**
   * Get available intervals for trading
   */
  getAvailableIntervals(): Observable<string[]> {
    if (!this.intervalsCache$) {
      this.intervalsCache$ = this.http.get<string[]>(`${this.apiUrl}/signal/intervals`)
        .pipe(
          retry(3),
          catchError(this.handleError),
          shareReplay(1)
        );
    }
    return this.intervalsCache$;
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