import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { TableModule } from 'primeng/table';
import { BadgeModule } from 'primeng/badge';
import { DropdownModule } from 'primeng/dropdown';
import { InputTextModule } from 'primeng/inputtext';
import { CalendarModule } from 'primeng/calendar';
import { NotificationService, TradingNotification, NotificationStats } from '../../services/notification.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    CardModule,
    TagModule,
    TooltipModule,
    TableModule,
    BadgeModule,
    DropdownModule,
    InputTextModule,
    CalendarModule
  ],
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.scss']
})
export class NotificationsComponent implements OnInit, OnDestroy {
  notifications: TradingNotification[] = [];
  stats: NotificationStats | null = null;
  unreadCount = 0;
  loading = false;
  
  // Filters
  selectedType: any = null;
  selectedPriority: any = null;
  showUnreadOnly = false;
  
  typeOptions = [
    { label: 'Összes típus', value: null },
    { label: 'Új pozíció', value: 'new_position' },
    { label: 'Pozíció lezárva', value: 'position_closed' },
    { label: 'Kereskedési hiba', value: 'trade_error' },
    { label: 'Pozíció frissítés', value: 'position_update' }
  ];
  
  priorityOptions = [
    { label: 'Összes prioritás', value: null },
    { label: 'Kritikus', value: 'critical' },
    { label: 'Magas', value: 'high' },
    { label: 'Közepes', value: 'medium' },
    { label: 'Alacsony', value: 'low' }
  ];

  private subscription = new Subscription();

  constructor(private notificationService: NotificationService) {}

  ngOnInit(): void {
    this.loadData();
    
    // Subscribe to real-time notifications
    this.subscription.add(
      this.notificationService.notifications$.subscribe(notifications => {
        this.notifications = notifications;
        this.applyFilters();
      })
    );
    
    this.subscription.add(
      this.notificationService.unreadCount$.subscribe(count => {
        this.unreadCount = count;
      })
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  loadData(): void {
    this.loading = true;
    
    // Load notifications
    this.notificationService.loadNotifications();
    
    // Load stats
    this.notificationService.getNotificationStats().subscribe({
      next: (response) => {
        if (response.success) {
          this.stats = response.data;
        }
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading notification stats:', error);
        this.loading = false;
      }
    });
  }

  applyFilters(): void {
    let filtered = [...this.notifications];
    
    if (this.selectedType?.value) {
      filtered = filtered.filter(n => n.notification_type === this.selectedType.value);
    }
    
    if (this.selectedPriority?.value) {
      filtered = filtered.filter(n => n.priority === this.selectedPriority.value);
    }
    
    if (this.showUnreadOnly) {
      filtered = filtered.filter(n => !n.is_read);
    }
    
    this.notifications = filtered;
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  toggleUnreadFilter(): void {
    this.showUnreadOnly = !this.showUnreadOnly;
    this.applyFilters();
  }

  markAsRead(notification: TradingNotification): void {
    if (!notification.is_read) {
      this.notificationService.markNotificationAsRead(notification.id);
    }
  }

  markAllAsRead(): void {
    this.notificationService.markAllNotificationsAsRead();
  }

  cleanupOldNotifications(): void {
    this.notificationService.cleanupOldNotifications().subscribe({
      next: (response) => {
        if (response.success) {
          console.log(`${response.data.deleted_count} régi értesítés törölve`);
          this.loadData(); // Reload data
        }
      },
      error: (error) => {
        console.error('Error cleaning up notifications:', error);
      }
    });
  }

  getNotificationIcon(type: string): string {
    return this.notificationService.getNotificationIcon(type);
  }

  getNotificationColor(priority: string): string {
    return this.notificationService.getNotificationColor(priority);
  }

  formatTimeAgo(timestamp: string): string {
    return this.notificationService.formatTimeAgo(timestamp);
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

  formatCurrency(value: number): string {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  }

  getRowClass(notification: TradingNotification): string {
    if (!notification.is_read) {
      return 'bg-blue-50 dark:bg-blue-900/20 font-medium';
    }
    return '';
  }
}