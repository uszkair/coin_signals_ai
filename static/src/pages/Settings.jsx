import { useState, useEffect } from 'react'
import { FaSave, FaRedo, FaCog, FaBell, FaChartLine } from 'react-icons/fa'

const Settings = ({ darkMode, setDarkMode }) => {
  const [settings, setSettings] = useState({
    // General settings
    refreshInterval: 60, // seconds
    darkMode: darkMode,
    
    // Notification settings
    enableNotifications: true,
    notifyOnBuy: true,
    notifyOnSell: true,
    
    // Trading settings
    defaultTradingMode: 'swing', // 'swing' or 'scalp'
    defaultTimeframe: '1h',
    defaultSymbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'],
    
    // Chart settings
    showVolume: true,
    showEMA: true,
    showRSI: true,
    showMACD: true,
    showBollingerBands: true,
  })
  
  const [saved, setSaved] = useState(false)
  
  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('cryptoSignalsSettings')
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings))
      } catch (e) {
        console.error('Error parsing saved settings:', e)
      }
    }
  }, [])
  
  // Update settings when darkMode prop changes
  useEffect(() => {
    setSettings(prev => ({ ...prev, darkMode }))
  }, [darkMode])
  
  // Handle input change
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    
    const newValue = type === 'checkbox' ? checked :
                     type === 'number' ? Number(value) :
                     value
    
    setSettings(prev => ({
      ...prev,
      [name]: newValue
    }))
    
    // Sync darkMode with App component
    if (name === 'darkMode') {
      setDarkMode(newValue)
    }
    
    // Reset saved status
    setSaved(false)
  }
  
  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Save settings to localStorage
    localStorage.setItem('cryptoSignalsSettings', JSON.stringify(settings))
    
    // Update dark mode in localStorage
    localStorage.setItem('darkMode', settings.darkMode.toString())
    
    // Apply dark mode
    if (settings.darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    
    // Show saved message
    setSaved(true)
    
    // Hide saved message after 3 seconds
    setTimeout(() => {
      setSaved(false)
    }, 3000)
  }
  
  // Reset settings to defaults
  const handleReset = () => {
    const defaultSettings = {
      refreshInterval: 60,
      darkMode: false,
      enableNotifications: true,
      notifyOnBuy: true,
      notifyOnSell: true,
      defaultTradingMode: 'swing',
      defaultTimeframe: '1h',
      defaultSymbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'],
      showVolume: true,
      showEMA: true,
      showRSI: true,
      showMACD: true,
      showBollingerBands: true,
    }
    
    setSettings(defaultSettings)
    setSaved(false)
  }
  
  return (
    <div className="container mx-auto">
      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold m-0">Settings</h1>
          
          <div className="flex space-x-2">
            <button
              type="button"
              onClick={handleReset}
              className="btn btn-secondary flex items-center"
            >
              <FaRedo className="mr-2" />
              Reset
            </button>
            
            <button
              type="submit"
              form="settings-form"
              className="btn btn-primary flex items-center"
            >
              <FaSave className="mr-2" />
              Save
            </button>
          </div>
        </div>
        
        {saved && (
          <div className="mb-4 p-3 bg-success bg-opacity-10 text-success rounded-md">
            Settings saved successfully!
          </div>
        )}
        
        <form id="settings-form" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* General Settings */}
            <div>
              <div className="flex items-center mb-4">
                <FaCog className="text-primary mr-2" />
                <h2 className="text-xl font-bold m-0">General Settings</h2>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="refreshInterval" className="block text-sm font-medium mb-1">
                    Data Refresh Interval (seconds)
                  </label>
                  <input
                    type="number"
                    id="refreshInterval"
                    name="refreshInterval"
                    min="10"
                    max="300"
                    value={settings.refreshInterval}
                    onChange={handleChange}
                    className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="darkMode"
                    name="darkMode"
                    checked={settings.darkMode}
                    onChange={handleChange}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                  />
                  <label htmlFor="darkMode" className="ml-2 block text-sm">
                    Dark Mode
                  </label>
                </div>
              </div>
              
              <div className="mt-8">
                <div className="flex items-center mb-4">
                  <FaBell className="text-primary mr-2" />
                  <h2 className="text-xl font-bold m-0">Notification Settings</h2>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="enableNotifications"
                      name="enableNotifications"
                      checked={settings.enableNotifications}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="enableNotifications" className="ml-2 block text-sm">
                      Enable Notifications
                    </label>
                  </div>
                  
                  <div className="flex items-center ml-6">
                    <input
                      type="checkbox"
                      id="notifyOnBuy"
                      name="notifyOnBuy"
                      checked={settings.notifyOnBuy}
                      onChange={handleChange}
                      disabled={!settings.enableNotifications}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label 
                      htmlFor="notifyOnBuy" 
                      className={`ml-2 block text-sm ${!settings.enableNotifications ? 'text-gray-400 dark:text-gray-600' : ''}`}
                    >
                      Notify on BUY Signals
                    </label>
                  </div>
                  
                  <div className="flex items-center ml-6">
                    <input
                      type="checkbox"
                      id="notifyOnSell"
                      name="notifyOnSell"
                      checked={settings.notifyOnSell}
                      onChange={handleChange}
                      disabled={!settings.enableNotifications}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label 
                      htmlFor="notifyOnSell" 
                      className={`ml-2 block text-sm ${!settings.enableNotifications ? 'text-gray-400 dark:text-gray-600' : ''}`}
                    >
                      Notify on SELL Signals
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Trading Settings */}
            <div>
              <div className="flex items-center mb-4">
                <FaChartLine className="text-primary mr-2" />
                <h2 className="text-xl font-bold m-0">Trading Settings</h2>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-3">
                    Default Trading Mode
                  </label>
                  <div className="flex space-x-4">
                    <div
                      className={`flex-1 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        settings.defaultTradingMode === 'swing'
                          ? 'border-primary bg-primary bg-opacity-10'
                          : 'border-gray-300 dark:border-gray-600'
                      }`}
                      onClick={() => handleChange({ target: { name: 'defaultTradingMode', value: 'swing', type: 'text' } })}
                    >
                      <div className="flex items-center mb-2">
                        <div className={`w-4 h-4 rounded-full mr-2 ${settings.defaultTradingMode === 'swing' ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                        <h3 className="font-bold text-lg">Swing Trading</h3>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Medium-term trading strategy using 1h and 4h timeframes. Suitable for less frequent trading with higher profit targets.
                      </p>
                    </div>
                    
                    <div
                      className={`flex-1 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        settings.defaultTradingMode === 'scalp'
                          ? 'border-danger bg-danger bg-opacity-10'
                          : 'border-gray-300 dark:border-gray-600'
                      }`}
                      onClick={() => handleChange({ target: { name: 'defaultTradingMode', value: 'scalp', type: 'text' } })}
                    >
                      <div className="flex items-center mb-2">
                        <div className={`w-4 h-4 rounded-full mr-2 ${settings.defaultTradingMode === 'scalp' ? 'bg-danger' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                        <h3 className="font-bold text-lg">Scalping</h3>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Short-term trading strategy using 1m and 5m timeframes. Suitable for frequent trading with smaller profit targets.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div>
                  <label htmlFor="defaultTimeframe" className="block text-sm font-medium mb-1">
                    Default Timeframe
                  </label>
                  <select
                    id="defaultTimeframe"
                    name="defaultTimeframe"
                    value={settings.defaultTimeframe}
                    onChange={handleChange}
                    className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
                  >
                    <option value="1m">1 minute</option>
                    <option value="5m">5 minutes</option>
                    <option value="15m">15 minutes</option>
                    <option value="1h">1 hour</option>
                    <option value="4h">4 hours</option>
                    <option value="1d">1 day</option>
                  </select>
                </div>
              </div>
              
              <div className="mt-8">
                <h3 className="text-lg font-medium mb-2">Chart Settings</h3>
                
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showVolume"
                      name="showVolume"
                      checked={settings.showVolume}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="showVolume" className="ml-2 block text-sm">
                      Show Volume
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showEMA"
                      name="showEMA"
                      checked={settings.showEMA}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="showEMA" className="ml-2 block text-sm">
                      Show EMA (20, 50)
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showRSI"
                      name="showRSI"
                      checked={settings.showRSI}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="showRSI" className="ml-2 block text-sm">
                      Show RSI
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showMACD"
                      name="showMACD"
                      checked={settings.showMACD}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="showMACD" className="ml-2 block text-sm">
                      Show MACD
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showBollingerBands"
                      name="showBollingerBands"
                      checked={settings.showBollingerBands}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="showBollingerBands" className="ml-2 block text-sm">
                      Show Bollinger Bands
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Settings