import { FaBars, FaMoon, FaSun } from 'react-icons/fa'
import { useState, useEffect } from 'react'

const Header = ({ toggleSidebar, darkMode, toggleDarkMode }) => {

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