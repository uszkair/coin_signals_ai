import { FaBars, FaMoon, FaSun, FaExchangeAlt } from 'react-icons/fa'
import { useState, useEffect } from 'react'

const Header = ({ toggleSidebar, tradingMode, toggleTradingMode, darkMode, toggleDarkMode }) => {

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
            <div className="relative inline-block w-[160px] h-8 rounded-full bg-gray-200 dark:bg-gray-700 cursor-pointer">
              {/* Toggle Switch */}
              <div
                className={`absolute top-0 bottom-0 w-1/2 rounded-full transition-all duration-300 ease-in-out ${
                  tradingMode === 'swing'
                    ? 'left-0 bg-primary'
                    : 'left-1/2 bg-danger'
                }`}
              ></div>
              
              {/* Labels */}
              <div className="absolute inset-0 flex">
                <div
                  className={`flex-1 flex items-center justify-center text-sm font-medium ${
                    tradingMode === 'swing' ? 'text-white' : 'text-gray-700 dark:text-gray-300'
                  }`}
                  onClick={() => tradingMode !== 'swing' && toggleTradingMode()}
                >
                  Swing
                </div>
                <div
                  className={`flex-1 flex items-center justify-center text-sm font-medium ${
                    tradingMode === 'scalp' ? 'text-white' : 'text-gray-700 dark:text-gray-300'
                  }`}
                  onClick={() => tradingMode !== 'scalp' && toggleTradingMode()}
                >
                  Scalp
                </div>
              </div>
            </div>
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