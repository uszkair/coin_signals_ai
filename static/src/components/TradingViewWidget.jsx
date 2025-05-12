import { useEffect, useRef, memo } from 'react'

const TradingViewWidget = memo(({ symbol = 'BTCUSDT', interval = '1h', theme = 'light' }) => {
  const containerRef = useRef(null)
  const widgetRef = useRef(null)
  
  // Convert interval to TradingView format
  const getIntervalForTradingView = (interval) => {
    switch (interval) {
      case '1m': return '1';
      case '5m': return '5';
      case '15m': return '15';
      case '30m': return '30';
      case '1h': return '60';
      case '4h': return '240';
      case '1d': return 'D';
      case '1w': return 'W';
      default: return '60'; // Default to 1h
    }
  }
  
  useEffect(() => {
    // Clean up previous widget if it exists
    if (widgetRef.current && containerRef.current) {
      containerRef.current.innerHTML = '';
    }
    
    // Skip if TradingView is not available
    if (!window.TradingView) {
      console.error('TradingView library not loaded');
      return;
    }
    
    // Create new widget
    const tradingViewInterval = getIntervalForTradingView(interval);
    
    // Format symbol for TradingView (add BINANCE: prefix)
    const formattedSymbol = `BINANCE:${symbol}`;
    
    widgetRef.current = new window.TradingView.widget({
      container_id: containerRef.current.id,
      autosize: true,
      symbol: formattedSymbol,
      interval: tradingViewInterval,
      timezone: 'Etc/UTC',
      theme: theme === 'dark' ? 'dark' : 'light',
      style: '1',
      locale: 'en',
      toolbar_bg: theme === 'dark' ? '#2A3042' : '#f1f3f6',
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      studies: [
        'RSI@tv-basicstudies',
        'MAExp@tv-basicstudies',
        'MACD@tv-basicstudies',
        'BB@tv-basicstudies'
      ],
      show_popup_button: true,
      popup_width: '1000',
      popup_height: '650',
      withdateranges: true,
    });
    
    return () => {
      // Clean up
      if (widgetRef.current && containerRef.current) {
        containerRef.current.innerHTML = '';
        widgetRef.current = null;
      }
    };
  }, [symbol, interval, theme]);
  
  return (
    <div 
      id="tradingview-widget-container" 
      ref={containerRef} 
      className="w-full h-full min-h-[400px] rounded-lg overflow-hidden"
    />
  );
});

TradingViewWidget.displayName = 'TradingViewWidget';

export default TradingViewWidget;