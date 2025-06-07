import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AIInsight {
  symbol: string;
  sentiment: {
    overall_sentiment: number;
    sentiment_label: string;
    confidence: number;
    news_sentiment: number;
    reddit_sentiment: number;
    fear_greed_index: number;
    analysis_time: string;
  };
  prediction: {
    symbol: string;
    current_price: number;
    predicted_price: number;
    price_change_percent: number;
    confidence: number;
    timeframe: string;
    support_level: number;
    resistance_level: number;
    volatility: number;
    technical_indicators: {
      rsi: number;
      macd: number;
      bb_position: string;
      trend: string;
    };
    prediction_time: string;
  };
  anomalies: {
    symbol: string;
    volume_anomaly: boolean;
    volume_zscore: number;
    volume_ratio: number;
    price_anomaly: boolean;
    price_zscore: number;
    price_change: number;
    anomaly_score: number;
    detection_time: string;
  };
  recommendation: {
    action: string;
    confidence: number;
    score: number;
    reasoning: string;
  };
  risk_score: number;
  generated_at: string;
}

export interface MarketOverview {
  symbols: { [key: string]: AIInsight };
  market_summary: {
    overall_sentiment: number;
    market_mood: string;
    analyzed_symbols: number;
    timestamp: string;
  };
}

export interface ChatMessage {
  message: string;
  isUser: boolean;
  timestamp: Date;
  suggestions?: string[];
}

export interface SmartAlert {
  type: string;
  symbol: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  timestamp: string;
}

export interface PortfolioOptimization {
  current_portfolio: { [key: string]: number };
  optimized_portfolio: { [key: string]: number };
  risk_reduction: number;
  expected_return_improvement: number;
  recommendations: string[];
  risk_scores: { [key: string]: number };
  optimization_time: string;
}

@Injectable({
  providedIn: 'root'
})
export class AIService {
  private baseUrl = environment.apiUrl;
  private chatMessages = new BehaviorSubject<ChatMessage[]>([]);
  private smartAlerts = new BehaviorSubject<SmartAlert[]>([]);
  private marketOverview = new BehaviorSubject<MarketOverview | null>(null);

  public chatMessages$ = this.chatMessages.asObservable();
  public smartAlerts$ = this.smartAlerts.asObservable();
  public marketOverview$ = this.marketOverview.asObservable();

  constructor(private http: HttpClient) {
    this.initializeChat();
    this.startAlertMonitoring();
  }

  // Market Sentiment Analysis
  getMarketSentiment(symbol: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/ai/sentiment/${symbol}`);
  }

  // Price Predictions
  getPricePrediction(symbol: string, timeframe: string = '24h'): Observable<any> {
    return this.http.get(`${this.baseUrl}/ai/prediction/${symbol}?timeframe=${timeframe}`);
  }

  // Anomaly Detection
  detectAnomalies(symbol: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/ai/anomalies/${symbol}`);
  }

  // Comprehensive AI Insights
  getAIInsights(symbol: string): Observable<{ success: boolean; data: AIInsight }> {
    return this.http.get<{ success: boolean; data: AIInsight }>(`${this.baseUrl}/ai/insights/${symbol}`);
  }

  // Market Overview
  getMarketOverview(symbols: string[] = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']): Observable<{ success: boolean; data: MarketOverview }> {
    const symbolsParam = symbols.join(',');
    return this.http.get<{ success: boolean; data: MarketOverview }>(`${this.baseUrl}/ai/market-overview?symbols=${symbolsParam}`);
  }

  // Portfolio Optimization
  optimizePortfolio(currentBtc: number = 45, currentEth: number = 30, currentOthers: number = 25): Observable<{ success: boolean; data: PortfolioOptimization }> {
    return this.http.get<{ success: boolean; data: PortfolioOptimization }>(`${this.baseUrl}/ai/portfolio-optimize?current_btc=${currentBtc}&current_eth=${currentEth}&current_others=${currentOthers}`);
  }

  // Smart Alerts
  getSmartAlerts(symbols: string[] = ['BTCUSDT', 'ETHUSDT']): Observable<{ success: boolean; data: { alerts: SmartAlert[]; total_alerts: number; generated_at: string } }> {
    const symbolsParam = symbols.join(',');
    return this.http.get<{ success: boolean; data: { alerts: SmartAlert[]; total_alerts: number; generated_at: string } }>(`${this.baseUrl}/ai/alerts?symbols=${symbolsParam}`);
  }

  // AI Chat
  sendChatMessage(message: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/ai/chat`, { message });
  }

  // Chat Management
  addChatMessage(message: ChatMessage): void {
    const currentMessages = this.chatMessages.value;
    this.chatMessages.next([...currentMessages, message]);
  }

  getChatMessages(): ChatMessage[] {
    return this.chatMessages.value;
  }

  clearChatMessages(): void {
    this.chatMessages.next([]);
    this.initializeChat();
  }

  // Alert Management
  addAlert(alert: SmartAlert): void {
    const currentAlerts = this.smartAlerts.value;
    this.smartAlerts.next([alert, ...currentAlerts].slice(0, 10)); // Keep only last 10 alerts
  }

  dismissAlert(index: number): void {
    const currentAlerts = this.smartAlerts.value;
    currentAlerts.splice(index, 1);
    this.smartAlerts.next([...currentAlerts]);
  }

  clearAllAlerts(): void {
    this.smartAlerts.next([]);
  }

  // Market Overview Management
  updateMarketOverview(overview: MarketOverview): void {
    this.marketOverview.next(overview);
  }

  // Utility Methods
  getSentimentColor(sentiment: number): string {
    if (sentiment > 0.3) return 'text-green-600';
    if (sentiment < -0.3) return 'text-red-600';
    return 'text-gray-600';
  }

  getSentimentIcon(sentiment: number): string {
    if (sentiment > 0.3) return 'pi-arrow-up';
    if (sentiment < -0.3) return 'pi-arrow-down';
    return 'pi-minus';
  }

  getConfidenceColor(confidence: number): string {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  }

  getRiskColor(risk: number): string {
    if (risk <= 30) return 'text-green-600';
    if (risk <= 60) return 'text-yellow-600';
    return 'text-red-600';
  }

  getActionColor(action: string): string {
    switch (action) {
      case 'STRONG_BUY':
      case 'BUY':
        return 'text-green-600';
      case 'STRONG_SELL':
      case 'SELL':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  }

  getActionIcon(action: string): string {
    switch (action) {
      case 'STRONG_BUY':
        return 'pi-arrow-up';
      case 'BUY':
        return 'pi-arrow-up-right';
      case 'STRONG_SELL':
        return 'pi-arrow-down';
      case 'SELL':
        return 'pi-arrow-down-right';
      default:
        return 'pi-minus';
    }
  }

  private initializeChat(): void {
    const welcomeMessage: ChatMessage = {
      message: 'Hello! I\'m your AI trading assistant. I can help you with market analysis, price predictions, risk assessment, and trading recommendations. How can I assist you today?',
      isUser: false,
      timestamp: new Date(),
      suggestions: [
        'Analyze market sentiment',
        'Get price predictions',
        'Check for anomalies',
        'Risk assessment'
      ]
    };
    this.chatMessages.next([welcomeMessage]);
  }

  private startAlertMonitoring(): void {
    // Poll for alerts every 30 seconds
    setInterval(() => {
      this.getSmartAlerts().subscribe({
        next: (response) => {
          if (response.success && response.data.alerts.length > 0) {
            response.data.alerts.forEach(alert => {
              // Only add new alerts (check if not already exists)
              const existingAlerts = this.smartAlerts.value;
              const exists = existingAlerts.some(existing => 
                existing.symbol === alert.symbol && 
                existing.type === alert.type && 
                existing.timestamp === alert.timestamp
              );
              if (!exists) {
                this.addAlert(alert);
              }
            });
          }
        },
        error: (error) => {
          console.error('Error fetching smart alerts:', error);
        }
      });
    }, 30000);
  }
}