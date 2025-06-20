import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';
import { WebSocketService } from './websocket.service';

export interface TradingNotification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  data?: any;
  is_read: boolean;
  is_sent: boolean;
  sent_at?: string;
  read_at?: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationStats {
  total_notifications: number;
  unread_notifications: number;
  read_notifications: number;
  by_type: { [key: string]: number };
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private apiUrl = `${environment.apiUrl}/notifications`;
  private notificationsSubject = new BehaviorSubject<TradingNotification[]>([]);
  private unreadCountSubject = new BehaviorSubject<number>(0);

  public notifications$ = this.notificationsSubject.asObservable();
  public unreadCount$ = this.unreadCountSubject.asObservable();

  constructor(
    private http: HttpClient,
    private websocketService: WebSocketService
  ) {
    this.initializeWebSocketListeners();
    this.loadNotifications();
  }

  private initializeWebSocketListeners(): void {
    // Listen for new trading notifications via WebSocket
    this.websocketService.onNotification().subscribe((notification) => {
      if (notification.type === 'new_position' ||
          notification.type === 'position_closed' ||
          notification.type === 'trade_error' ||
          notification.type === 'volume_anomaly' ||
          notification.type === 'price_anomaly') {
        
        // Add new notification to the list
        const tradingNotification: TradingNotification = {
          id: Date.now(), // Temporary ID until we get real one from API
          notification_type: notification.type,
          title: notification.title,
          message: notification.message,
          priority: notification.priority || 'medium',
          data: notification.data,
          is_read: false,
          is_sent: true,
          sent_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };

        const currentNotifications = this.notificationsSubject.value;
        this.notificationsSubject.next([tradingNotification, ...currentNotifications]);
        this.updateUnreadCount();
      }
    });
  }

  // API Methods
  getNotifications(limit: number = 50, unreadOnly: boolean = false): Observable<any> {
    const params = new URLSearchParams();
    params.set('limit', limit.toString());
    if (unreadOnly) {
      params.set('unread_only', 'true');
    }
    
    return this.http.get(`${this.apiUrl}/?${params.toString()}`);
  }

  getUnreadCount(): Observable<any> {
    return this.http.get(`${this.apiUrl}/unread-count`);
  }

  markAsRead(notificationId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/mark-read`, {
      notification_id: notificationId
    });
  }

  markAllAsRead(): Observable<any> {
    return this.http.post(`${this.apiUrl}/mark-all-read`, {});
  }

  getRecentNotifications(hours: number = 24): Observable<any> {
    return this.http.get(`${this.apiUrl}/recent?hours=${hours}`);
  }

  getNotificationStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stats`);
  }

  deleteNotification(notificationId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/delete`, {
      body: { notification_id: notificationId }
    });
  }

  deleteAllReadNotifications(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/delete-all-read`);
  }

  cleanupOldNotifications(daysOld: number = 7): Observable<any> {
    return this.http.delete(`${this.apiUrl}/cleanup?days_old=${daysOld}`);
  }

  // Local state management
  loadNotifications(): void {
    this.getNotifications().subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.notificationsSubject.next(response.data);
          this.updateUnreadCount();
        }
      },
      error: (error) => {
        console.error('Error loading notifications:', error);
      }
    });
  }

  private updateUnreadCount(): void {
    const unreadCount = this.notificationsSubject.value.filter(n => !n.is_read).length;
    this.unreadCountSubject.next(unreadCount);
  }

  markNotificationAsRead(notificationId: number): void {
    this.markAsRead(notificationId).subscribe({
      next: (response) => {
        if (response.success) {
          // Update local state
          const notifications = this.notificationsSubject.value.map(n => 
            n.id === notificationId ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
          );
          this.notificationsSubject.next(notifications);
          this.updateUnreadCount();
        }
      },
      error: (error) => {
        console.error('Error marking notification as read:', error);
      }
    });
  }

  markAllNotificationsAsRead(): void {
    this.markAllAsRead().subscribe({
      next: (response) => {
        if (response.success) {
          // Update local state
          const notifications = this.notificationsSubject.value.map(n => 
            ({ ...n, is_read: true, read_at: new Date().toISOString() })
          );
          this.notificationsSubject.next(notifications);
          this.updateUnreadCount();
        }
      },
      error: (error) => {
        console.error('Error marking all notifications as read:', error);
      }
    });
  }

  deleteNotificationById(notificationId: number): void {
    this.deleteNotification(notificationId).subscribe({
      next: (response) => {
        if (response.success) {
          // Remove from local state
          const notifications = this.notificationsSubject.value.filter(n => n.id !== notificationId);
          this.notificationsSubject.next(notifications);
          this.updateUnreadCount();
        }
      },
      error: (error) => {
        console.error('Error deleting notification:', error);
      }
    });
  }

  deleteAllReadNotificationsLocal(): void {
    this.deleteAllReadNotifications().subscribe({
      next: (response) => {
        if (response.success) {
          // Remove all read notifications from local state
          const notifications = this.notificationsSubject.value.filter(n => !n.is_read);
          this.notificationsSubject.next(notifications);
          this.updateUnreadCount();
          console.log(`${response.data.deleted_count} olvasott értesítés törölve`);
        }
      },
      error: (error) => {
        console.error('Error deleting all read notifications:', error);
      }
    });
  }

  // Utility methods
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
}