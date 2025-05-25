import { Component, Input, OnInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-trading-view-widget',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './trading-view-widget.component.html',
  styleUrls: []
})
export class TradingViewWidgetComponent implements OnInit, OnDestroy {
  @Input() symbol: string = 'BTCUSDT';
  @Input() interval: string = '1h';
  @Input() theme: 'light' | 'dark' = 'light';
  
  @ViewChild('tradingViewContainer', { static: true }) 
  tradingViewContainer!: ElementRef;

  ngOnInit(): void {
    // TradingView widget integration would go here
    // For now, we'll just show a placeholder
    this.loadTradingViewWidget();
  }

  ngOnDestroy(): void {
    // Cleanup TradingView widget if needed
  }

  private loadTradingViewWidget(): void {
    // Placeholder for TradingView widget loading
    // In a real implementation, you would load the TradingView script
    // and initialize the widget here
    console.log(`Loading TradingView widget for ${this.symbol} with ${this.interval} interval`);
  }
}