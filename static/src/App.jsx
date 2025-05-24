import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  
  // Initialize dark mode from localStorage or system preference
  useEffect(() => {
    // Check localStorage first
    const savedDarkMode = localStorage.getItem('darkMode')
    
    if (savedDarkMode === 'true') {
      setDarkMode(true)
    } else if (savedDarkMode === 'false') {
      setDarkMode(false)
    } else {
      // If no preference in localStorage, check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setDarkMode(prefersDark)
      localStorage.setItem('darkMode', prefersDark ? 'true' : 'false')
    }
  }, [])
  
  // Update dark mode class on document when darkMode state changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      <Sidebar open={sidebarOpen} toggleSidebar={toggleSidebar} />
      
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          toggleSidebar={toggleSidebar}
          darkMode={darkMode}
          toggleDarkMode={() => {
            const newDarkMode = !darkMode
            setDarkMode(newDarkMode)
            localStorage.setItem('darkMode', newDarkMode ? 'true' : 'false')
          }}
        />
        
        <main className="flex-1 overflow-y-auto p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/settings" element={
              <Settings
                darkMode={darkMode}
                setDarkMode={(value) => {
                  setDarkMode(value)
                  localStorage.setItem('darkMode', value ? 'true' : 'false')
                }}
              />
            } />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App