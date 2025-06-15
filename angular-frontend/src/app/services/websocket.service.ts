import { Injectable } from '@angular/core';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';
import { Signal } from './signal.service';

export interface WebSocketMessage {
  type: 'signal' | 'notification' | 'status' | 'position_update' | 'position_status' | 'connection' | 'error' | 'pong';
  data: any;
}

export interface PositionUpdate {
  symbol: string;
  position_side: string;
  position_amt: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  pnl_percentage: number;
  stop_loss_price?: number;
  take_profit_price?: number;
  position_type: string;
  leverage?: number;
  margin_type?: string;
  update_time: number;
}

export interface PositionUpdateData {
  pnl_updates: PositionUpdate[];
  count: number;
  timestamp: number;
}

export interface PositionStatusData {
  action: 'opened' | 'closed';
  symbol: string;
  position_id?: string;
  reason?: string;
  pnl?: number;
  pnl_percentage?: number;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: WebSocket | null = null;
  private messageSubject = new Subject<WebSocketMessage>();
  private connectionStatusSubject = new BehaviorSubject<'connected' | 'disconnected' | 'connecting'>('disconnected');
  
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000; // 5 seconds

  constructor() {
    this.connect();
  }

  // Public observables
  get messages$(): Observable<WebSocketMessage> {
    return this.messageSubject.asObservable();
  }

  get connectionStatus$(): Observable<'connected' | 'disconnected' | 'connecting'> {
    return this.connectionStatusSubject.asObservable();
  }

  // Connection management
  private connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.connectionStatusSubject.next('connecting');
    
    try {
      // Convert HTTP URL to WebSocket URL
      const wsUrl = environment.apiUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.connectionStatusSubject.next('connected');
        this.reconnectAttempts = 0;
      };

      this.socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.messageSubject.next(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.connectionStatusSubject.next('disconnected');
        this.scheduleReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.connectionStatusSubject.next('disconnected');
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      this.connectionStatusSubject.next('disconnected');
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${this.reconnectInterval}ms`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.log('Max reconnection attempts reached');
    }
  }


  // Subscribe to specific message types
  onSignalUpdate(): Observable<Signal> {
    return new Observable(observer => {
      const subscription = this.messages$.subscribe(message => {
        if (message.type === 'signal') {
          observer.next(message.data as Signal);
        }
      });
      
      return () => subscription.unsubscribe();
    });
  }

  onNotification(): Observable<any> {
    return new Observable(observer => {
      const subscription = this.messages$.subscribe(message => {
        if (message.type === 'notification') {
          observer.next(message.data);
        }
      });
      
      return () => subscription.unsubscribe();
    });
  }

  // Subscribe to position updates
  onPositionUpdate(): Observable<PositionUpdateData> {
    return new Observable(observer => {
      const subscription = this.messages$.subscribe(message => {
        if (message.type === 'position_update') {
          observer.next(message.data as PositionUpdateData);
        }
      });
      
      return () => subscription.unsubscribe();
    });
  }

  // Subscribe to position status changes (opened/closed)
  onPositionStatus(): Observable<PositionStatusData> {
    return new Observable(observer => {
      const subscription = this.messages$.subscribe(message => {
        if (message.type === 'position_status') {
          observer.next(message.data as PositionStatusData);
        }
      });
      
      return () => subscription.unsubscribe();
    });
  }

  // Send message to server
  sendMessage(message: any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message);
    }
  }

  // Subscribe to specific symbol updates
  subscribeToSymbol(symbol: string): void {
    this.sendMessage({
      type: 'subscribe',
      symbol: symbol
    });
  }

  // Unsubscribe from specific symbol updates
  unsubscribeFromSymbol(symbol: string): void {
    this.sendMessage({
      type: 'unsubscribe',
      symbol: symbol
    });
  }

  // Send ping to keep connection alive
  ping(): void {
    this.sendMessage({
      type: 'ping'
    });
  }

  // Get connection status
  getStatus(): void {
    this.sendMessage({
      type: 'get_status'
    });
  }

  // Manually disconnect
  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  // Manually reconnect
  reconnect(): void {
    this.disconnect();
    this.connect();
  }

}