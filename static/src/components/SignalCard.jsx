import React from 'react'

function SignalCard({ signal }) {
  if (!signal) return null

  // Determine card style based on signal type
  const getSignalClass = () => {
    switch (signal.signal) {
      case 'BUY':
        return 'signal-buy'
      case 'SELL':
        return 'signal-sell'
      default:
        return 'signal-hold'
    }
  }

  // Format price with 2 decimal places
  const formatPrice = (price) => {
    if (typeof price !== 'number') return 'N/A'
    return price.toFixed(2)
  }

  // Format percentage
  const formatPercent = (value) => {
    if (typeof value !== 'number') return 'N/A'
    return `${value.toFixed(2)}%`
  }

  // Calculate potential profit percentage
  const calculateProfit = () => {
    if (!signal.entry || !signal.take_profit) return null
    const diff = signal.signal === 'BUY' 
      ? signal.take_profit - signal.entry 
      : signal.entry - signal.take_profit
    const percent = (Math.abs(diff) / signal.entry) * 100
    return percent.toFixed(2)
  }

  // Calculate potential loss percentage
  const calculateLoss = () => {
    if (!signal.entry || !signal.stop_loss) return null
    const diff = signal.signal === 'BUY' 
      ? signal.entry - signal.stop_loss 
      : signal.stop_loss - signal.entry
    const percent = (Math.abs(diff) / signal.entry) * 100
    return percent.toFixed(2)
  }

  const profit = calculateProfit()
  const loss = calculateLoss()
  const riskReward = profit && loss ? (parseFloat(profit) / parseFloat(loss)).toFixed(2) : null

  return (
    <div className={`card ${getSignalClass()} p-4 mb-4`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-lg font-bold">{signal.symbol}</h3>
          <p className="text-sm opacity-75">{signal.interval || '1h'}</p>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold">{signal.signal}</div>
          <p className="text-sm opacity-75">
            {signal.timestamp ? new Date(signal.timestamp).toLocaleTimeString() : 'Now'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4">
        <div>
          <p className="text-sm font-medium">Current Price</p>
          <p className="text-lg font-bold">${formatPrice(signal.price)}</p>
        </div>
        <div>
          <p className="text-sm font-medium">RSI</p>
          <p className="text-lg font-bold">{formatPrice(signal.rsi)}</p>
        </div>
        <div>
          <p className="text-sm font-medium">EMA20</p>
          <p className="text-lg font-bold">${formatPrice(signal.ema20)}</p>
        </div>
        {signal.ema20_4h && (
          <div>
            <p className="text-sm font-medium">EMA20 (4h)</p>
            <p className="text-lg font-bold">${formatPrice(signal.ema20_4h)}</p>
          </div>
        )}
      </div>

      {signal.signal !== 'HOLD' && signal.entry && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm font-medium">Entry</p>
              <p className="text-lg font-bold">${formatPrice(signal.entry)}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Stop Loss</p>
              <p className="text-lg font-bold">${formatPrice(signal.stop_loss)}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Take Profit</p>
              <p className="text-lg font-bold">${formatPrice(signal.take_profit)}</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mt-4">
            <div>
              <p className="text-sm font-medium">Potential Profit</p>
              <p className="text-lg font-bold text-green-600">{profit}%</p>
            </div>
            <div>
              <p className="text-sm font-medium">Potential Loss</p>
              <p className="text-lg font-bold text-red-600">{loss}%</p>
            </div>
            <div>
              <p className="text-sm font-medium">Risk/Reward</p>
              <p className="text-lg font-bold">{riskReward}:1</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SignalCard