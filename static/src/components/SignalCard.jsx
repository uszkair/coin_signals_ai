import { useState } from 'react'
import { FaArrowUp, FaArrowDown, FaInfoCircle, FaChartLine } from 'react-icons/fa'

const SignalCard = ({ signal, onViewChart }) => {
  const [showDetails, setShowDetails] = useState(false)
  
  if (!signal) return null
  
  const { 
    symbol, 
    interval, 
    price, 
    rsi, 
    ema20, 
    signal: signalType, 
    entry, 
    stop_loss, 
    take_profit,
    timestamp
  } = signal
  
  // Format price with appropriate decimal places based on price magnitude
  const formatPrice = (price) => {
    if (!price) return 'N/A'
    
    if (price < 0.1) {
      return price.toFixed(6)
    } else if (price < 1) {
      return price.toFixed(4)
    } else if (price < 1000) {
      return price.toFixed(2)
    } else {
      return price.toFixed(0)
    }
  }
  
  // Calculate potential profit percentage
  const calculateProfit = () => {
    if (!entry || !take_profit) return null
    
    const profitPercentage = signalType === 'BUY'
      ? ((take_profit - entry) / entry) * 100
      : ((entry - take_profit) / entry) * 100
      
    return profitPercentage.toFixed(2)
  }
  
  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return ''
    
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } catch (e) {
      return ''
    }
  }
  
  // Determine card color based on signal type
  const getCardClass = () => {
    switch (signalType) {
      case 'BUY':
        return 'border-l-4 border-success'
      case 'SELL':
        return 'border-l-4 border-danger'
      default:
        return 'border-l-4 border-warning'
    }
  }
  
  // Determine signal badge color
  const getSignalBadgeClass = () => {
    switch (signalType) {
      case 'BUY':
        return 'bg-success'
      case 'SELL':
        return 'bg-danger'
      default:
        return 'bg-warning'
    }
  }
  
  // Check if symbol is a comma-separated list
  const isMultiSymbol = symbol && symbol.includes(',');
  
  // Format symbol for display
  const displaySymbol = isMultiSymbol
    ? symbol.split(',').map(s => s.replace('USDT', '')).join(', ') + 'USDT'
    : symbol;
  
  return (
    <div className={`card ${getCardClass()} mb-4`}>
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center">
          <h3 className="text-lg font-bold m-0 truncate max-w-[200px]" title={symbol}>
            {displaySymbol}
          </h3>
          <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
            {interval}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded text-sm font-medium text-white ${getSignalBadgeClass()}`}>
            {signalType}
          </span>
          
          <button
            onClick={() => {
              // If multiple symbols, use the first one for the chart
              const chartSymbol = isMultiSymbol ? symbol.split(',')[0] : symbol;
              onViewChart(chartSymbol, interval);
            }}
            className="p-1 text-primary hover:text-primary-dark"
            title={isMultiSymbol ? `View Chart (${symbol.split(',')[0]})` : "View Chart"}
          >
            <FaChartLine />
          </button>
        </div>
      </div>
      
      <div className="flex justify-between mb-2">
        <div>
          <span className="text-gray-600 dark:text-gray-400 text-sm">Price:</span>
          <span className="ml-1 font-medium">{formatPrice(price)}</span>
        </div>
        
        {timestamp && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {formatTime(timestamp)}
          </div>
        )}
      </div>
      
      {signalType !== 'HOLD' && (
        <div className="flex justify-between mb-2">
          <div>
            <span className="text-gray-600 dark:text-gray-400 text-sm">Entry:</span>
            <span className="ml-1 font-medium">{formatPrice(entry)}</span>
          </div>
          
          <div>
            <span className="text-gray-600 dark:text-gray-400 text-sm">Target:</span>
            <span className="ml-1 font-medium text-success">{formatPrice(take_profit)}</span>
            {calculateProfit() && (
              <span className="ml-1 text-xs text-success">
                ({calculateProfit()}%)
              </span>
            )}
          </div>
        </div>
      )}
      
      <div className="flex justify-between items-center mt-3">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center text-sm text-primary hover:text-primary-dark"
        >
          <FaInfoCircle className="mr-1" />
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
        
        {signalType !== 'HOLD' && (
          <div className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Stop Loss:</span>
            <span className="ml-1 font-medium text-danger">{formatPrice(stop_loss)}</span>
          </div>
        )}
      </div>
      
      {showDetails && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-gray-600 dark:text-gray-400 text-sm">RSI:</span>
              <span className="ml-1 font-medium">
                {rsi ? rsi.toFixed(1) : 'N/A'}
                {rsi && (
                  rsi < 30 ? (
                    <FaArrowDown className="inline ml-1 text-danger" />
                  ) : rsi > 70 ? (
                    <FaArrowUp className="inline ml-1 text-success" />
                  ) : null
                )}
              </span>
            </div>
            
            <div>
              <span className="text-gray-600 dark:text-gray-400 text-sm">EMA20:</span>
              <span className="ml-1 font-medium">
                {ema20 ? formatPrice(ema20) : 'N/A'}
                {price && ema20 && (
                  price > ema20 ? (
                    <FaArrowUp className="inline ml-1 text-success" />
                  ) : (
                    <FaArrowDown className="inline ml-1 text-danger" />
                  )
                )}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SignalCard