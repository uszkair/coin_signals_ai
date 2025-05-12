import React, { useState, useEffect, useRef } from 'react';
import { FaFilter, FaChartLine, FaTable, FaSync } from 'react-icons/fa';
import useSignalHistory from '../hooks/useSignalHistory';
import SignalTable from '../components/SignalTable';
import SignalDetailsModal from '../components/SignalDetailsModal';
import SignalChartOverlay from '../components/SignalChartOverlay';
import TradingViewWidget from '../components/TradingViewWidget';

const SignalHistoryPage = () => {
  // State for filters and view options
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState('1h');
  const [days, setDays] = useState(30);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'chart'
  const [filters, setFilters] = useState({
    signalType: 'all',
    minScore: 0,
    outcome: 'all',
    pattern: 'all'
  });
  
  // State for selected signal and modal
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Reference to TradingView widget
  const tradingViewRef = useRef(null);
  
  // Fetch signal history data
  const { 
    data: signals, 
    rawData: allSignals,
    loading, 
    error, 
    refetch 
  } = useSignalHistory({
    symbol,
    interval,
    days,
    filters
  });
  
  // Extract unique patterns for filter dropdown
  const uniquePatterns = [...new Set(allSignals.map(signal => signal.pattern))].filter(Boolean);
  
  // Handle row click in the table
  const handleRowClick = (signal) => {
    setSelectedSignal(signal);
    setIsModalOpen(true);
  };
  
  // Handle view on chart button click
  const handleViewOnChart = (signal) => {
    setViewMode('chart');
    setSelectedSignal(signal);
    setIsModalOpen(false);
    
    // Scroll to chart
    setTimeout(() => {
      document.getElementById('chart-section').scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };
  
  // Handle filter change
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Calculate statistics
  const calculateStats = () => {
    if (!allSignals || allSignals.length === 0) {
      return {
        total: 0,
        buy: 0,
        sell: 0,
        tpHits: 0,
        slHits: 0,
        winRate: 0
      };
    }
    
    const total = allSignals.length;
    const buy = allSignals.filter(s => s.signal === 'BUY').length;
    const sell = allSignals.filter(s => s.signal === 'SELL').length;
    const tpHits = allSignals.filter(s => s.outcome === 'take_profit_hit').length;
    const slHits = allSignals.filter(s => s.outcome === 'stop_loss_hit').length;
    const winRate = (tpHits / (tpHits + slHits) * 100) || 0;
    
    return {
      total,
      buy,
      sell,
      tpHits,
      slHits,
      winRate: winRate.toFixed(1)
    };
  };
  
  const stats = calculateStats();
  
  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Signal History</h1>
      
      {/* Controls section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
          <h2 className="text-lg font-semibold mb-2 md:mb-0">Settings</h2>
          
          <div className="flex flex-wrap gap-2">
            {/* View mode toggle */}
            <div className="flex rounded-md overflow-hidden border border-gray-300 dark:border-gray-600">
              <button
                onClick={() => setViewMode('table')}
                className={`px-3 py-2 text-sm flex items-center ${
                  viewMode === 'table' 
                    ? 'bg-primary text-white' 
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200'
                }`}
              >
                <FaTable className="mr-1" />
                Table
              </button>
              <button
                onClick={() => setViewMode('chart')}
                className={`px-3 py-2 text-sm flex items-center ${
                  viewMode === 'chart' 
                    ? 'bg-primary text-white' 
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200'
                }`}
              >
                <FaChartLine className="mr-1" />
                Chart
              </button>
            </div>
            
            {/* Refresh button */}
            <button
              onClick={refetch}
              className="btn btn-primary py-2 px-3 flex items-center"
              disabled={loading}
            >
              <FaSync className={`mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Symbol selector */}
          <div>
            <label htmlFor="symbol" className="block text-sm font-medium mb-1">
              Symbol
            </label>
            <select
              id="symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value="BTCUSDT">BTCUSDT</option>
              <option value="ETHUSDT">ETHUSDT</option>
              <option value="SOLUSDT">SOLUSDT</option>
              <option value="BNBUSDT">BNBUSDT</option>
              <option value="ADAUSDT">ADAUSDT</option>
            </select>
          </div>
          
          {/* Interval selector */}
          <div>
            <label htmlFor="interval" className="block text-sm font-medium mb-1">
              Interval
            </label>
            <select
              id="interval"
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value="15m">15m</option>
              <option value="1h">1h</option>
              <option value="4h">4h</option>
              <option value="1d">1d</option>
            </select>
          </div>
          
          {/* Days selector */}
          <div>
            <label htmlFor="days" className="block text-sm font-medium mb-1">
              Lookback Days
            </label>
            <select
              id="days"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Filters section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
        <div className="flex items-center mb-4">
          <FaFilter className="text-gray-500 dark:text-gray-400 mr-2" />
          <h2 className="text-lg font-semibold">Filters</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Signal type filter */}
          <div>
            <label htmlFor="signalType" className="block text-sm font-medium mb-1">
              Signal Type
            </label>
            <select
              id="signalType"
              name="signalType"
              value={filters.signalType}
              onChange={handleFilterChange}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value="all">All Signals</option>
              <option value="BUY">Buy Signals</option>
              <option value="SELL">Sell Signals</option>
              <option value="HOLD">Hold Signals</option>
            </select>
          </div>
          
          {/* Min score filter */}
          <div>
            <label htmlFor="minScore" className="block text-sm font-medium mb-1">
              Min Score
            </label>
            <select
              id="minScore"
              name="minScore"
              value={filters.minScore}
              onChange={handleFilterChange}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value={0}>Any Score</option>
              <option value={1}>1+</option>
              <option value={2}>2+</option>
              <option value={3}>3+</option>
              <option value={4}>4 Only</option>
            </select>
          </div>
          
          {/* Outcome filter */}
          <div>
            <label htmlFor="outcome" className="block text-sm font-medium mb-1">
              Outcome
            </label>
            <select
              id="outcome"
              name="outcome"
              value={filters.outcome}
              onChange={handleFilterChange}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value="all">All Outcomes</option>
              <option value="take_profit_hit">Take Profit Hit</option>
              <option value="stop_loss_hit">Stop Loss Hit</option>
              <option value="undecided">Pending</option>
            </select>
          </div>
          
          {/* Pattern filter */}
          <div>
            <label htmlFor="pattern" className="block text-sm font-medium mb-1">
              Pattern
            </label>
            <select
              id="pattern"
              name="pattern"
              value={filters.pattern}
              onChange={handleFilterChange}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value="all">All Patterns</option>
              {uniquePatterns.map(pattern => (
                <option key={pattern} value={pattern}>{pattern}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      {/* Statistics section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">Statistics</h2>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
            <div className="text-sm text-gray-500 dark:text-gray-400">Total Signals</div>
            <div className="text-2xl font-bold">{stats.total}</div>
          </div>
          
          <div className="p-3 bg-green-50 dark:bg-green-900 dark:bg-opacity-20 rounded-md">
            <div className="text-sm text-gray-500 dark:text-gray-400">Buy Signals</div>
            <div className="text-2xl font-bold text-success">{stats.buy}</div>
          </div>
          
          <div className="p-3 bg-red-50 dark:bg-red-900 dark:bg-opacity-20 rounded-md">
            <div className="text-sm text-gray-500 dark:text-gray-400">Sell Signals</div>
            <div className="text-2xl font-bold text-danger">{stats.sell}</div>
          </div>
          
          <div className="p-3 bg-green-50 dark:bg-green-900 dark:bg-opacity-20 rounded-md">
            <div className="text-sm text-gray-500 dark:text-gray-400">TP Hits</div>
            <div className="text-2xl font-bold text-success">{stats.tpHits}</div>
          </div>
          
          <div className="p-3 bg-red-50 dark:bg-red-900 dark:bg-opacity-20 rounded-md">
            <div className="text-sm text-gray-500 dark:text-gray-400">SL Hits</div>
            <div className="text-2xl font-bold text-danger">{stats.slHits}</div>
          </div>
          
          <div className="p-3 bg-blue-50 dark:bg-blue-900 dark:bg-opacity-20 rounded-md">
            <div className="text-sm text-gray-500 dark:text-gray-400">Win Rate</div>
            <div className="text-2xl font-bold text-primary">{stats.winRate}%</div>
          </div>
        </div>
      </div>
      
      {/* Chart view */}
      {viewMode === 'chart' && (
        <div id="chart-section" className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
          <h2 className="text-lg font-semibold mb-4">Chart with Signals</h2>
          
          <div className="h-[600px] w-full">
            <TradingViewWidget
              symbol={symbol}
              interval={interval}
              ref={tradingViewRef}
            />
            
            <SignalChartOverlay
              signals={signals}
              widget={tradingViewRef.current}
              onMarkerClick={handleRowClick}
            />
          </div>
        </div>
      )}
      
      {/* Table view */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
        <h2 className="text-lg font-semibold mb-4">Signal List</h2>
        
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
        ) : signals.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No signals found for the selected criteria.
          </div>
        ) : (
          <SignalTable
            signals={signals}
            onRowClick={handleRowClick}
          />
        )}
      </div>
      
      {/* Signal details modal */}
      <SignalDetailsModal
        signal={selectedSignal}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onViewChart={handleViewOnChart}
      />
    </div>
  );
};

export default SignalHistoryPage;