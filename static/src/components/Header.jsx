import { FaBars, FaMoon, FaSun, FaExchangeAlt } from 'react-icons/fa'
import { useState, useEffect } from 'react'

const Header = ({ toggleSidebar, tradingMode, toggleTradingMode }) => {
  const [darkMode, setDarkMode] = useState(false)

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode
    setDarkMode(newDarkMode)
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('darkMode', 'true')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('darkMode', 'false')
    }
  }

  // Initialize dark mode from localStorage
  useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode') === 'true'
    setDarkMode(savedDarkMode)
    
    if (savedDarkMode) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  return (
    <header className="bg-white dark:bg-gray-800 shadow-md py-4 px-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button 
            onClick={toggleSidebar}
            className="text-gray-600 dark:text-gray-300 focus:outline-none mr-4"
          >
            <FaBars className="h-6 w-6" />
          </button>
          <h1 className="text-xl font-bold text-gray-800 dark:text-white m-0">
            Crypto Trading Assistant
          </h1>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Trading Mode Toggle */}
          <div className="flex items-center">
            <button
              onClick={toggleTradingMode}
              className={`flex items-center px-3 py-1 rounded-md ${
                tradingMode === 'swing' 
                  ? 'bg-primary text-white' 
                  : 'bg-danger text-white'
              }`}
            >
              <FaExchangeAlt className="mr-2" />
              <span className="font-medium">
                {tradingMode === 'swing' ? 'Swing Mode' : 'Scalp Mode'}
              </span>
            </button>
          </div>
          
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className="text-gray-600 dark:text-gray-300 focus:outline-none"
          >
            {darkMode ? (
              <FaSun className="h-6 w-6 text-yellow-400" />
            ) : (
              <FaMoon className="h-6 w-6 text-gray-700" />
            )}
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header