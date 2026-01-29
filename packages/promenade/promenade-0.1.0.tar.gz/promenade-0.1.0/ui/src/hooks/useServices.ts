import { useState, useEffect, useCallback } from 'react';
import type { StatusResponse, Service } from '../types';

const API_BASE = '/api';

export function useServices(pollInterval = 2000) {
  const [services, setServices] = useState<Record<string, Service>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/status`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: StatusResponse = await response.json();
      setServices(data.services);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, pollInterval);
    return () => clearInterval(interval);
  }, [fetchStatus, pollInterval]);

  const startService = async (name: string) => {
    await fetch(`${API_BASE}/services/${name}/start`, { method: 'POST' });
    await fetchStatus();
  };

  const stopService = async (name: string) => {
    await fetch(`${API_BASE}/services/${name}/stop`, { method: 'POST' });
    await fetchStatus();
  };

  const restartService = async (name: string) => {
    await fetch(`${API_BASE}/services/${name}/restart`, { method: 'POST' });
    await fetchStatus();
  };

  const restartAll = async () => {
    for (const name of Object.keys(services)) {
      await fetch(`${API_BASE}/services/${name}/restart`, { method: 'POST' });
    }
    await fetchStatus();
  };

  return {
    services,
    loading,
    error,
    startService,
    stopService,
    restartService,
    restartAll,
    refresh: fetchStatus,
  };
}
