import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TradingNotification } from '../../services/notification.service';

@Component({
  selector: 'app-notification-details-modal',
  standalone: true,
  imports: [
    CommonModule,
    DialogModule,
    ButtonModule,
    TagModule
  ],
  templateUrl: './notification-details-modal.component.html',
  styles: []
})
export class NotificationDetailsModalComponent {
  @Input() visible = false;
  @Input() notification: TradingNotification | null = null;
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() markAsReadEvent = new EventEmitter<TradingNotification>();
  @Output() deleteEvent = new EventEmitter<TradingNotification>();

  onClose(): void {
    this.visible = false;
    this.visibleChange.emit(false);
  }

  markAsRead(): void {
    if (this.notification) {
      this.markAsReadEvent.emit(this.notification);
    }
  }

  deleteNotification(): void {
    if (this.notification) {
      this.deleteEvent.emit(this.notification);
      this.onClose();
    }
  }

  getNotificationIcon(type: string): string {
    switch (type) {
      case 'new_position':
        return 'pi-plus-circle';
      case 'position_closed':
        return 'pi-check-circle';
      case 'trade_error':
        return 'pi-exclamation-triangle';
      case 'position_update':
        return 'pi-refresh';
      case 'volume_anomaly':
        return 'pi-chart-bar';
      case 'price_anomaly':
        return 'pi-trending-up';
      default:
        return 'pi-bell';
    }
  }

  getNotificationColor(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'danger';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'secondary';
      default:
        return 'info';
    }
  }

  getTypeLabel(type: string): string {
    switch (type) {
      case 'new_position':
        return 'Új pozíció';
      case 'position_closed':
        return 'Pozíció lezárva';
      case 'trade_error':
        return 'Kereskedési hiba';
      case 'position_update':
        return 'Pozíció frissítés';
      case 'volume_anomaly':
        return 'Volumen anomália';
      case 'price_anomaly':
        return 'Ár anomália';
      default:
        return type;
    }
  }

  getPriorityLabel(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'Kritikus';
      case 'high':
        return 'Magas';
      case 'medium':
        return 'Közepes';
      case 'low':
        return 'Alacsony';
      default:
        return priority;
    }
  }

  getHeaderClass(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800';
      case 'high':
        return 'bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800';
      case 'medium':
        return 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800';
      case 'low':
        return 'bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800';
      default:
        return 'bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800';
    }
  }

  getIconBackgroundClass(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 dark:bg-red-800/30';
      case 'high':
        return 'bg-orange-100 dark:bg-orange-800/30';
      case 'medium':
        return 'bg-blue-100 dark:bg-blue-800/30';
      case 'low':
        return 'bg-gray-100 dark:bg-gray-800/30';
      default:
        return 'bg-gray-100 dark:bg-gray-800/30';
    }
  }

  getIconColorClass(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      case 'high':
        return 'text-orange-600 dark:text-orange-400';
      case 'medium':
        return 'text-blue-600 dark:text-blue-400';
      case 'low':
        return 'text-gray-600 dark:text-gray-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  }

  getTitleColorClass(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'text-red-800 dark:text-red-200';
      case 'high':
        return 'text-orange-800 dark:text-orange-200';
      case 'medium':
        return 'text-blue-800 dark:text-blue-200';
      case 'low':
        return 'text-gray-800 dark:text-gray-200';
      default:
        return 'text-gray-800 dark:text-gray-200';
    }
  }

  formatCurrency(value: number): string {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  }

  formatTimeAgo(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Most';
    if (diffMins < 60) return `${diffMins} perce`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} órája`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} napja`;
  }

  hasDataToShow(data: any): boolean {
    if (!data) return false;
    
    const relevantKeys = ['symbol', 'price', 'quantity', 'pnl', 'volume_multiplier'];
    return relevantKeys.some(key => data[key] !== undefined && data[key] !== null);
  }

  hasAdditionalData(data: any): boolean {
    if (!data) return false;
    
    const displayedKeys = ['symbol', 'price', 'quantity', 'pnl', 'volume_multiplier'];
    const additionalKeys = Object.keys(data).filter(key => !displayedKeys.includes(key));
    
    return additionalKeys.length > 0;
  }

  formatAdditionalData(data: any): string {
    if (!data) return '';
    
    const displayedKeys = ['symbol', 'price', 'quantity', 'pnl', 'volume_multiplier'];
    const additionalData: any = {};
    
    Object.keys(data).forEach(key => {
      if (!displayedKeys.includes(key)) {
        additionalData[key] = data[key];
      }
    });
    
    return JSON.stringify(additionalData, null, 2);
  }

  hasSymbolsInMessage(): boolean {
    if (!this.notification?.message) return false;
    // Check if message contains symbols like BTCUSDT, ETHUSDT
    const symbolPattern = /[A-Z]{3,}USDT/g;
    return symbolPattern.test(this.notification.message);
  }

  formatSymbols(symbols: string): string {
    if (!symbols) return '';
    // If symbols are comma-separated, split and format them
    if (symbols.includes(',')) {
      return symbols.split(',').map(s => s.trim()).join(', ');
    }
    return symbols;
  }

  extractSymbolsFromMessage(): string {
    if (!this.notification?.message) return '';
    // Extract symbols like BTCUSDT, ETHUSDT from message
    const symbolPattern = /[A-Z]{3,}USDT/g;
    const matches = this.notification.message.match(symbolPattern);
    if (matches) {
      return matches.join(', ');
    }
    return '';
  }

  hasVolumeMultiplierInMessage(): boolean {
    if (!this.notification?.message) return false;
    // Check if message contains volume multiplier like "5.4x normal" or "2.5x normal"
    const volumePattern = /\d+\.?\d*x\s+normal/i;
    return volumePattern.test(this.notification.message);
  }

  extractVolumeMultiplierFromMessage(): string {
    if (!this.notification?.message) return '';
    // Extract volume multiplier like "5.4x normal" from message
    const volumePattern = /(\d+\.?\d*)x\s+normal/i;
    const match = this.notification.message.match(volumePattern);
    if (match) {
      return `${match[1]}x normál`;
    }
    return '';
  }
}