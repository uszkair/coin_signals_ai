import React, { useEffect, useRef, memo } from 'react'

function TradingViewWidget({ symbol = 'BTCUSDT', interval = '1h' }) {
  const containerRef = useRef(null)
  const widgetRef = useRef(null)

  // Convert interval to TradingView format
  const getIntervalForTradingView = (interval) => {
    switch (interval) {
      case '1m': return '1'
      case '5m': return '5'
      case '15m': return '15'
      case '1h': return '60'
      case '4h': return '240'
      case '1d': return 'D'
      default: return '60' // Default to 1h
    }
  }

  // Format symbol for TradingView
  const formatSymbol = (symbol) => {
    if (symbol.endsWith('USDT')) {
      return `BINANCE:${symbol.replace('USDT', 'USD')}`
    }
    return `BINANCE:${symbol}`
  }

  useEffect(() => {
    if (containerRef.current && typeof window.TradingView !== 'undefined') {
      // Clean up previous widget if it exists
      if (widgetRef.current) {
        containerRef.current.innerHTML = ''
      }

      // Create new widget
      widgetRef.current = new window.TradingView.widget({
        autosize: true,
        symbol: formatSymbol(symbol),
        interval: getIntervalForTradingView(interval),
        timezone: 'Etc/UTC',
        theme: 'light',
        style: '1',
        locale: 'en',
        toolbar_bg: '#f1f3f6',
        enable_publishing: false,
        allow_symbol_change: true,
        container_id: containerRef.current.id,
        studies: [
          'RSI@tv-basicstudies',
          'MACD@tv-basicstudies',
          'MAExp@tv-basicstudies',
          'BB@tv-basicstudies'
        ],
        disabled_features: ['use_localstorage_for_settings'],
        enabled_features: ['study_templates'],
        overrides: {
          'mainSeriesProperties.style': 1,
          'symbolWatermarkProperties.color': '#FF0000',
          'volumePaneSize': 'medium',
        }
      })
    }

    return () => {
      // Clean up
      if (widgetRef.current) {
        widgetRef.current = null
      }
    }
  }, [symbol, interval])

  return (
    <div className="tradingview-widget-container">
      <div 
        id="tradingview_widget" 
        ref={containerRef} 
        className="w-full h-[500px] rounded-lg overflow-hidden"
      />
    </div>
  )
}

export default memo(TradingViewWidget)