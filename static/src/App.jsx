import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
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
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      <Sidebar open={sidebarOpen} toggleSidebar={toggleSidebar} />
      
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header 
          toggleSidebar={toggleSidebar} 
          tradingMode={tradingMode} 
          toggleTradingMode={toggleTradingMode} 
        />
        
        <main className="flex-1 overflow-y-auto p-4">
          <Routes>
            <Route path="/" element={<Dashboard tradingMode={tradingMode} />} />
            <Route path="/history" element={<SignalHistory />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App