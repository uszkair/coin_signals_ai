import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private apiUrl = `${environment.apiUrl}/settings`;
  private settingsSubject = new BehaviorSubject<any | null>(null);
  public settings$ = this.settingsSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadSettings();
  }

  // Load all settings
  loadSettings(): Observable<any> {
    const request = this.http.get<any>(`${this.apiUrl}`);
    request.subscribe(settings => {
      this.settingsSubject.next(settings);
    });
    return request;
  }

  // Update all settings
  updateSettings(settings: any): Observable<any> {
    const request = this.http.put(`${this.apiUrl}`, settings);
    request.subscribe(() => {
      this.loadSettings(); // Reload settings after update
    });
    return request;
  }

  // Get specific category settings
  getCategorySettings(category: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/category/${category}`);
  }

  // Update specific category settings
  updateCategorySettings(category: string, settings: any): Observable<any> {
    const request = this.http.put(`${this.apiUrl}/category/${category}`, settings);
    request.subscribe(() => {
      this.loadSettings(); // Reload settings after update
    });
    return request;
  }

  // Reset settings to defaults
  resetToDefaults(): Observable<any> {
    const request = this.http.post(`${this.apiUrl}/reset`, {});
    request.subscribe(() => {
      this.loadSettings(); // Reload settings after reset
    });
    return request;
  }

  // Get default settings
  getDefaults(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/defaults`);
  }

  // Convenience methods for specific categories
  getSignalGenerationSettings(): Observable<any> {
    return this.getCategorySettings('signal_generation');
  }

  updateSignalGenerationSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('signal_generation', settings);
  }

  getTechnicalAnalysisSettings(): Observable<any> {
    return this.getCategorySettings('technical_analysis');
  }

  updateTechnicalAnalysisSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('technical_analysis', settings);
  }

  getAIMLSettings(): Observable<any> {
    return this.getCategorySettings('ai_ml');
  }

  updateAIMLSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('ai_ml', settings);
  }

  getAutoTradingSettings(): Observable<any> {
    return this.getCategorySettings('auto_trading');
  }

  updateAutoTradingSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('auto_trading', settings);
  }

  getRiskManagementSettings(): Observable<any> {
    return this.getCategorySettings('risk_management');
  }

  updateRiskManagementSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('risk_management', settings);
  }

  getNotificationSettings(): Observable<any> {
    return this.getCategorySettings('notifications');
  }

  updateNotificationSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('notifications', settings);
  }

  getBacktestingSettings(): Observable<any> {
    return this.getCategorySettings('backtesting');
  }

  updateBacktestingSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('backtesting', settings);
  }

  getDataHistorySettings(): Observable<any> {
    return this.getCategorySettings('data_history');
  }

  updateDataHistorySettings(settings: any): Observable<any> {
    return this.updateCategorySettings('data_history', settings);
  }

  getAdvancedSettings(): Observable<any> {
    return this.getCategorySettings('advanced');
  }

  updateAdvancedSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('advanced', settings);
  }

  getUIUXSettings(): Observable<any> {
    return this.getCategorySettings('ui_ux');
  }

  updateUIUXSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('ui_ux', settings);
  }

  getTradingEnvironmentSettings(): Observable<any> {
    return this.getCategorySettings('trading_environment');
  }

  updateTradingEnvironmentSettings(settings: any): Observable<any> {
    return this.updateCategorySettings('trading_environment', settings);
  }

  // Stop Loss/Take Profit Settings
  getStopLossTakeProfitSettings(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stop-loss-take-profit`);
  }

  updateStopLossTakeProfitSettings(settings: any): Observable<any> {
    const request = this.http.put(`${this.apiUrl}/stop-loss-take-profit`, settings);
    request.subscribe(() => {
      this.loadSettings(); // Reload settings after update
    });
    return request;
  }

  // Get current settings from cache
  getCurrentSettings(): any {
    return this.settingsSubject.value;
  }
}