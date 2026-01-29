import { useState, useEffect, useRef, useCallback } from 'react';
import type { LogLine } from '../types';

const WS_URL = `ws://${window.location.host}/api/logs/stream`;
const MAX_LOGS = 500;

export function useLogStream(serviceFilter?: string) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const url = serviceFilter ? `${WS_URL}?services=${serviceFilter}` : WS_URL;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const line: LogLine = JSON.parse(event.data);
      setLogs((prev) => {
        const newLogs = [...prev, line];
        // Keep only last MAX_LOGS entries
        if (newLogs.length > MAX_LOGS) {
          return newLogs.slice(-MAX_LOGS);
        }
        return newLogs;
      });
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect after a delay
      setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [serviceFilter]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return { logs, connected, clearLogs };
}
