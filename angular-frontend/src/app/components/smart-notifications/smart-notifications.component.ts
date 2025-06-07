import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { AIService, SmartAlert } from '../../services/ai.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-smart-notifications',
  standalone: true,
  imports: [CommonModule, ButtonModule, CardModule, TagModule, TooltipModule],
  templateUrl: './smart-notifications.component.html'
})
export class SmartNotificationsComponent implements OnInit, OnDestroy {
  alerts: SmartAlert[] = [];
  private subscription = new Subscription();

  constructor(private aiService: AIService) {}

  ngOnInit(): void {
    this.subscription.add(
      this.aiService.smartAlerts$.subscribe(alerts => {
        this.alerts = alerts;
      })
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  dismissAlert(index: number): void {
    this.aiService.dismissAlert(index);
  }

  clearAllAlerts(): void {
    this.aiService.clearAllAlerts();
  }

  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'high':
        return 'border-red-200 bg-red-50';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50';
      case 'low':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  }

  getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'high':
        return 'pi-exclamation-triangle text-red-600';
      case 'medium':
        return 'pi-info-circle text-yellow-600';
      case 'low':
        return 'pi-info text-blue-600';
      default:
        return 'pi-bell text-gray-600';
    }
  }

  getSeverityTextColor(severity: string): string {
    switch (severity) {
      case 'high':
        return 'text-red-800';
      case 'medium':
        return 'text-yellow-800';
      case 'low':
        return 'text-blue-800';
      default:
        return 'text-gray-800';
    }
  }

  getTypeIcon(type: string): string {
    switch (type) {
      case 'volume_anomaly':
        return 'pi-chart-bar';
      case 'price_anomaly':
        return 'pi-trending-up';
      case 'sentiment_extreme':
        return 'pi-heart';
      case 'trading_opportunity':
        return 'pi-star';
      default:
        return 'pi-bell';
    }
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  }

  getAlertTitle(type: string): string {
    switch (type) {
      case 'volume_anomaly':
        return 'Volume Anomaly';
      case 'price_anomaly':
        return 'Price Alert';
      case 'sentiment_extreme':
        return 'Sentiment Alert';
      case 'trading_opportunity':
        return 'Trading Opportunity';
      default:
        return 'Smart Alert';
    }
  }
}