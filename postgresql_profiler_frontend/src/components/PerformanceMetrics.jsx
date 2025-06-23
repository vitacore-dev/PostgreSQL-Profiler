import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Activity, 
  Database, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

const PerformanceMetrics = () => {
  const [metrics, setMetrics] = useState([]);
  const [databases, setDatabases] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState('');
  const [timeRange, setTimeRange] = useState('24'); // hours
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentStats, setCurrentStats] = useState(null);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  useEffect(() => {
    loadDatabases();
  }, []);

  useEffect(() => {
    if (selectedDatabase) {
      loadMetrics();
      // Автообновление каждые 30 секунд
      const interval = setInterval(loadMetrics, 30000);
      return () => clearInterval(interval);
    }
  }, [selectedDatabase, timeRange]);

  const loadDatabases = async () => {
    try {
      const response = await fetch(`${API_BASE}/databases`);
      const data = await response.json();
      
      if (data.success) {
        setDatabases(data.data);
        if (data.data.length > 0) {
          setSelectedDatabase(data.data[0].id.toString());
        }
      } else {
        setError(data.error || 'Failed to load databases');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
  };

  const loadMetrics = async () => {
    if (!selectedDatabase) return;
    
    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE}/databases/${selectedDatabase}/metrics/history?hours=${timeRange}&per_page=100`
      );
      const data = await response.json();
      
      if (data.success) {
        // Преобразуем данные для графиков
        const formattedMetrics = data.data.map(metric => ({
          ...metric,
          timestamp: new Date(metric.timestamp).toLocaleTimeString(),
          cpu_usage: parseFloat(metric.cpu_usage) || 0,
          memory_usage: parseFloat(metric.memory_usage) || 0,
          disk_io: parseFloat(metric.disk_io) || 0,
          active_connections: parseInt(metric.active_connections) || 0,
          query_count: parseInt(metric.query_count) || 0,
          slow_queries: parseInt(metric.slow_queries) || 0
        })).reverse(); // Показываем от старых к новым
        
        setMetrics(formattedMetrics);
        
        // Вычисляем текущие статистики
        if (formattedMetrics.length > 0) {
          const latest = formattedMetrics[formattedMetrics.length - 1];
          const previous = formattedMetrics[formattedMetrics.length - 2];
          
          setCurrentStats({
            cpu_usage: {
              current: latest.cpu_usage,
              trend: previous ? latest.cpu_usage - previous.cpu_usage : 0
            },
            memory_usage: {
              current: latest.memory_usage,
              trend: previous ? latest.memory_usage - previous.memory_usage : 0
            },
            disk_io: {
              current: latest.disk_io,
              trend: previous ? latest.disk_io - previous.disk_io : 0
            },
            active_connections: {
              current: latest.active_connections,
              trend: previous ? latest.active_connections - previous.active_connections : 0
            },
            query_count: {
              current: latest.query_count,
              trend: previous ? latest.query_count - previous.query_count : 0
            },
            slow_queries: {
              current: latest.slow_queries,
              trend: previous ? latest.slow_queries - previous.slow_queries : 0
            }
          });
        }
        
        setError(null);
      } else {
        setError(data.error || 'Failed to load metrics');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUp className="w-4 h-4 text-red-500" />;
    if (trend < 0) return <TrendingDown className="w-4 h-4 text-green-500" />;
    return <div className="w-4 h-4" />;
  };

  const getTrendColor = (trend) => {
    if (trend > 0) return 'text-red-600';
    if (trend < 0) return 'text-green-600';
    return 'text-gray-600';
  };

  const formatValue = (value, type) => {
    switch (type) {
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'count':
        return value.toLocaleString();
      case 'mb':
        return `${(value / 1024 / 1024).toFixed(1)} MB/s`;
      default:
        return value.toString();
    }
  };

  if (loading && !metrics.length) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Performance Metrics</h1>
          <p className="text-gray-600 mt-1">Detailed performance analysis and metrics</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Performance Metrics</h1>
        <p className="text-gray-600 mt-1">Detailed performance analysis and metrics</p>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-red-800">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Фильтры */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium">Database:</label>
          <Select value={selectedDatabase} onValueChange={setSelectedDatabase}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select database" />
            </SelectTrigger>
            <SelectContent>
              {databases.map((db) => (
                <SelectItem key={db.id} value={db.id.toString()}>
                  {db.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium">Time Range:</label>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1 Hour</SelectItem>
              <SelectItem value="6">6 Hours</SelectItem>
              <SelectItem value="24">24 Hours</SelectItem>
              <SelectItem value="168">7 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={loadMetrics}
          disabled={loading}
          className="flex items-center space-x-1"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Текущие метрики */}
      {currentStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">CPU Usage</p>
                  <p className="text-2xl font-bold">{formatValue(currentStats.cpu_usage.current, 'percentage')}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <Cpu className="w-5 h-5 text-blue-500" />
                  {getTrendIcon(currentStats.cpu_usage.trend)}
                </div>
              </div>
              <p className={`text-xs ${getTrendColor(currentStats.cpu_usage.trend)}`}>
                {currentStats.cpu_usage.trend > 0 ? '+' : ''}{currentStats.cpu_usage.trend.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Memory Usage</p>
                  <p className="text-2xl font-bold">{formatValue(currentStats.memory_usage.current, 'percentage')}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <MemoryStick className="w-5 h-5 text-green-500" />
                  {getTrendIcon(currentStats.memory_usage.trend)}
                </div>
              </div>
              <p className={`text-xs ${getTrendColor(currentStats.memory_usage.trend)}`}>
                {currentStats.memory_usage.trend > 0 ? '+' : ''}{currentStats.memory_usage.trend.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Disk I/O</p>
                  <p className="text-2xl font-bold">{formatValue(currentStats.disk_io.current, 'mb')}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <HardDrive className="w-5 h-5 text-purple-500" />
                  {getTrendIcon(currentStats.disk_io.trend)}
                </div>
              </div>
              <p className={`text-xs ${getTrendColor(currentStats.disk_io.trend)}`}>
                {currentStats.disk_io.trend > 0 ? '+' : ''}{formatValue(currentStats.disk_io.trend, 'mb')}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Connections</p>
                  <p className="text-2xl font-bold">{formatValue(currentStats.active_connections.current, 'count')}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <Database className="w-5 h-5 text-orange-500" />
                  {getTrendIcon(currentStats.active_connections.trend)}
                </div>
              </div>
              <p className={`text-xs ${getTrendColor(currentStats.active_connections.trend)}`}>
                {currentStats.active_connections.trend > 0 ? '+' : ''}{currentStats.active_connections.trend}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Queries</p>
                  <p className="text-2xl font-bold">{formatValue(currentStats.query_count.current, 'count')}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <Activity className="w-5 h-5 text-cyan-500" />
                  {getTrendIcon(currentStats.query_count.trend)}
                </div>
              </div>
              <p className={`text-xs ${getTrendColor(currentStats.query_count.trend)}`}>
                {currentStats.query_count.trend > 0 ? '+' : ''}{currentStats.query_count.trend}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Slow Queries</p>
                  <p className="text-2xl font-bold">{formatValue(currentStats.slow_queries.current, 'count')}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="w-5 h-5 text-red-500" />
                  {getTrendIcon(currentStats.slow_queries.trend)}
                </div>
              </div>
              <p className={`text-xs ${getTrendColor(currentStats.slow_queries.trend)}`}>
                {currentStats.slow_queries.trend > 0 ? '+' : ''}{currentStats.slow_queries.trend}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU и Memory */}
        <Card>
          <CardHeader>
            <CardTitle>System Resources</CardTitle>
            <CardDescription>CPU and Memory usage over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="cpu_usage" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="CPU Usage (%)"
                />
                <Line 
                  type="monotone" 
                  dataKey="memory_usage" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="Memory Usage (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Database Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Database Activity</CardTitle>
            <CardDescription>Connections and queries over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="active_connections" 
                  stackId="1"
                  stroke="#f59e0b" 
                  fill="#f59e0b"
                  fillOpacity={0.6}
                  name="Active Connections"
                />
                <Area 
                  type="monotone" 
                  dataKey="query_count" 
                  stackId="2"
                  stroke="#06b6d4" 
                  fill="#06b6d4"
                  fillOpacity={0.6}
                  name="Query Count"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Disk I/O */}
        <Card>
          <CardHeader>
            <CardTitle>Disk I/O</CardTitle>
            <CardDescription>Disk input/output operations</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="disk_io" 
                  stroke="#8b5cf6" 
                  strokeWidth={2}
                  name="Disk I/O (MB/s)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Slow Queries */}
        <Card>
          <CardHeader>
            <CardTitle>Query Performance</CardTitle>
            <CardDescription>Slow queries tracking</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="slow_queries" 
                  stroke="#ef4444" 
                  fill="#ef4444"
                  fillOpacity={0.6}
                  name="Slow Queries"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {metrics.length === 0 && !loading && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No metrics data</h3>
              <p className="text-gray-600">
                {selectedDatabase 
                  ? 'No performance metrics found for the selected database and time range.' 
                  : 'Please select a database to view performance metrics.'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PerformanceMetrics;

