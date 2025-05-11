import { useState } from 'react'
import { toast } from 'react-toastify'

function Settings() {
  const [settings, setSettings] = useState({
    watchedSymbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'XRPUSDT', 'DOTUSDT'],
    refreshInterval: 60,
    notificationsEnabled: true,
    emailNotifications: false,
    email: '',
    scalping: {
      rsiThreshold: 35,
      profitTarget: 1.5,
      stopLoss: 1.0
    },
    swing: {
      rsiThreshold: 30,
      profitTarget: 5.0,
      stopLoss: 2.0
    }
  })

  const [newSymbol, setNewSymbol] = useState('')

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    
    if (name.includes('.')) {
      // Handle nested properties (e.g., scalping.rsiThreshold)
      const [category, property] = name.split('.')
      setSettings({
        ...settings,
        [category]: {
          ...settings[category],
          [property]: type === 'checkbox' ? checked : type === 'number' ? parseFloat(value) : value
        }
      })
    } else {
      // Handle top-level properties
      setSettings({
        ...settings,
        [name]: type === 'checkbox' ? checked : type === 'number' ? parseFloat(value) : value
      })
    }
  }

  const handleAddSymbol = () => {
    if (!newSymbol) return
    
    const formattedSymbol = newSymbol.toUpperCase().trim()
    
    if (settings.watchedSymbols.includes(formattedSymbol)) {
      toast.warning(`${formattedSymbol} is already in your watched symbols`)
      return
    }
    
    setSettings({
      ...settings,
      watchedSymbols: [...settings.watchedSymbols, formattedSymbol]
    })
    
    setNewSymbol('')
    toast.success(`${formattedSymbol} added to watched symbols`)
  }

  const handleRemoveSymbol = (symbol) => {
    setSettings({
      ...settings,
      watchedSymbols: settings.watchedSymbols.filter(s => s !== symbol)
    })
    
    toast.info(`${symbol} removed from watched symbols`)
  }

  const handleSaveSettings = () => {
    // In a real app, this would save to an API or localStorage
    console.log('Saving settings:', settings)
    toast.success('Settings saved successfully')
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Settings</h1>
        <p className="text-gray-600">Configure your trading assistant preferences</p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Watched Symbols</h2>
        
        <div className="flex flex-wrap gap-2 mb-4">
          {settings.watchedSymbols.map(symbol => (
            <div 
              key={symbol} 
              className="bg-gray-100 rounded-full px-3 py-1 text-sm flex items-center"
            >
              <span>{symbol}</span>
              <button 
                onClick={() => handleRemoveSymbol(symbol)}
                className="ml-2 text-gray-500 hover:text-red-500"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
        
        <div className="flex gap-2">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            placeholder="Add symbol (e.g., BTCUSDT)"
            className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          />
          <button
            onClick={handleAddSymbol}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Add
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">General Settings</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="refreshInterval" className="block text-sm font-medium text-gray-700 mb-1">
              Refresh Interval (seconds)
            </label>
            <input
              type="number"
              id="refreshInterval"
              name="refreshInterval"
              value={settings.refreshInterval}
              onChange={handleChange}
              min="10"
              max="3600"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>
          
          <div className="flex items-center h-full pt-6">
            <input
              type="checkbox"
              id="notificationsEnabled"
              name="notificationsEnabled"
              checked={settings.notificationsEnabled}
              onChange={handleChange}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="notificationsEnabled" className="ml-2 block text-sm text-gray-700">
              Enable Browser Notifications
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="emailNotifications"
              name="emailNotifications"
              checked={settings.emailNotifications}
              onChange={handleChange}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="emailNotifications" className="ml-2 block text-sm text-gray-700">
              Enable Email Notifications
            </label>
          </div>
          
          {settings.emailNotifications && (
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={settings.email}
                onChange={handleChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Scalping Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Scalping Settings</h2>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="scalping.rsiThreshold" className="block text-sm font-medium text-gray-700 mb-1">
                RSI Threshold
              </label>
              <input
                type="number"
                id="scalping.rsiThreshold"
                name="scalping.rsiThreshold"
                value={settings.scalping.rsiThreshold}
                onChange={handleChange}
                min="1"
                max="99"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="scalping.profitTarget" className="block text-sm font-medium text-gray-700 mb-1">
                Profit Target (%)
              </label>
              <input
                type="number"
                id="scalping.profitTarget"
                name="scalping.profitTarget"
                value={settings.scalping.profitTarget}
                onChange={handleChange}
                min="0.1"
                step="0.1"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="scalping.stopLoss" className="block text-sm font-medium text-gray-700 mb-1">
                Stop Loss (%)
              </label>
              <input
                type="number"
                id="scalping.stopLoss"
                name="scalping.stopLoss"
                value={settings.scalping.stopLoss}
                onChange={handleChange}
                min="0.1"
                step="0.1"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          </div>
        </div>

        {/* Swing Trading Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Swing Trading Settings</h2>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="swing.rsiThreshold" className="block text-sm font-medium text-gray-700 mb-1">
                RSI Threshold
              </label>
              <input
                type="number"
                id="swing.rsiThreshold"
                name="swing.rsiThreshold"
                value={settings.swing.rsiThreshold}
                onChange={handleChange}
                min="1"
                max="99"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="swing.profitTarget" className="block text-sm font-medium text-gray-700 mb-1">
                Profit Target (%)
              </label>
              <input
                type="number"
                id="swing.profitTarget"
                name="swing.profitTarget"
                value={settings.swing.profitTarget}
                onChange={handleChange}
                min="0.1"
                step="0.1"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="swing.stopLoss" className="block text-sm font-medium text-gray-700 mb-1">
                Stop Loss (%)
              </label>
              <input
                type="number"
                id="swing.stopLoss"
                name="swing.stopLoss"
                value={settings.swing.stopLoss}
                onChange={handleChange}
                min="0.1"
                step="0.1"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSaveSettings}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Save Settings
        </button>
      </div>
    </div>
  )
}

export default Settings