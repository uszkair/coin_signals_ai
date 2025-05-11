import { useState } from 'react'
import { Link } from 'react-router-dom'

function Header({ sidebarOpen, setSidebarOpen, tradingMode, toggleTradingMode }) {
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header className="sticky top-0 bg-white border-b border-gray-200 z-30">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 -mb-px">
          {/* Left: Hamburger button */}
          <div className="flex lg:hidden">
            <button
              className="text-gray-500 hover:text-gray-600"
              aria-controls="sidebar"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <span className="sr-only">Open sidebar</span>
              <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
                <path
                  d="M3 12h18M3 6h18M3 18h18"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>

          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <svg className="w-8 h-8 mr-2 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 2a8 8 0 100 16 8 8 0 000-16zm-1 12a1 1 0 102 0V6a1 1 0 10-2 0v8z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-lg font-bold text-gray-800">Crypto Trading Assistant</span>
            </Link>
          </div>

          {/* Right: Trading Mode Toggle + User Menu */}
          <div className="flex items-center space-x-3">
            {/* Trading Mode Toggle */}
            <div className="hidden md:flex items-center">
              <span className="mr-2 text-sm font-medium text-gray-600">
                {tradingMode === 'swing' ? 'Swing Trading' : 'Scalping'}
              </span>
              <button
                onClick={toggleTradingMode}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                  tradingMode === 'scalp' ? 'bg-primary-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    tradingMode === 'scalp' ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* User Menu */}
            <div className="relative inline-flex">
              <button
                className="inline-flex justify-center items-center group"
                aria-haspopup="true"
              >
                <div className="flex items-center truncate">
                  <span className="truncate ml-2 text-sm font-medium group-hover:text-gray-800">
                    User
                  </span>
                  <svg
                    className="w-3 h-3 shrink-0 ml-1 fill-current text-gray-400"
                    viewBox="0 0 12 12"
                  >
                    <path d="M5.9 11.4L.5 6l1.4-1.4 4 4 4-4L11.3 6z" />
                  </svg>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header