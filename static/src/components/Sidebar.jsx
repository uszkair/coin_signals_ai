import { Link, useLocation } from 'react-router-dom'
import { FaTimes, FaChartLine, FaHistory, FaCog } from 'react-icons/fa'

const Sidebar = ({ open, toggleSidebar }) => {
  const location = useLocation()
  
  // Navigation items
  const navItems = [
    {
      path: '/',
      name: 'Dashboard',
      icon: <FaChartLine className="w-5 h-5" />
    },
    {
      path: '/history',
      name: 'Signal History',
      icon: <FaHistory className="w-5 h-5" />
    },
    {
      path: '/signal-history',
      name: 'Signal Analyzer',
      icon: <FaHistory className="w-5 h-5" />
    },
    {
      path: '/settings',
      name: 'Settings',
      icon: <FaCog className="w-5 h-5" />
    }
  ]
  
  return (
    <>
      {/* Mobile sidebar backdrop */}
      {open && (
        <div 
          className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 shadow-lg transform 
        ${open ? 'translate-x-0' : '-translate-x-full'} 
        lg:translate-x-0 lg:static lg:inset-0 
        transition duration-300 ease-in-out
      `}>
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <h2 className="text-xl font-bold text-primary dark:text-primary">
            CryptoSignals
          </h2>
          <button 
            onClick={toggleSidebar}
            className="p-1 rounded-md lg:hidden focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <FaTimes className="w-6 h-6 text-gray-600 dark:text-gray-300" />
          </button>
        </div>
        
        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`
                    flex items-center px-4 py-3 rounded-lg transition-colors duration-200
                    ${location.pathname === item.path 
                      ? 'bg-primary text-white' 
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}
                  `}
                  onClick={() => window.innerWidth < 1024 && toggleSidebar()}
                >
                  <span className="mr-3">{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        
        <div className="absolute bottom-0 w-full p-4 border-t dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p>© 2025 CryptoSignals</p>
            <p>v1.0.0</p>
          </div>
        </div>
      </div>
    </>
  )
}

export default Sidebar