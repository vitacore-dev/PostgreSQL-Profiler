import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Database, 
  Activity, 
  BarChart3, 
  Settings, 
  AlertTriangle, 
  Lightbulb,
  Menu,
  X,
  Server,
  Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// Компоненты страниц
import Dashboard from './components/Dashboard';
import DatabaseConnections from './components/DatabaseConnections';
import QueryAnalyzer from './components/QueryAnalyzer';
import PerformanceMetrics from './components/PerformanceMetrics';
import Alerts from './components/Alerts';
import Recommendations from './components/Recommendations';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const location = useLocation();
  
  const menuItems = [
    { path: '/', icon: BarChart3, label: 'Dashboard', color: 'text-blue-500' },
    { path: '/databases', icon: Database, label: 'Databases', color: 'text-green-500' },
    { path: '/queries', icon: Activity, label: 'Query Analyzer', color: 'text-purple-500' },
    { path: '/metrics', icon: Server, label: 'Performance', color: 'text-orange-500' },
    { path: '/alerts', icon: AlertTriangle, label: 'Alerts', color: 'text-red-500' },
    { path: '/recommendations', icon: Lightbulb, label: 'Recommendations', color: 'text-yellow-500' },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: -300 }}
          animate={{ x: 0 }}
          exit={{ x: -300 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed left-0 top-0 h-full w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 z-50 shadow-xl"
        >
          <div className="p-6">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  PG Profiler
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="lg:hidden"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            
            <nav className="space-y-2">
              {menuItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsOpen(false)}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    <item.icon className={`w-5 h-5 ${isActive ? 'text-blue-500' : item.color}`} />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const Header = ({ sidebarOpen, setSidebarOpen }) => {
  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </Button>
          
          <div className="hidden lg:flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              PostgreSQL Profiler
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            Connected
          </Badge>
          
          <Button variant="ghost" size="sm">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  );
};

const MainContent = () => {
  return (
    <div className="flex-1 overflow-auto">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/databases" element={<DatabaseConnections />} />
        <Route path="/queries" element={<QueryAnalyzer />} />
        <Route path="/metrics" element={<PerformanceMetrics />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/recommendations" element={<Recommendations />} />
      </Routes>
    </div>
  );
};

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Закрываем сайдбар при изменении размера экрана
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setSidebarOpen(true);
      } else {
        setSidebarOpen(false);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
        
        <div className={`flex flex-col min-h-screen transition-all duration-300 ${
          sidebarOpen && window.innerWidth >= 1024 ? 'lg:ml-64' : ''
        }`}>
          <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
          <MainContent />
        </div>
        
        {/* Overlay для мобильных устройств */}
        {sidebarOpen && window.innerWidth < 1024 && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </div>
    </Router>
  );
}

export default App;

