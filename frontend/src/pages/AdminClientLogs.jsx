import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { getApiData, getApiList, getApiErrorMessage } from '../lib/api';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminClientLogs = () => {
  const [adminKey, setAdminKey] = useState(localStorage.getItem('adminKey') || '');
  const [level, setLevel] = useState('');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cleanupDays, setCleanupDays] = useState(30);

  const fetchLogs = async () => {
    if (!adminKey) {
      toast.error('Admin key required');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/logs/client`, {
        headers: { 'x-admin-key': adminKey },
        params: { standard: true, limit: 100, level: level || undefined },
        timeout: 10000
      });
      setLogs(getApiList(response));
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Failed to load logs'));
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanup = async () => {
    if (!adminKey) {
      toast.error('Admin key required');
      return;
    }

    try {
      const response = await axios.delete(`${API}/admin/logs/client`, {
        headers: { 'x-admin-key': adminKey },
        params: { standard: true, days: cleanupDays }
      });
      const data = getApiData(response);
      toast.success(`Deleted ${data.deleted} logs older than ${data.older_than_days} days`);
      fetchLogs();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Failed to clean logs'));
    }
  };

  useEffect(() => {
    if (adminKey) {
      fetchLogs();
    }
  }, []);

  const handleSaveKey = () => {
    localStorage.setItem('adminKey', adminKey);
    toast.success('Admin key saved');
    fetchLogs();
  };

  return (
    <div className="max-w-5xl mx-auto px-4 md:px-6 py-8">
      <div className="mb-6">
        <h1 className="playfair text-2xl md:text-3xl font-bold">Client Logs</h1>
        <p className="text-muted-foreground text-sm">Review client-side error logs.</p>
      </div>

      <div className="bg-card border border-border rounded-sm p-4 mb-6 space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          <input
            type="password"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            placeholder="Admin key"
            className="flex-1 px-3 py-2 border border-border rounded-sm"
          />
          <button
            onClick={handleSaveKey}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-sm"
          >
            Save Key
          </button>
        </div>
        <div className="flex flex-col md:flex-row gap-3 items-center">
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="px-3 py-2 border border-border rounded-sm"
          >
            <option value="">All Levels</option>
            <option value="error">Error</option>
            <option value="warn">Warn</option>
            <option value="info">Info</option>
          </select>
          <button
            onClick={fetchLogs}
            className="px-4 py-2 bg-secondary rounded-sm"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="1"
              max="365"
              value={cleanupDays}
              onChange={(e) => setCleanupDays(Number(e.target.value))}
              className="w-24 px-3 py-2 border border-border rounded-sm"
            />
            <button
              onClick={handleCleanup}
              className="px-4 py-2 border border-border rounded-sm"
            >
              Cleanup
            </button>
          </div>
        </div>
      </div>

      <div className="bg-card border border-border rounded-sm">
        {logs.length === 0 ? (
          <div className="p-6 text-muted-foreground">No logs available.</div>
        ) : (
          <div className="divide-y divide-border">
            {logs.map((log) => (
              <div key={log.id} className="p-4">
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="uppercase">{log.level || 'error'}</span>
                  <span>{log.created_at}</span>
                  {log.user_id && <span>User: {log.user_id}</span>}
                  {log.source && <span>Source: {log.source}</span>}
                </div>
                <p className="mt-2 text-sm font-medium">{log.message}</p>
                {log.url && (
                  <p className="mt-1 text-xs text-muted-foreground">{log.url}</p>
                )}
                {log.context && (
                  <pre className="mt-2 text-xs bg-secondary p-2 rounded-sm overflow-auto max-h-40">
                    {JSON.stringify(log.context, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminClientLogs;
