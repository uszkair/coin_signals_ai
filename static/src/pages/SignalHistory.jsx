import { useState, useEffect } from 'react'
import { format } from 'date-fns'

function SignalHistory() {
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all') // 'all', 'buy', 'sell'
  const [dateRange, setDateRange] = useState('today') // 'today', 'week', 'month', 'all'

  // Fetch signal history
  useEffect(() => {
    const fetchSignalHistory = async () => {
      try {
        setLoading(true)
        // In a real app, this would be an API call to get the signal history
        // For now, we'll simulate it with a fetch to a local endpoint
        const response = await fetch('/api/signal-history')
        
        // If the endpoint doesn't exist yet, we'll use mock data
        if (!response.ok) {
          // Mock data for demonstration
          const mockData = generateMockData()
          setSignals(mockData)
          return
        }
        
        const data = await response.json()
        setSignals(data)
      } catch (err) {
        console.error('Error fetching signal history:', err)
        setError('Failed to load signal history')
        // Use mock data as fallback
        setSignals(generateMockData())
      } finally {
        setLoading(false)
      }
    }

    fetchSignalHistory()
  }, [])

  // Generate mock data for demonstration
  const generateMockData = () => {
    const mockData = []
    const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT']
    const intervals = ['1h', '4h', '1d']
    const signals = ['BUY', 'SELL']
    
    // Generate data for the past 30 days
    for (let i = 0; i < 50; i++) {
      const date = new Date()
      date.setDate(date.getDate() - Math.floor(Math.random() * 30))
      
      const symbol = symbols[Math.floor(Math.random() * symbols.length)]
      const interval = intervals[Math.floor(Math.random() * intervals.length)]
      const signal = signals[Math.floor(Math.random() * signals.length)]
      const price = Math.random() * 50000 + 1000
      
      mockData.push({
        id: i,
        symbol,
        interval,
        signal,
        price,
        timestamp: date.toISOString(),
        rsi: Math.random() * 100,
        ema20: price * (0.9 + Math.random() * 0.2),
        entry: price,
        stop_loss: signal === 'BUY' ? price * 0.95 : price * 1.05,
        take_profit: signal === 'BUY' ? price * 1.1 : price * 0.9,
        result: Math.random() > 0.5 ? 'success' : 'failure'
      })
    }
    
    return mockData
  }

  // Filter signals based on current filter
  const filteredSignals = signals.filter(signal => {
    if (filter !== 'all' && signal.signal.toLowerCase() !== filter) {
      return false
    }
    
    if (dateRange !== 'all') {
      const signalDate = new Date(signal.timestamp)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      
      if (dateRange === 'today' && signalDate < today) {
        return false
      }
      
      if (dateRange === 'week') {
        const weekAgo = new Date()
        weekAgo.setDate(weekAgo.getDate() - 7)
        weekAgo.setHours(0, 0, 0, 0)
        if (signalDate < weekAgo) {
          return false
        }
      }
      
      if (dateRange === 'month') {
        const monthAgo = new Date()
        monthAgo.setMonth(monthAgo.getMonth() - 1)
        monthAgo.setHours(0, 0, 0, 0)
        if (signalDate < monthAgo) {
          return false
        }
      }
    }
    
    return true
  })

  // Format price with 2 decimal places
  const formatPrice = (price) => {
    if (typeof price !== 'number') return 'N/A'
    return price.toFixed(2)
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Signal History</h1>
        <p className="text-gray-600">View and analyze past trading signals</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label htmlFor="filter-select" className="block text-sm font-medium text-gray-700 mb-1">
                Signal Type
              </label>
              <select
                id="filter-select"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="all">All Signals</option>
                <option value="buy">Buy Signals</option>
                <option value="sell">Sell Signals</option>
              </select>
            </div>

            <div>
              <label htmlFor="date-range-select" className="block text-sm font-medium text-gray-700 mb-1">
                Date Range
              </label>
              <select
                id="date-range-select"
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="today">Today</option>
                <option value="week">Last 7 Days</option>
                <option value="month">Last 30 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>
          </div>

          <div>
            <button
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Signal History Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="text-center py-8">
            <p>Loading signal history...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-500">
            <p>{error}</p>
          </div>
        ) : filteredSignals.length === 0 ? (
          <div className="text-center py-8">
            <p>No signals found matching the current filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date/Time
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Interval
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Signal
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Price
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entry
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stop Loss
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Take Profit
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Result
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSignals.map((signal) => (
                  <tr key={signal.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(signal.timestamp), 'yyyy-MM-dd HH:mm')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {signal.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {signal.interval}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        signal.signal === 'BUY' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {signal.signal}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${formatPrice(signal.price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${formatPrice(signal.entry)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${formatPrice(signal.stop_loss)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${formatPrice(signal.take_profit)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {signal.result && (
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          signal.result === 'success' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {signal.result === 'success' ? 'Success' : 'Failed'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default SignalHistory