import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { useSignals, useSignal, useSymbols } from '../hooks/useApi'
import SignalCard from '../components/SignalCard'
import TradingViewWidget from '../components/TradingViewWidget'

function Dashboard({ tradingMode }) {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [selectedInterval, setSelectedInterval] = useState('1h')
  const [autoRefresh, setAutoRefresh] = useState(true)
  
  // Fetch available symbols
  const { data: symbols, isLoading: symbolsLoading } = useSymbols()
  
  // Fetch signals for all coins
  const { 
    data: allSignals, 
    isLoading: allSignalsLoading, 
    error: allSignalsError,
    refetch: refetchAllSignals
  } = useSignals(null, selectedInterval, tradingMode, {
    refetchInterval: autoRefresh ? 60000 : false // Refresh every minute if autoRefresh is enabled
  })
  
  // Fetch detailed signal for selected coin
  const { 
    data: selectedSignal, 
    isLoading: selectedSignalLoading,
    refetch: refetchSelectedSignal
  } = useSignal(selectedSymbol, selectedInterval, tradingMode, {
    refetchInterval: autoRefresh ? 60000 : false // Refresh every minute if autoRefresh is enabled
  })

  // Handle errors
  useEffect(() => {
    if (allSignalsError) {
      toast.error(`Error fetching signals: ${allSignalsError.message}`)
    }
  }, [allSignalsError])

  // Handle manual refresh
  const handleRefresh = () => {
    refetchAllSignals()
    refetchSelectedSignal()
    toast.info('Signals refreshed')
  }

  // Handle symbol selection
  const handleSymbolChange = (e) => {
    setSelectedSymbol(e.target.value)
  }

  // Handle interval selection
  const handleIntervalChange = (e) => {
    setSelectedInterval(e.target.value)
  }

  // Filter signals by type
  const getBuySignals = () => {
    if (!allSignals) return []
    return allSignals.filter(signal => signal.signal === 'BUY')
  }

  const getSellSignals = () => {
    if (!allSignals) return []
    return allSignals.filter(signal => signal.signal === 'SELL')
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Trading Dashboard</h1>
        <p className="text-gray-600">
          Current Mode: <span className="font-semibold">{tradingMode === 'swing' ? 'Swing Trading' : 'Scalping'}</span>
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label htmlFor="symbol-select" className="block text-sm font-medium text-gray-700 mb-1">
                Symbol
              </label>
              <select
                id="symbol-select"
                value={selectedSymbol}
                onChange={handleSymbolChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                disabled={symbolsLoading}
              >
                {symbolsLoading ? (
                  <option>Loading...</option>
                ) : (
                  symbols?.map((symbol) => (
                    <option key={symbol} value={symbol}>
                      {symbol}
                    </option>
                  ))
                )}
              </select>
            </div>

            <div>
              <label htmlFor="interval-select" className="block text-sm font-medium text-gray-700 mb-1">
                Timeframe
              </label>
              <select
                id="interval-select"
                value={selectedInterval}
                onChange={handleIntervalChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center">
              <input
                id="auto-refresh"
                type="checkbox"
                checked={autoRefresh}
                onChange={() => setAutoRefresh(!autoRefresh)}
                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <label htmlFor="auto-refresh" className="ml-2 block text-sm text-gray-700">
                Auto Refresh
              </label>
            </div>

            <button
              onClick={handleRefresh}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-4 h-full">
            <h2 className="text-xl font-semibold mb-4">Chart: {selectedSymbol}</h2>
            <TradingViewWidget symbol={selectedSymbol} interval={selectedInterval} />
          </div>
        </div>

        {/* Selected Symbol Signal */}
        <div>
          <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <h2 className="text-xl font-semibold mb-4">Current Signal</h2>
            {selectedSignalLoading ? (
              <div className="text-center py-8">
                <p>Loading signal...</p>
              </div>
            ) : selectedSignal ? (
              <SignalCard signal={selectedSignal} />
            ) : (
              <div className="text-center py-8">
                <p>No signal available</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Buy and Sell Signals */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        {/* Buy Signals */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-xl font-semibold mb-4">Buy Signals</h2>
          {allSignalsLoading ? (
            <div className="text-center py-8">
              <p>Loading signals...</p>
            </div>
          ) : getBuySignals().length > 0 ? (
            getBuySignals().map((signal) => (
              <SignalCard key={signal.symbol} signal={signal} />
            ))
          ) : (
            <div className="text-center py-8">
              <p>No buy signals available</p>
            </div>
          )}
        </div>

        {/* Sell Signals */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-xl font-semibold mb-4">Sell Signals</h2>
          {allSignalsLoading ? (
            <div className="text-center py-8">
              <p>Loading signals...</p>
            </div>
          ) : getSellSignals().length > 0 ? (
            getSellSignals().map((signal) => (
              <SignalCard key={signal.symbol} signal={signal} />
            ))
          ) : (
            <div className="text-center py-8">
              <p>No sell signals available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard