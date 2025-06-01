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
    if (this.widget && typeof this.widget.remove === 'function') {
      try {
        this.widget.remove();
      } catch (error) {
        console.warn('Error removing TradingView widget:', error);
      }
    }
    this.widget = null;
  }

  private loadTradingViewWidget(): void {
    // Load TradingView script if not already loaded
    if (!(window as any).TradingView) {
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = () => {
        setTimeout(() => this.initializeWidget(), 100); // Small delay to ensure DOM is ready
      };
      document.head.appendChild(script);
    } else {
      setTimeout(() => this.initializeWidget(), 100); // Small delay for DOM readiness
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
        locale: "en",
        toolbar_bg: "#f1f3f6",
        enable_publishing: false,
        allow_symbol_change: false,
        container_id: this.tradingViewContainer.nativeElement.id,
        // Reduced studies for faster loading
        studies: [
          "RSI@tv-basicstudies"
        ],
        show_popup_button: false, // Disable popup for faster loading
        loading_screen: { backgroundColor: "#ffffff" },
        disabled_features: [
          "use_localstorage_for_settings",
          "volume_force_overlay"
        ],
        enabled_features: [
          "hide_left_toolbar"
        ]
      });
    }
  }

  // Update widget when inputs change
  ngOnChanges(): void {
    if (this.widget && typeof this.widget.remove === 'function') {
      try {
        this.widget.remove();
      } catch (error) {
        console.warn('Error removing TradingView widget on change:', error);
      }
      this.widget = null;
    }
    this.loadTradingViewWidget();
  }
}