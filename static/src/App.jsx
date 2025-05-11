import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import SignalHistory from './pages/SignalHistory'
import Settings from './pages/Settings'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [tradingMode, setTradingMode] = useState('swing') // 'swing' or 'scalp'

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const toggleTradingMode = () => {
    setTradingMode(tradingMode === 'swing' ? 'scalp' : 'swing')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        sidebarOpen={sidebarOpen} 
        setSidebarOpen={setSidebarOpen}
        tradingMode={tradingMode}
        toggleTradingMode={toggleTradingMode}
      />

      {/* Main Content */}
      <div className="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
        <Header 
          sidebarOpen={sidebarOpen} 
          setSidebarOpen={setSidebarOpen} 
          tradingMode={tradingMode}
          toggleTradingMode={toggleTradingMode}
        />
        
        <main className="flex-grow p-4 sm:p-6 bg-gray-50">
          <Routes>
            <Route 
              path="/" 
              element={<Dashboard tradingMode={tradingMode} />} 
            />
            <Route 
              path="/history" 
              element={<SignalHistory />} 
            />
            <Route 
              path="/settings" 
              element={<Settings />} 
            />
            <Route 
              path="*" 
              element={<Navigate to="/" replace />} 
            />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App