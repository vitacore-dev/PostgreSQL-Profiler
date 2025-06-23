import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Lightbulb, TrendingUp, AlertTriangle, CheckCircle, Clock, Database, Zap, Settings } from 'lucide-react';

const Recommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, performance, security, maintenance

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  useEffect(() => {
    loadRecommendations();
    // Автообновление каждые 5 минут
    const interval = setInterval(loadRecommendations, 300000);
    return () => clearInterval(interval);
  }, []);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/recommendations`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setRecommendations(data.data || []);
        setError(null);
      } else {
        setError(data.message || data.error || 'Failed to load recommendations');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const applyRecommendation = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/recommendations/${id}/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        // Обновляем локальное состояние
        setRecommendations(prev => prev.map(rec => 
          rec.id === id ? { ...rec, applied: true, applied_at: new Date().toISOString() } : rec
        ));
        setError(null);
      } else {
        setError(data.message || data.error || 'Failed to apply recommendation');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'performance': return <TrendingUp className="w-4 h-4" />;
      case 'security': return <AlertTriangle className="w-4 h-4" />;
      case 'maintenance': return <Settings className="w-4 h-4" />;
      case 'indexing': return <Database className="w-4 h-4" />;
      default: return <Lightbulb className="w-4 h-4" />;
    }
  };

  const filteredRecommendations = recommendations.filter(rec => 
    filter === 'all' || rec.category === filter
  );

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Recommendations</h1>
          <p className="text-gray-600 mt-1">AI-powered optimization recommendations</p>
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
        <h1 className="text-3xl font-bold text-gray-900">Recommendations</h1>
        <p className="text-gray-600 mt-1">AI-powered optimization recommendations</p>
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
      <div className="flex space-x-2">
        {['all', 'performance', 'security', 'maintenance', 'indexing'].map((filterType) => (
          <Button
            key={filterType}
            variant={filter === filterType ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(filterType)}
            className="capitalize"
          >
            {filterType === 'all' ? 'All' : filterType}
          </Button>
        ))}
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Lightbulb className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                <p className="text-2xl font-bold">{recommendations.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <div>
                <p className="text-sm font-medium text-gray-600">High Priority</p>
                <p className="text-2xl font-bold">
                  {recommendations.filter(r => r.priority === 'high').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium text-gray-600">Applied</p>
                <p className="text-2xl font-bold">
                  {recommendations.filter(r => r.applied).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold">
                  {recommendations.filter(r => !r.applied).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Список рекомендаций */}
      <div className="space-y-4">
        {filteredRecommendations.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Lightbulb className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations found</h3>
                <p className="text-gray-600">
                  {filter === 'all' 
                    ? 'No recommendations available at the moment.' 
                    : `No ${filter} recommendations found.`}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredRecommendations.map((recommendation) => (
            <Card key={recommendation.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    {getCategoryIcon(recommendation.category)}
                    <div>
                      <CardTitle className="text-lg">{recommendation.title}</CardTitle>
                      <CardDescription className="mt-1">
                        Database: {recommendation.database_name || `ID ${recommendation.database_id}`}
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getPriorityColor(recommendation.priority)}>
                      {recommendation.priority}
                    </Badge>
                    {recommendation.applied && (
                      <Badge className="bg-green-100 text-green-800">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Applied
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 mb-4">{recommendation.description}</p>
                
                <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Impact:</span>
                    <span className="ml-2 capitalize">{recommendation.impact}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Effort:</span>
                    <span className="ml-2 capitalize">{recommendation.effort}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Category:</span>
                    <span className="ml-2 capitalize">{recommendation.category}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    Created: {new Date(recommendation.created_at).toLocaleDateString()}
                  </span>
                  {!recommendation.applied && (
                    <Button
                      size="sm"
                      onClick={() => applyRecommendation(recommendation.id)}
                      className="flex items-center space-x-1"
                    >
                      <Zap className="w-4 h-4" />
                      <span>Apply</span>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default Recommendations;

