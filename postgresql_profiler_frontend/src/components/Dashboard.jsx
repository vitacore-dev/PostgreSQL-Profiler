// Обновлённый Dashboard с отображением только сохранённых баз данных
import React, { useState, useEffect } from 'react';
import { Database, Activity, AlertTriangle, TrendingUp, Clock, Users, Cpu, HardDrive, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const Dashboard = () => {
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [databases, setDatabases] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  useEffect(() => {
    loadDatabases();
  }, []);

  useEffect(() => {
    if (selectedDatabase) {
      loadDashboardData(selectedDatabase.id);
      // Автообновление каждые 30 секунд
      const interval = setInterval(() => loadDashboardData(selectedDatabase.id), 30000);
      return () => clearInterval(interval);
    }
  }, [selectedDatabase]);

  const loadDatabases = async () => {
    try {
      const response = await fetch(`${API_BASE}/databases`);
      const data = await response.json();
      
      if (data.status === 'success') {
        // Показываем только активные базы данных
        const activeDatabases = data.data.filter(db => db.is_active);
        setDatabases(activeDatabases);
        
        // Автоматически выбираем первую базу данных
        if (activeDatabases.length > 0 && !selectedDatabase) {
          setSelectedDatabase(activeDatabases[0]);
        }
        setError(null);
      } else {
        setError(data.message || 'Failed to load databases');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
  };

  const loadDashboardData = async (databaseId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/databases/${databaseId}/dashboard`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setDashboardData(data.data);
        setError(null);
      } else {
        setError(data.message || 'Failed to load dashboard data');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatMetricValue = (value, unit = '') => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
      return value.toFixed(1) + unit;
    }
    return value + unit;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-yellow-600 bg-yellow-100';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      default:
        return 'text-blue-600 bg-blue-100 border-blue-200';
    }
  };

  if (databases.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Database className="w-16 h-16 text-gray-400 mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No Database Connections</h3>
        <p className="text-gray-500 mb-4">
          You need to add and save database connections before viewing the dashboard.
        </p>
        <p className="text-sm text-gray-400">
          Go to "Database Connections" to add your first database.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Database Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        {databases.length > 0 && (
          <div className="flex items-center space-x-3">
            <label className="text-sm font-medium text-gray-700">Database:</label>
            <select
              value={selectedDatabase?.id || ''}
              onChange={(e) => {
                const db = databases.find(d => d.id === parseInt(e.target.value));
                setSelectedDatabase(db);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {databases.map((db) => (
                <option key={db.id} value={db.id}>
                  {db.name} ({db.host}:{db.port})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {error}
          </div>
        </div>
      )}

      {selectedDatabase && (
        <>
          {/* Database Status Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Database className="w-8 h-8 text-blue-500" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{selectedDatabase.name}</h3>
                  <p className="text-sm text-gray-500">
                    {selectedDatabase.username}@{selectedDatabase.host}:{selectedDatabase.port}/{selectedDatabase.database}
                  </p>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedDatabase.connection_status)}`}>
                {selectedDatabase.connection_status || 'Unknown'}
              </div>
            </div>
            
            {selectedDatabase.last_connected && (
              <div className="mt-4 text-sm text-gray-500">
                Last connected: {new Date(selectedDatabase.last_connected).toLocaleString()}
              </div>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-gray-600">Loading dashboard data...</span>
            </div>
          ) : dashboardData ? (
            <>
              {/* Key Metrics */}
              {dashboardData.latest_metrics && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Active Connections</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {formatMetricValue(dashboardData.latest_metrics.active_connections)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatMetricValue(dashboardData.latest_metrics.connection_utilization, '%')} utilization
                        </p>
                      </div>
                      <Users className="w-8 h-8 text-blue-500" />
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">CPU Usage</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {formatMetricValue(dashboardData.latest_metrics.cpu_usage, '%')}
                        </p>
                        <p className="text-xs text-gray-500">System load</p>
                      </div>
                      <Cpu className="w-8 h-8 text-green-500" />
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Memory Usage</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {formatMetricValue(dashboardData.latest_metrics.memory_usage, '%')}
                        </p>
                        <p className="text-xs text-gray-500">RAM utilization</p>
                      </div>
                      <HardDrive className="w-8 h-8 text-purple-500" />
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Avg Query Time</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {formatMetricValue(dashboardData.latest_metrics.avg_query_time, 'ms')}
                        </p>
                        <p className="text-xs text-gray-500">Performance</p>
                      </div>
                      <Clock className="w-8 h-8 text-orange-500" />
                    </div>
                  </div>
                </div>
              )}

              {/* Alerts and Recommendations Summary */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Active Alerts</h3>
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                      <span className="text-sm font-medium text-red-600">
                        {dashboardData.active_alerts_count || 0}
                      </span>
                    </div>
                  </div>
                  
                  {dashboardData.active_alerts_count > 0 ? (
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        You have {dashboardData.active_alerts_count} active alert{dashboardData.active_alerts_count !== 1 ? 's' : ''} 
                        that require attention.
                      </p>
                      <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                        View all alerts →
                      </button>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No active alerts. System is running smoothly.</p>
                  )}
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-5 h-5 text-blue-500" />
                      <span className="text-sm font-medium text-blue-600">
                        {dashboardData.pending_recommendations_count || 0}
                      </span>
                    </div>
                  </div>
                  
                  {dashboardData.pending_recommendations_count > 0 ? (
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        {dashboardData.pending_recommendations_count} optimization recommendation{dashboardData.pending_recommendations_count !== 1 ? 's' : ''} 
                        available to improve performance.
                      </p>
                      <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                        View recommendations →
                      </button>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No pending recommendations. Database is well optimized.</p>
                  )}
                </div>
              </div>

              {/* Slow Queries */}
              {dashboardData.slow_queries && dashboardData.slow_queries.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Slow Queries</h3>
                  <div className="space-y-3">
                    {dashboardData.slow_queries.slice(0, 5).map((query, index) => (
                      <div key={query.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-xs font-medium text-gray-500">#{index + 1}</span>
                            <span className="text-sm font-medium text-gray-900">{query.query_type}</span>
                            <span className="text-xs text-gray-500">({query.calls} calls)</span>
                          </div>
                          <p className="text-sm text-gray-600 truncate max-w-md">
                            {query.query_text}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-red-600">
                            {formatMetricValue(query.mean_time, 'ms')}
                          </p>
                          <p className="text-xs text-gray-500">avg time</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <button className="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium">
                    View all queries →
                  </button>
                </div>
              )}

              {/* Performance Chart Placeholder */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Overview</h3>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Activity className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                    <p>Performance charts will be displayed here</p>
                    <p className="text-sm">Historical metrics visualization</p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
                <p className="text-gray-500">
                  Monitoring data will appear here once the system starts collecting metrics.
                </p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Dashboard;

