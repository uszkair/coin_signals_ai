import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ProgressBarModule } from 'primeng/progressbar';
import { TooltipModule } from 'primeng/tooltip';
import { SkeletonModule } from 'primeng/skeleton';
import { AIService, MarketOverview } from '../../services/ai.service';
import { Subscription, interval } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-ai-insights-panel',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    CardModule,
    TagModule,
    ProgressBarModule,
    TooltipModule,
    SkeletonModule
  ],
  templateUrl: './ai-insights-panel.component.html'
})
export class AiInsightsPanelComponent implements OnInit, OnDestroy {
  marketOverview: MarketOverview | null = null;
  isLoading = true;
  error: string | null = null;
  
  private subscription = new Subscription();

  constructor(private aiService: AIService) {}

  ngOnInit(): void {
    this.loadMarketOverview();
    
    // Auto-refresh every 30 seconds
    this.subscription.add(
      interval(30000).pipe(
        switchMap(() => this.aiService.getMarketOverview())
      ).subscribe({
        next: (response) => {
          if (response.success) {
            this.marketOverview = response.data;
            this.aiService.updateMarketOverview(response.data);
            this.error = null;
          }
        },
        error: (error) => {
          console.error('Error refreshing market overview:', error);
          this.error = 'Failed to refresh data';
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  loadMarketOverview(): void {
    this.isLoading = true;
    this.error = null;
    
    this.aiService.getMarketOverview().subscribe({
      next: (response) => {
        this.isLoading = false;
        if (response.success) {
          this.marketOverview = response.data;
          this.aiService.updateMarketOverview(response.data);
        } else {
          this.error = 'Failed to load market overview';
        }
      },
      error: (error) => {
        this.isLoading = false;
        this.error = 'Failed to load market overview';
        console.error('Market overview error:', error);
      }
    });
  }

  getSentimentColor(sentiment: number): string {
    return this.aiService.getSentimentColor(sentiment);
  }

  getSentimentIcon(sentiment: number): string {
    return this.aiService.getSentimentIcon(sentiment);
  }

  getConfidenceColor(confidence: number): string {
    return this.aiService.getConfidenceColor(confidence);
  }

  getRiskColor(risk: number): string {
    return this.aiService.getRiskColor(risk);
  }

  getActionColor(action: string): string {
    return this.aiService.getActionColor(action);
  }

  getActionIcon(action: string): string {
    return this.aiService.getActionIcon(action);
  }

  formatPercentage(value: number): string {
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  }

  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  }

  getSymbolDisplayName(symbol: string): string {
    return symbol.replace('USDT', '');
  }

  refresh(): void {
    this.loadMarketOverview();
  }

  getSymbolKeys(): string[] {
    return this.marketOverview ? Object.keys(this.marketOverview.symbols) : [];
  }

  hasHighRiskSymbol(): boolean {
    if (!this.marketOverview) return false;
    return Object.values(this.marketOverview.symbols).some(symbol => symbol.risk_score > 70);
  }

  getHighRiskSymbol(): string {
    if (!this.marketOverview) return '';
    const highRiskSymbol = Object.entries(this.marketOverview.symbols)
      .find(([_, symbol]) => symbol.risk_score > 70);
    return highRiskSymbol ? this.getSymbolDisplayName(highRiskSymbol[0]) : '';
  }

  hasStrongSignal(): boolean {
    if (!this.marketOverview) return false;
    return Object.values(this.marketOverview.symbols).some(symbol =>
      symbol.recommendation?.confidence > 85
    );
  }

  getStrongSignalAction(): string {
    if (!this.marketOverview) return '';
    const strongSignal = Object.values(this.marketOverview.symbols)
      .find(symbol => symbol.recommendation?.confidence > 85);
    return strongSignal?.recommendation?.action.replace('_', ' ').toLowerCase() || '';
  }

  getStrongSignalSymbol(): string {
    if (!this.marketOverview) return '';
    const strongSignal = Object.entries(this.marketOverview.symbols)
      .find(([_, symbol]) => symbol.recommendation?.confidence > 85);
    return strongSignal ? this.getSymbolDisplayName(strongSignal[0]) : '';
  }

  hasVolumeAnomaly(): boolean {
    if (!this.marketOverview) return false;
    return Object.values(this.marketOverview.symbols).some(symbol =>
      symbol.anomalies?.volume_anomaly
    );
  }

  getVolumeAnomalySymbol(): string {
    if (!this.marketOverview) return '';
    const anomalySymbol = Object.entries(this.marketOverview.symbols)
      .find(([_, symbol]) => symbol.anomalies?.volume_anomaly);
    return anomalySymbol ? this.getSymbolDisplayName(anomalySymbol[0]) : '';
  }

  getTopRecommendations(): Array<{symbol: string, action: string, confidence: number, reasoning: string}> {
    if (!this.marketOverview) return [];
    
    return Object.entries(this.marketOverview.symbols)
      .map(([symbol, data]) => ({
        symbol: this.getSymbolDisplayName(symbol),
        action: data.recommendation?.action || 'HOLD',
        confidence: data.recommendation?.confidence || 0,
        reasoning: data.recommendation?.reasoning || 'No specific reasoning available'
      }))
      .filter(rec => rec.confidence > 70)
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 3);
  }

  formatLastUpdated(): string {
    if (!this.marketOverview?.market_summary?.timestamp) {
      return 'Unknown';
    }
    
    const date = new Date(this.marketOverview.market_summary.timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  getConfidenceTagSeverity(confidence: number): string {
    if (confidence >= 80) return 'success';
    if (confidence >= 60) return 'info';
    return 'danger';
  }

  // Make Math available in template
  Math = Math;
}