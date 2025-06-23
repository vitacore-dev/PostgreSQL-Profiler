// Обновлённый компонент Database Connections с сохранением состояния
import React, { useState, useEffect } from 'react';
import { Plus, Database, Trash2, Edit, TestTube, AlertCircle, CheckCircle, Clock, Loader } from 'lucide-react';

const DatabaseConnections = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingConnection, setEditingConnection] = useState(null);
  const [testingConnection, setTestingConnection] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    host: '',
    port: 5432,
    database: '',
    username: '',
    password: '',
    ssl_mode: 'prefer',
    auto_monitoring: true,
    monitoring_interval: 60,
    alert_thresholds: {
      connection_utilization: 80,
      cpu_usage: 85,
      memory_usage: 90,
      disk_usage: 95,
      cache_hit_ratio: 90,
      avg_query_time: 1000,
      locks_count: 100,
      deadlocks_count: 1
    }
  });

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  useEffect(() => {
    loadConnections();
    // Автообновление каждые 30 секунд
    const interval = setInterval(loadConnections, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/databases`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setConnections(data.data);
        setError(null);
      } else {
        setError(data.message || 'Failed to load connections');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const url = editingConnection 
        ? `${API_BASE}/databases/${editingConnection.id}`
        : `${API_BASE}/databases`;
      
      const method = editingConnection ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.status === 'success') {
        await loadConnections(); // Перезагружаем список
        resetForm();
        setError(null);
      } else {
        setError(data.message || 'Failed to save connection');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this connection?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/databases/${id}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.status === 'success') {
        await loadConnections(); // Перезагружаем список
        setError(null);
      } else {
        setError(data.message || 'Failed to delete connection');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
  };

  const handleTest = async (connection) => {
    setTestingConnection(connection.id);
    
    try {
      const response = await fetch(`${API_BASE}/databases/${connection.id}`, {
        method: 'GET',
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Обновляем статус соединения в локальном состоянии
        setConnections(prev => prev.map(conn => 
          conn.id === connection.id 
            ? { ...conn, connection_status: 'connected', last_connected: new Date().toISOString() }
            : conn
        ));
        setError(null);
      } else {
        setError(`Test failed: ${data.message}`);
      }
    } catch (err) {
      setError('Test failed: ' + err.message);
    } finally {
      setTestingConnection(null);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      host: '',
      port: 5432,
      database: '',
      username: '',
      password: '',
      ssl_mode: 'prefer',
      auto_monitoring: true,
      monitoring_interval: 60,
      alert_thresholds: {
        connection_utilization: 80,
        cpu_usage: 85,
        memory_usage: 90,
        disk_usage: 95,
        cache_hit_ratio: 90,
        avg_query_time: 1000,
        locks_count: 100,
        deadlocks_count: 1
      }
    });
    setShowForm(false);
    setEditingConnection(null);
  };

  const handleEdit = (connection) => {
    setFormData({
      name: connection.name,
      host: connection.host,
      port: connection.port,
      database: connection.database,
      username: connection.username,
      password: '', // Не показываем пароль
      ssl_mode: connection.ssl_mode,
      auto_monitoring: connection.auto_monitoring,
      monitoring_interval: connection.monitoring_interval,
      alert_thresholds: connection.alert_thresholds || {
        connection_utilization: 80,
        cpu_usage: 85,
        memory_usage: 90,
        disk_usage: 95,
        cache_hit_ratio: 90,
        avg_query_time: 1000,
        locks_count: 100,
        deadlocks_count: 1
      }
    });
    setEditingConnection(connection);
    setShowForm(true);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  if (loading && connections.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading connections...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Database Connections</h2>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Connection</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        </div>
      )}

      {/* Connection Form */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingConnection ? 'Edit Connection' : 'Add New Connection'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Connection Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Production DB"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Host *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.host}
                    onChange={(e) => setFormData({...formData, host: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="localhost"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Port *
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.port}
                    onChange={(e) => setFormData({...formData, port: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Database *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.database}
                    onChange={(e) => setFormData({...formData, database: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="postgres"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password *
                  </label>
                  <input
                    type="password"
                    required={!editingConnection}
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={editingConnection ? "Leave empty to keep current" : ""}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    SSL Mode
                  </label>
                  <select
                    value={formData.ssl_mode}
                    onChange={(e) => setFormData({...formData, ssl_mode: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="disable">Disable</option>
                    <option value="allow">Allow</option>
                    <option value="prefer">Prefer</option>
                    <option value="require">Require</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Monitoring Interval (seconds)
                  </label>
                  <input
                    type="number"
                    min="30"
                    max="3600"
                    value={formData.monitoring_interval}
                    onChange={(e) => setFormData({...formData, monitoring_interval: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto_monitoring"
                  checked={formData.auto_monitoring}
                  onChange={(e) => setFormData({...formData, auto_monitoring: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="auto_monitoring" className="ml-2 block text-sm text-gray-900">
                  Enable automatic monitoring
                </label>
              </div>

              {/* Alert Thresholds */}
              <div className="border-t pt-4">
                <h4 className="text-md font-medium text-gray-900 mb-3">Alert Thresholds</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Connection Utilization (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.alert_thresholds.connection_utilization}
                      onChange={(e) => setFormData({
                        ...formData, 
                        alert_thresholds: {
                          ...formData.alert_thresholds,
                          connection_utilization: parseInt(e.target.value)
                        }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      CPU Usage (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.alert_thresholds.cpu_usage}
                      onChange={(e) => setFormData({
                        ...formData, 
                        alert_thresholds: {
                          ...formData.alert_thresholds,
                          cpu_usage: parseInt(e.target.value)
                        }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Memory Usage (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.alert_thresholds.memory_usage}
                      onChange={(e) => setFormData({
                        ...formData, 
                        alert_thresholds: {
                          ...formData.alert_thresholds,
                          memory_usage: parseInt(e.target.value)
                        }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Average Query Time (ms)
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={formData.alert_thresholds.avg_query_time}
                      onChange={(e) => setFormData({
                        ...formData, 
                        alert_thresholds: {
                          ...formData.alert_thresholds,
                          avg_query_time: parseInt(e.target.value)
                        }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors disabled:opacity-50"
                >
                  {loading ? 'Saving...' : (editingConnection ? 'Update' : 'Create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Connections List */}
      <div className="grid gap-4">
        {connections.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No database connections</h3>
            <p className="text-gray-500 mb-4">Get started by adding your first database connection.</p>
            <button
              onClick={() => setShowForm(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg inline-flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>Add Connection</span>
            </button>
          </div>
        ) : (
          connections.map((connection) => (
            <div key={connection.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <Database className="w-8 h-8 text-blue-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{connection.name}</h3>
                    <p className="text-sm text-gray-500">
                      {connection.username}@{connection.host}:{connection.port}/{connection.database}
                    </p>
                    {connection.last_connected && (
                      <p className="text-xs text-gray-400">
                        Last connected: {new Date(connection.last_connected).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium border flex items-center space-x-1 ${getStatusColor(connection.connection_status)}`}>
                    {getStatusIcon(connection.connection_status)}
                    <span className="capitalize">{connection.connection_status || 'unknown'}</span>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleTest(connection)}
                      disabled={testingConnection === connection.id}
                      className="p-2 text-gray-500 hover:text-blue-500 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50"
                      title="Test Connection"
                    >
                      {testingConnection === connection.id ? (
                        <Loader className="w-4 h-4 animate-spin" />
                      ) : (
                        <TestTube className="w-4 h-4" />
                      )}
                    </button>
                    
                    <button
                      onClick={() => handleEdit(connection)}
                      className="p-2 text-gray-500 hover:text-yellow-500 hover:bg-yellow-50 rounded-md transition-colors"
                      title="Edit Connection"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => handleDelete(connection.id)}
                      className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete Connection"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              {connection.auto_monitoring && (
                <div className="mt-4 flex items-center text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  Auto-monitoring enabled (every {connection.monitoring_interval}s)
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default DatabaseConnections;

