import { Component, OnInit, Input, ElementRef, OnChanges, SimpleChanges } from '@angular/core';

declare const TradingView: any;

@Component({
  selector: 'app-trading-view-widget',
  standalone: true,
  template: '<div id="tradingview-widget-container" style="height: 100%;"></div>',
  styles: [':host { display: block; height: 100%; width: 100%; }']
})
export class TradingViewWidgetComponent implements OnInit, OnChanges {
  @Input() symbol: string = 'BTCUSDT';
  @Input() interval: string = '1h';
  @Input() theme: 'light' | 'dark' = 'light';
  
  private container: HTMLElement | null = null;
  private widget: any = null;

  constructor(private el: ElementRef) {}

  ngOnInit(): void {
    this.initWidget();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['symbol'] && !changes['symbol'].firstChange) || 
        (changes['interval'] && !changes['interval'].firstChange) ||
        (changes['theme'] && !changes['theme'].firstChange)) {
      this.initWidget();
    }
  }

  private initWidget(): void {
    // Make sure TradingView is loaded
    if (typeof TradingView === 'undefined') {
      this.loadTradingViewScript().then(() => {
        this.createWidget();
      });
    } else {
      this.createWidget();
    }
  }

  private createWidget(): void {
    this.container = document.getElementById('tradingview-widget-container');
    
    if (this.container) {
      // Clear previous widget if exists
      if (this.widget) {
        this.container.innerHTML = '';
      }
      
      // Map interval to TradingView format
      const tvInterval = this.mapInterval(this.interval);
      
      // Create new widget
      this.widget = new TradingView.widget({
        container_id: 'tradingview-widget-container',
        symbol: `BINANCE:${this.symbol}`,
        interval: tvInterval,
        theme: this.theme,
        style: '1',
        locale: 'en',
        toolbar_bg: '#f1f3f6',
        enable_publishing: false,
        hide_top_toolbar: false,
        hide_legend: false,
        save_image: false,
        height: '100%',
        width: '100%',
        studies: [
          'RSI@tv-basicstudies',
          'MASimple@tv-basicstudies',
          'MACD@tv-basicstudies'
        ],
        show_popup_button: true,
        popup_width: '1000',
        popup_height: '650',
        autosize: true
      });
    }
  }

  private loadTradingViewScript(): Promise<void> {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.type = 'text/javascript';
      script.src = 'https://s3.tradingview.com/tv.js';
      script.onload = () => resolve();
      document.head.appendChild(script);
    });
  }

  private mapInterval(interval: string): string {
    // Map our interval format to TradingView format
    switch (interval) {
      case '1m': return '1';
      case '5m': return '5';
      case '15m': return '15';
      case '1h': return '60';
      case '4h': return '240';
      case '1d': return 'D';
      default: return '60'; // Default to 1h
    }
  }
}