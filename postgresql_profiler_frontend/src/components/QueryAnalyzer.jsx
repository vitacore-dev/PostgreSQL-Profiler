import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Search, 
  Clock, 
  Database, 
  TrendingUp, 
  Filter,
  Eye,
  AlertTriangle
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const QueryAnalyzer = () => {
  const [queries] = useState([
    {
      id: 1,
      query: 'SELECT u.id, u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id WHERE u.created_at > $1',
      avgTime: 245.5,
      calls: 1250,
      totalTime: 306875,
      database: 'production',
      type: 'SELECT',
      lastSeen: '2025-06-18T10:30:00Z'
    },
    {
      id: 2,
      query: 'UPDATE orders SET status = $1, updated_at = NOW() WHERE id = $2',
      avgTime: 189.2,
      calls: 890,
      totalTime: 168428,
      database: 'production',
      type: 'UPDATE',
      lastSeen: '2025-06-18T10:25:00Z'
    },
    {
      id: 3,
      query: 'INSERT INTO logs (level, message, created_at) VALUES ($1, $2, NOW())',
      avgTime: 156.8,
      calls: 2340,
      totalTime: 366912,
      database: 'analytics',
      type: 'INSERT',
      lastSeen: '2025-06-18T10:28:00Z'
    }
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');

  const queryTypeData = [
    { type: 'SELECT', count: 1250, avgTime: 245.5 },
    { type: 'INSERT', count: 2340, avgTime: 156.8 },
    { type: 'UPDATE', count: 890, avgTime: 189.2 },
    { type: 'DELETE', count: 120, avgTime: 98.3 }
  ];

  const getTypeColor = (type) => {
    const colors = {
      SELECT: 'bg-blue-100 text-blue-800',
      INSERT: 'bg-green-100 text-green-800',
      UPDATE: 'bg-yellow-100 text-yellow-800',
      DELETE: 'bg-red-100 text-red-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const formatTime = (ms) => {
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Query Analyzer</h1>
          <p className="text-gray-600 mt-1">Analyze and optimize your database queries</p>
        </div>
      </div>

      {/* Query Type Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Query Type Distribution</CardTitle>
          <CardDescription>Performance breakdown by query type</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={queryTypeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" name="Query Count" />
              <Bar dataKey="avgTime" fill="#10b981" name="Avg Time (ms)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search queries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant={selectedType === 'all' ? 'default' : 'outline'}
            onClick={() => setSelectedType('all')}
          >
            All
          </Button>
          <Button
            variant={selectedType === 'SELECT' ? 'default' : 'outline'}
            onClick={() => setSelectedType('SELECT')}
          >
            SELECT
          </Button>
          <Button
            variant={selectedType === 'INSERT' ? 'default' : 'outline'}
            onClick={() => setSelectedType('INSERT')}
          >
            INSERT
          </Button>
          <Button
            variant={selectedType === 'UPDATE' ? 'default' : 'outline'}
            onClick={() => setSelectedType('UPDATE')}
          >
            UPDATE
          </Button>
        </div>
      </div>

      {/* Query List */}
      <div className="space-y-4">
        {queries.map((query) => (
          <Card key={query.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge className={getTypeColor(query.type)}>
                      {query.type}
                    </Badge>
                    <Badge variant="outline">
                      <Database className="w-3 h-3 mr-1" />
                      {query.database}
                    </Badge>
                  </div>
                  <code className="text-sm bg-gray-100 p-2 rounded block overflow-x-auto">
                    {query.query}
                  </code>
                </div>
                <Button variant="outline" size="sm">
                  <Eye className="w-4 h-4 mr-1" />
                  Analyze
                </Button>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">Avg Time</div>
                  <div className="font-semibold flex items-center">
                    <Clock className="w-4 h-4 mr-1 text-orange-500" />
                    {formatTime(query.avgTime)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Total Calls</div>
                  <div className="font-semibold flex items-center">
                    <TrendingUp className="w-4 h-4 mr-1 text-blue-500" />
                    {query.calls.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Total Time</div>
                  <div className="font-semibold">
                    {formatTime(query.totalTime)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Last Seen</div>
                  <div className="font-semibold">
                    {new Date(query.lastSeen).toLocaleTimeString()}
                  </div>
                </div>
              </div>
              
              {query.avgTime > 200 && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center text-yellow-800">
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    <span className="text-sm font-medium">Performance Warning</span>
                  </div>
                  <p className="text-sm text-yellow-700 mt-1">
                    This query has a high average execution time. Consider adding indexes or optimizing the query structure.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default QueryAnalyzer;

