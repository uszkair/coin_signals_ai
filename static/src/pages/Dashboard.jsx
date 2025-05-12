import { useState, useEffect, useCallback } from 'react'
import { useSymbols, useSignals, useSignal } from '../hooks/useApi'
import SignalCard from '../components/SignalCard'
import TradingViewWidget from '../components/TradingViewWidget'
import { FaSync, FaChevronDown } from 'react-icons/fa'

const Dashboard = ({ tradingMode }) => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [selectedInterval, setSelectedInterval] = useState('1h')
  const [showChart, setShowChart] = useState(true)
  const [activeSymbols, setActiveSymbols] = useState([])
  
  // Fetch available symbols
  const { data: symbolsData, loading: symbolsLoading } = useSymbols()
  
  // Fetch signals for all active symbols
  const { 
    data: signalsData, 
    loading: signalsLoading, 
    refetch: refetchSignals 
  } = useSignals(activeSymbols, selectedInterval, tradingMode)
  
  // Fetch detailed signal for selected symbol
  const {
    data: selectedSignalData,
    loading: selectedSignalLoading,
    refetch: refetchSelectedSignal
  } = useSignal(selectedSymbol, selectedInterval, tradingMode)
  
  // Initialize active symbols when symbols data is loaded
  useEffect(() => {
    if (symbolsData && symbolsData.symbols && symbolsData.symbols.length > 0) {
      // Start with first 4 symbols
      setActiveSymbols(symbolsData.symbols.slice(0, 4))
    }
  }, [symbolsData])
  
  // Refresh data when trading mode changes
  useEffect(() => {
    if (activeSymbols.length > 0) {
      refetchSignals()
    }
    if (selectedSymbol) {
      refetchSelectedSignal()
    }
  }, [tradingMode, selectedInterval, activeSymbols, selectedSymbol])
  
  // Handle symbol selection
  const handleSymbolChange = (event) => {
    setSelectedSymbol(event.target.value)
  }
  
  // Handle interval selection
  const handleIntervalChange = (event) => {
    setSelectedInterval(event.target.value)
  }
  
  // Handle view chart button click from signal card
  const handleViewChart = useCallback((symbol, interval) => {
    setSelectedSymbol(symbol)
    setSelectedInterval(interval)
    setShowChart(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])
  
  // Handle refresh button click
  const handleRefresh = () => {
    refetchSignals()
    refetchSelectedSignal()
  }
  
  // Toggle symbol in active symbols list
  const toggleSymbol = (symbol) => {
    if (activeSymbols.includes(symbol)) {
      setActiveSymbols(activeSymbols.filter(s => s !== symbol))
    } else {
      setActiveSymbols([...activeSymbols, symbol])
    }
  }
  
  // Get available intervals based on trading mode
  const getAvailableIntervals = () => {
    return tradingMode === 'scalp' 
      ? ['1m', '5m', '15m'] 
      : ['1h', '4h', '1d']
  }
  
  return (
    <div className="container mx-auto">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left column - Chart and controls */}
        <div className="lg:w-2/3">
          <div className="card mb-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4">
              <h2 className="text-xl font-bold m-0">Market Chart</h2>
              
              <div className="flex flex-wrap gap-2 mt-2 sm:mt-0">
                {/* Symbol selector */}
                <select
                  value={selectedSymbol}
                  onChange={handleSymbolChange}
                  className="bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm"
                >
                  {symbolsLoading ? (
                    <option>Loading...</option>
                  ) : (
                    symbolsData?.symbols?.map(symbol => (
                      <option key={symbol} value={symbol}>
                        {symbol}
                      </option>
                    ))
                  )}
                </select>
                
                {/* Interval selector */}
                <select
                  value={selectedInterval}
                  onChange={handleIntervalChange}
                  className="bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm"
                >
                  {getAvailableIntervals().map(interval => (
                    <option key={interval} value={interval}>
                      {interval}
                    </option>
                  ))}
                </select>
                
                {/* Refresh button */}
                <button
                  onClick={handleRefresh}
                  className="btn btn-primary py-2 px-3"
                  disabled={signalsLoading}
                >
                  <FaSync className={`${signalsLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>
            
            {/* TradingView Chart */}
            {showChart && (
              <div className="h-[500px] w-full">
                <TradingViewWidget 
                  symbol={selectedSymbol} 
                  interval={selectedInterval}
                  theme={document.documentElement.classList.contains('dark') ? 'dark' : 'light'}
                />
              </div>
            )}
          </div>
          
          {/* Selected Symbol Signal */}
          {selectedSignalData && !selectedSignalLoading && (
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-3">Current Signal</h2>
              <SignalCard 
                signal={selectedSignalData} 
                onViewChart={handleViewChart}
              />
            </div>
          )}
        </div>
        
        {/* Right column - Signals */}
        <div className="lg:w-1/3">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold m-0">
              Signals
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                {tradingMode === 'scalp' ? 'Scalping Mode' : 'Swing Mode'}
              </span>
            </h2>
            
            <div className="relative group">
              <button className="btn btn-secondary py-1 px-2 flex items-center">
                <span className="mr-1">Symbols</span>
                <FaChevronDown className="w-3 h-3" />
              </button>
              
              <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg z-10 hidden group-hover:block">
                <div className="p-2">
                  {symbolsData?.symbols?.map(symbol => (
                    <div key={symbol} className="flex items-center p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                      <input
                        type="checkbox"
                        id={`symbol-${symbol}`}
                        checked={activeSymbols.includes(symbol)}
                        onChange={() => toggleSymbol(symbol)}
                        className="mr-2"
                      />
                      <label htmlFor={`symbol-${symbol}`} className="cursor-pointer flex-1">
                        {symbol}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          {/* Signal cards */}
          <div className="space-y-4">
            {signalsLoading ? (
              <div className="card p-8 text-center">
                <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent text-primary rounded-full" role="status">
                  <span className="sr-only">Loading...</span>
                </div>
                <p className="mt-2">Loading signals...</p>
              </div>
            ) : signalsData && signalsData.length > 0 ? (
              signalsData.map((signal, index) => (
                <SignalCard 
                  key={`${signal.symbol}-${index}`} 
                  signal={signal} 
                  onViewChart={handleViewChart}
                />
              ))
            ) : (
              <div className="card p-6 text-center">
                <p>No signals available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard