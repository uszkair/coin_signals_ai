import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AISignal {
  symbol: string;
  interval: string;
  ai_signal: string;
  ai_confidence: number;
  probabilities: {
    buy: number;
    sell: number;
    hold: number;
  };
  model_predictions: any;
  feature_importance: any;
  market_regime: string;
  risk_score: number;
  timestamp: string;
  ml_available: boolean;
}

export interface ModelStatus {
  ml_available: boolean;
  models_trained: boolean;
  available_models: string[];
  model_path: string;
  training_features: string[];
  supported_intervals: string[];
  market_regimes: string[];
}

export interface RiskAssessment {
  symbol: string;
  risk_score: number;
  risk_level: string;
  confidence: number;
  market_regime: string;
  recommendation: string;
  position_sizing: {
    recommended_percentage: number;
    risk_multiplier: number;
    max_recommended: string;
    reasoning: string;
  };
  risk_factors: any;
  analysis_timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class AiMlService {
  private baseUrl = 'http://localhost:8000/api/ai';

  constructor(private http: HttpClient) {}

  // AI Signal Generation
  getAISignal(symbol: string, interval: string = '1h'): Observable<{ success: boolean; data: AISignal }> {
    return this.http.get<{ success: boolean; data: AISignal }>(`${this.baseUrl}/signal/${symbol}?interval=${interval}`);
  }

  getAISignalPost(symbol: string, interval: string = '1h'): Observable<{ success: boolean; data: AISignal }> {
    return this.http.post<{ success: boolean; data: AISignal }>(`${this.baseUrl}/signal`, {
      symbol,
      interval
    });
  }

  getBatchAISignals(symbols: string[], interval: string = '1h'): Observable<{ success: boolean; data: any }> {
    const symbolsParam = symbols.join(',');
    return this.http.get<{ success: boolean; data: any }>(`${this.baseUrl}/signals/batch?symbols=${symbolsParam}&interval=${interval}`);
  }

  // Model Management
  getModelStatus(): Observable<{ success: boolean; data: ModelStatus }> {
    return this.http.get<{ success: boolean; data: ModelStatus }>(`${this.baseUrl}/model/status`);
  }

  trainModels(symbols?: string[], days: number = 90, background: boolean = true): Observable<{ success: boolean; data: any }> {
    return this.http.post<{ success: boolean; data: any }>(`${this.baseUrl}/model/train`, {
      symbols,
      days,
      background
    });
  }

  getModelPerformance(): Observable<{ success: boolean; data: any }> {
    return this.http.get<{ success: boolean; data: any }>(`${this.baseUrl}/models/performance`);
  }

  // Analysis Functions
  getMarketRegime(symbol: string, interval: string = '1h'): Observable<{ success: boolean; data: any }> {
    return this.http.get<{ success: boolean; data: any }>(`${this.baseUrl}/analysis/market-regime/${symbol}?interval=${interval}`);
  }

  getFeatureImportance(symbol: string, interval: string = '1h'): Observable<{ success: boolean; data: any }> {
    return this.http.get<{ success: boolean; data: any }>(`${this.baseUrl}/analysis/feature-importance/${symbol}?interval=${interval}`);
  }

  getRiskAssessment(symbol: string, interval: string = '1h'): Observable<{ success: boolean; data: RiskAssessment }> {
    return this.http.get<{ success: boolean; data: RiskAssessment }>(`${this.baseUrl}/analysis/risk-assessment/${symbol}?interval=${interval}`);
  }

  // Utility Methods
  interpretAISignal(aiSignal: AISignal): string {
    const confidence = aiSignal.ai_confidence;
    const signal = aiSignal.ai_signal;
    
    if (confidence > 80) {
      return `Erős AI ${signal} jel (${confidence.toFixed(1)}% bizalom)`;
    } else if (confidence > 60) {
      return `Közepes AI ${signal} jel (${confidence.toFixed(1)}% bizalom)`;
    } else {
      return `Gyenge AI ${signal} jel (${confidence.toFixed(1)}% bizalom)`;
    }
  }

  getRiskLevelColor(riskScore: number): string {
    if (riskScore > 80) return 'text-red-600';
    if (riskScore > 60) return 'text-orange-600';
    if (riskScore > 40) return 'text-yellow-600';
    if (riskScore > 20) return 'text-green-600';
    return 'text-blue-600';
  }

  getMarketRegimeIcon(regime: string): string {
    switch (regime) {
      case 'TRENDING': return 'pi pi-arrow-up-right';
      case 'RANGING': return 'pi pi-arrows-h';
      case 'VOLATILE': return 'pi pi-exclamation-triangle';
      default: return 'pi pi-question-circle';
    }
  }

  getConfidenceColor(confidence: number): string {
    if (confidence > 80) return 'text-green-600';
    if (confidence > 60) return 'text-blue-600';
    if (confidence > 40) return 'text-yellow-600';
    return 'text-red-600';
  }

  formatProbabilities(probabilities: { buy: number; sell: number; hold: number }): string {
    return `BUY: ${(probabilities.buy * 100).toFixed(1)}%, SELL: ${(probabilities.sell * 100).toFixed(1)}%, HOLD: ${(probabilities.hold * 100).toFixed(1)}%`;
  }

  getTopFeatures(featureImportance: any, count: number = 3): Array<{ name: string; importance: number }> {
    if (!featureImportance) return [];
    
    return Object.entries(featureImportance)
      .map(([name, importance]) => ({ name, importance: importance as number }))
      .sort((a, b) => b.importance - a.importance)
      .slice(0, count);
  }
}