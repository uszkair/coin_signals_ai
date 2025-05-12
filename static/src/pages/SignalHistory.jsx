import { useState, useEffect } from 'react'
import { FaCalendarAlt, FaDownload, FaFilter } from 'react-icons/fa'
import axios from 'axios'

const SignalHistory = () => {
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [filter, setFilter] = useState({
    symbol: '',
    signalType: 'all' // 'all', 'BUY', 'SELL', 'HOLD'
  })
  
  // Fetch signal history for the selected date
  useEffect(() => {
    const fetchSignalHistory = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Format date for API request (YYYYMMDD)
        const formattedDate = date.replace(/-/g, '')
        
        // Fetch signals from the API
        const response = await axios.get(`/api/history/${formattedDate}`)
        setSignals(response.data || [])
      } catch (err) {
        console.error('Error fetching signal history:', err)
        setError('Failed to load signal history. Please try again later.')
        setSignals([])
      } finally {
        setLoading(false)
      }
    }
    
    fetchSignalHistory()
  }, [date])
  
  // Handle date change
  const handleDateChange = (e) => {
    setDate(e.target.value)
  }
  
  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilter(prev => ({ ...prev, [name]: value }))
  }
  
  // Filter signals based on current filter settings
  const filteredSignals = signals.filter(signal => {
    // Filter by symbol
    if (filter.symbol && !signal.symbol.includes(filter.symbol.toUpperCase())) {
      return false
    }
    
    // Filter by signal type
    if (filter.signalType !== 'all' && signal.signal !== filter.signalType) {
      return false
    }
    
    return true
  })
  
  // Export signals to CSV
  const exportToCSV = () => {
    if (filteredSignals.length === 0) return
    
    // Create CSV header
    const headers = Object.keys(filteredSignals[0]).join(',')
    
    // Create CSV rows
    const rows = filteredSignals.map(signal => {
      return Object.values(signal).map(value => {
        // Handle values with commas by wrapping in quotes
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value}"`
        }
        return value
      }).join(',')
    }).join('\n')
    
    // Combine header and rows
    const csv = `${headers}\n${rows}`
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `signals_${date}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    
    try {
      const date = new Date(timestamp)
      return date.toLocaleString()
    } catch (e) {
      return timestamp
    }
  }
  
  // Get signal type badge class
  const getSignalBadgeClass = (signalType) => {
    switch (signalType) {
      case 'BUY':
        return 'bg-success'
      case 'SELL':
        return 'bg-danger'
      default:
        return 'bg-warning'
    }
  }
  
  return (
    <div className="container mx-auto">
      <div className="card">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
          <h1 className="text-2xl font-bold m-0">Signal History</h1>
          
          <div className="flex flex-wrap gap-2 mt-2 sm:mt-0">
            {/* Date selector */}
            <div className="flex items-center bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2">
              <FaCalendarAlt className="text-gray-500 dark:text-gray-400 mr-2" />
              <input
                type="date"
                value={date}
                onChange={handleDateChange}
                className="bg-transparent border-none p-0 focus:outline-none focus:ring-0"
              />
            </div>
            
            {/* Export button */}
            <button
              onClick={exportToCSV}
              disabled={filteredSignals.length === 0}
              className="btn btn-primary flex items-center"
            >
              <FaDownload className="mr-2" />
              Export CSV
            </button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center mb-2">
            <FaFilter className="text-gray-500 dark:text-gray-400 mr-2" />
            <h3 className="text-lg font-medium m-0">Filters</h3>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="symbol" className="block text-sm font-medium mb-1">
                Symbol
              </label>
              <input
                type="text"
                id="symbol"
                name="symbol"
                value={filter.symbol}
                onChange={handleFilterChange}
                placeholder="e.g. BTC"
                className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
              />
            </div>
            
            <div>
              <label htmlFor="signalType" className="block text-sm font-medium mb-1">
                Signal Type
              </label>
              <select
                id="signalType"
                name="signalType"
                value={filter.signalType}
                onChange={handleFilterChange}
                className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
              >
                <option value="all">All Signals</option>
                <option value="BUY">Buy Signals</option>
                <option value="SELL">Sell Signals</option>
                <option value="HOLD">Hold Signals</option>
              </select>
            </div>
          </div>
        </div>
        
        {/* Results */}
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent text-primary rounded-full" role="status">
              <span className="sr-only">Loading...</span>
            </div>
            <p className="mt-2">Loading signals...</p>
          </div>
        ) : error ? (
          <div className="bg-danger-light text-danger p-4 rounded-lg">
            {error}
          </div>
        ) : filteredSignals.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No signals found for the selected date and filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Interval
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Signal
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Entry
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Target
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Stop Loss
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredSignals.map((signal, index) => (
                  <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {signal.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {signal.interval}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded text-xs font-medium text-white ${getSignalBadgeClass(signal.signal)}`}>
                        {signal.signal}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {signal.price?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {signal.entry?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {signal.take_profit?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {signal.stop_loss?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {formatTimestamp(signal.timestamp)}
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