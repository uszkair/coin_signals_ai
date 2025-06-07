import { Injectable } from '@angular/core';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';
import { Signal } from './signal.service';

export interface WebSocketMessage {
  type: 'signal' | 'notification' | 'status';
  data: any;
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

}