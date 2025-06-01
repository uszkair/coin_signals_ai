import { Component, Input, OnInit, OnDestroy, OnChanges, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-trading-view-widget',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './trading-view-widget.component.html',
  styleUrls: []
})
export class TradingViewWidgetComponent implements OnInit, OnDestroy, OnChanges {
  @Input() symbol: string = 'BTCUSDT';
  @Input() interval: string = '1h';
  @Input() theme: 'light' | 'dark' = 'light';
  
  @ViewChild('tradingViewContainer', { static: true })
  tradingViewContainer!: ElementRef;

  private widget: any;

  ngOnInit(): void {
    this.loadTradingViewWidget();
  }

  ngOnDestroy(): void {
    if (this.widget) {
      this.widget.remove();
    }
  }

  private loadTradingViewWidget(): void {
    // Load TradingView script if not already loaded
    if (!(window as any).TradingView) {
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = () => {
        this.initializeWidget();
      };
      document.head.appendChild(script);
    } else {
      this.initializeWidget();
    }
  }

  private initializeWidget(): void {
    if (this.tradingViewContainer && (window as any).TradingView) {
      // Convert symbol format (BTCUSDT -> BINANCE:BTCUSDT)
      const formattedSymbol = `BINANCE:${this.symbol}`;
      
      this.widget = new (window as any).TradingView.widget({
        autosize: true,
        symbol: formattedSymbol,
        interval: this.interval.toUpperCase(),
        timezone: "Europe/Budapest",
        theme: this.theme,
        style: "1",
        locale: "hu_HU",
        toolbar_bg: "#f1f3f6",
        enable_publishing: false,
        allow_symbol_change: false,
        container_id: this.tradingViewContainer.nativeElement.id,
        studies: [
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies"
        ],
        show_popup_button: true,
        popup_width: "1000",
        popup_height: "650"
      });
    }
  }

  // Update widget when inputs change
  ngOnChanges(): void {
    if (this.widget) {
      this.widget.remove();
      this.loadTradingViewWidget();
    }
  }
}