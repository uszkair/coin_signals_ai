import { useState, useEffect } from 'react'
import { useSymbols } from '../hooks/useApi'
import TradingViewWidget from '../components/TradingViewWidget'
import { FaSync, FaChevronDown } from 'react-icons/fa'

const Dashboard = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [selectedInterval, setSelectedInterval] = useState('1h')
  const [showChart, setShowChart] = useState(true)
  const [activeSymbols, setActiveSymbols] = useState([])
  
  // Fetch available symbols
  const { data: symbolsData, loading: symbolsLoading } = useSymbols()
  
  // No longer fetching signals
  
  // Initialize active symbols when symbols data is loaded
  useEffect(() => {
    if (symbolsData && symbolsData.symbols && symbolsData.symbols.length > 0) {
      // Start with first 4 symbols
      setActiveSymbols(symbolsData.symbols.slice(0, 4))
    }
  }, [symbolsData])
  
  // No longer need to refresh signals
  
  // Handle symbol selection
  const handleSymbolChange = (event) => {
    setSelectedSymbol(event.target.value)
  }
  
  // Handle interval selection
  const handleIntervalChange = (event) => {
    setSelectedInterval(event.target.value)
  }
  
  // Handle refresh button click
  const handleRefresh = () => {
    // Just refresh the page for now
    window.location.reload()
  }
  
  // Toggle symbol in active symbols list
  const toggleSymbol = (symbol) => {
    if (activeSymbols.includes(symbol)) {
      setActiveSymbols(activeSymbols.filter(s => s !== symbol))
    } else {
      setActiveSymbols([...activeSymbols, symbol])
    }
  }
  
  // Available intervals
  const getAvailableIntervals = () => {
    return ['1m', '5m', '15m', '1h', '4h', '1d']
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
                >
                  <FaSync />
                </button>
              </div>
            </div>
            
            {/* TradingView Chart */}
            {showChart && (
              <div className="h-[500px] w-full">
                <TradingViewWidget
                  symbol={selectedSymbol}
                  interval={selectedInterval}
                />
              </div>
            )}
          </div>
          
        </div>
        
        {/* Right column - Symbol List */}
        <div className="lg:w-1/3">
          <div className="card p-4">
            <h2 className="text-xl font-bold mb-4">Available Symbols</h2>
            
            <div className="space-y-2">
              {symbolsLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin inline-block w-6 h-6 border-4 border-current border-t-transparent text-primary rounded-full" role="status">
                    <span className="sr-only">Loading...</span>
                  </div>
                  <p className="mt-2">Loading symbols...</p>
                </div>
              ) : (
                <div className="max-h-[500px] overflow-y-auto">
                  {symbolsData?.symbols?.map(symbol => (
                    <div
                      key={symbol}
                      className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer"
                      onClick={() => setSelectedSymbol(symbol)}
                    >
                      <div className="flex items-center justify-between">
                        <span className={selectedSymbol === symbol ? "font-bold text-primary" : ""}>
                          {symbol}
                        </span>
                        {selectedSymbol === symbol && (
                          <span className="text-xs bg-primary text-white px-2 py-1 rounded">
                            Selected
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard