import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject, combineLatest } from 'rxjs';
import { catchError, retry, shareReplay, switchMap, map, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { NewsResponse, NewsItem } from '../models';
import { SignalService } from './signal.service';

@Injectable({
  providedIn: 'root'
})
export class NewsService {
  private apiUrl = '/api';
  
  // News limit subject
  private newsLimitSubject = new BehaviorSubject<number>(10);
  
  // News for current symbol observable
  currentSymbolNews$: Observable<NewsResponse>;
  
  // Trending news observable
  trendingNews$: Observable<NewsResponse>;

  constructor(
    private http: HttpClient,
    private signalService: SignalService
  ) {
    // Initialize observables in constructor
    this.currentSymbolNews$ = combineLatest([
      this.signalService.currentSymbol$,
      this.newsLimitSubject.asObservable()
    ]).pipe(
      debounceTime(300),
      switchMap(([symbol, limit]) => this.fetchNews(symbol, limit)),
      shareReplay(1)
    );
    
    this.trendingNews$ = this.getTrendingNews().pipe(shareReplay(1));
  }

  /**
   * Set news limit
   */
  setNewsLimit(limit: number): void {
    this.newsLimitSubject.next(limit);
  }

  /**
   * Get news for a specific symbol
   */
  getNews(symbol: string, limit: number = 10): Observable<NewsResponse> {
    return this.fetchNews(symbol, limit);
  }
  
  /**
   * Fetch news from API
   */
  private fetchNews(symbol: string, limit: number): Observable<NewsResponse> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('limit', limit.toString());

    return this.http.get<NewsResponse>(`${this.apiUrl}/news`, { params })
      .pipe(
        retry(1),
        catchError(this.handleError),
        map(response => {
          // Sort news by date (newest first)
          response.news = response.news.sort((a, b) =>
            new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
          );
          return response;
        })
      );
  }

  /**
   * Get trending news across all symbols
   */
  getTrendingNews(limit: number = 5): Observable<NewsResponse> {
    const params = new HttpParams()
      .set('limit', limit.toString())
      .set('trending', 'true');

    return this.http.get<NewsResponse>(`${this.apiUrl}/news`, { params })
      .pipe(
        retry(1),
        catchError(this.handleError)
      );
  }
  
  /**
   * Get news by impact score (high to low)
   */
  getHighImpactNews(limit: number = 5): Observable<NewsItem[]> {
    return this.getTrendingNews(20).pipe(
      map(response => {
        // Sort by impact score and take top 'limit' items
        return response.news
          .sort((a, b) => b.impactScore - a.impactScore)
          .slice(0, limit);
      })
    );
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