// Обновлённый компонент Alerts с расширенным функционалом
import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Clock, Eye, EyeOff, Filter, ChevronDown, ChevronUp, Loader } from 'lucide-react';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    database_id: '',
    severity: '',
    resolved: false,
    alert_type: ''
  });
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0
  });
  const [databases, setDatabases] = useState([]);
  const [expandedAlert, setExpandedAlert] = useState(null);
  const [processingAlert, setProcessingAlert] = useState(null);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  const severityColors = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-blue-100 text-blue-800 border-blue-200'
  };

  const alertTypeIcons = {
    connection: '🔗',
    resource: '💾',
    performance: '⚡',
    anomaly: '🤖',
    security: '🔒'
  };

  useEffect(() => {
    loadDatabases();
    loadAlerts();
  }, []);

  useEffect(() => {
    loadAlerts();
  }, [filters, pagination.page]);

  const loadDatabases = async () => {
    try {
      const response = await fetch(`${API_BASE}/databases`);
      const data = await response.json();
      if (data.status === 'success') {
        setDatabases(data.data.filter(db => db.is_active));
      }
    } catch (err) {
      console.error('Failed to load databases:', err);
    }
  };

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        per_page: pagination.per_page.toString(),
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== '' && v !== false))
      });

      const response = await fetch(`${API_BASE}/alerts?${params}`);
      const data = await response.json();

      if (data.status === 'success') {
        setAlerts(data.data);
        setPagination(prev => ({
          ...prev,
          total: data.pagination.total,
          pages: data.pagination.pages
        }));
        setError(null);
      } else {
        setError(data.message || 'Failed to load alerts');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      setProcessingAlert(alertId);
      const response = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });

      const data = await response.json();
      if (data.status === 'success') {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, is_acknowledged: true }
            : alert
        ));
      } else {
        setError(data.message || 'Failed to acknowledge alert');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setProcessingAlert(null);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      setProcessingAlert(alertId);
      const response = await fetch(`${API_BASE}/alerts/${alertId}/resolve`, {
        method: 'POST'
      });

      const data = await response.json();
      if (data.status === 'success') {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, is_resolved: true, resolved_at: new Date().toISOString() }
            : alert
        ));
      } else {
        setError(data.message || 'Failed to resolve alert');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setProcessingAlert(null);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getTimeSince = (timestamp) => {
    const now = new Date();
    const alertTime = new Date(timestamp);
    const diffMs = now - alertTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'Just now';
  };

  const getDatabaseName = (databaseId) => {
    const db = databases.find(d => d.id === databaseId);
    return db ? db.name : `Database ${databaseId}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Alerts</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span>Total: {pagination.total}</span>
          <span>•</span>
          <span>Page {pagination.page} of {pagination.pages}</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {error}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-3">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filters</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Database</label>
            <select
              value={filters.database_id}
              onChange={(e) => setFilters({...filters, database_id: e.target.value})}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Databases</option>
              {databases.map(db => (
                <option key={db.id} value={db.id}>{db.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({...filters, severity: e.target.value})}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
            <select
              value={filters.alert_type}
              onChange={(e) => setFilters({...filters, alert_type: e.target.value})}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="connection">Connection</option>
              <option value="resource">Resource</option>
              <option value="performance">Performance</option>
              <option value="anomaly">Anomaly</option>
              <option value="security">Security</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.resolved}
              onChange={(e) => setFilters({...filters, resolved: e.target.value === 'true'})}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={false}>Active Only</option>
              <option value={true}>Resolved Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <Loader className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-600">Loading alerts...</span>
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Alerts Found</h3>
          <p className="text-gray-500">
            {Object.values(filters).some(v => v !== '' && v !== false) 
              ? 'No alerts match your current filters.' 
              : 'All systems are running smoothly!'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className="flex-shrink-0 mt-1">
                      <span className="text-lg">
                        {alertTypeIcons[alert.alert_type] || '⚠️'}
                      </span>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="text-sm font-semibold text-gray-900 truncate">
                          {alert.title}
                        </h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full border ${severityColors[alert.severity]}`}>
                          {alert.severity}
                        </span>
                        {alert.is_acknowledged && (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                            Acknowledged
                          </span>
                        )}
                        {alert.is_resolved && (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 border border-green-200">
                            Resolved
                          </span>
                        )}
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-2">
                        {alert.description}
                      </p>
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>{getDatabaseName(alert.database_id)}</span>
                        <span>•</span>
                        <span>{getTimeSince(alert.created_at)}</span>
                        <span>•</span>
                        <span className="capitalize">{alert.alert_source}</span>
                        {alert.metric_value && alert.threshold_value && (
                          <>
                            <span>•</span>
                            <span>
                              Value: {alert.metric_value} (Threshold: {alert.threshold_value})
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => setExpandedAlert(expandedAlert === alert.id ? null : alert.id)}
                      className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                      title="Toggle details"
                    >
                      {expandedAlert === alert.id ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                    
                    {!alert.is_acknowledged && !alert.is_resolved && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={processingAlert === alert.id}
                        className="px-3 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors disabled:opacity-50"
                        title="Acknowledge alert"
                      >
                        {processingAlert === alert.id ? (
                          <Loader className="w-3 h-3 animate-spin" />
                        ) : (
                          'Acknowledge'
                        )}
                      </button>
                    )}
                    
                    {!alert.is_resolved && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        disabled={processingAlert === alert.id}
                        className="px-3 py-1 text-xs font-medium text-green-600 hover:text-green-800 hover:bg-green-50 rounded transition-colors disabled:opacity-50"
                        title="Resolve alert"
                      >
                        {processingAlert === alert.id ? (
                          <Loader className="w-3 h-3 animate-spin" />
                        ) : (
                          'Resolve'
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Expanded Details */}
              {expandedAlert === alert.id && (
                <div className="border-t border-gray-200 bg-gray-50 p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Alert Details</h4>
                      <dl className="space-y-1">
                        <div className="flex justify-between">
                          <dt className="text-gray-500">Created:</dt>
                          <dd className="text-gray-900">{formatTimestamp(alert.created_at)}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-500">Type:</dt>
                          <dd className="text-gray-900 capitalize">{alert.alert_type}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-500">Source:</dt>
                          <dd className="text-gray-900 capitalize">{alert.alert_source}</dd>
                        </div>
                        {alert.resolved_at && (
                          <div className="flex justify-between">
                            <dt className="text-gray-500">Resolved:</dt>
                            <dd className="text-gray-900">{formatTimestamp(alert.resolved_at)}</dd>
                          </div>
                        )}
                      </dl>
                    </div>
                    
                    {alert.alert_metadata && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Metadata</h4>
                        <pre className="text-xs text-gray-600 bg-white p-2 rounded border overflow-x-auto">
                          {JSON.stringify(alert.alert_metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((pagination.page - 1) * pagination.per_page) + 1} to{' '}
            {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
            {pagination.total} alerts
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => setPagination(prev => ({...prev, page: prev.page - 1}))}
              disabled={pagination.page <= 1}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <span className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md">
              {pagination.page}
            </span>
            
            <button
              onClick={() => setPagination(prev => ({...prev, page: prev.page + 1}))}
              disabled={pagination.page >= pagination.pages}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Alerts;

