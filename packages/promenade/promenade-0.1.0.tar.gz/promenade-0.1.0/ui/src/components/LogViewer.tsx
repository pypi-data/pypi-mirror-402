import { useEffect, useRef, useState, useCallback } from 'react';
import type { LogLine } from '../types';

interface LogViewerProps {
  logs: LogLine[];
  services: string[];
  connected: boolean;
  onClear: () => void;
}

export function LogViewer({ logs, services, connected, onClear }: LogViewerProps) {
  const [filter, setFilter] = useState('');
  const [serviceFilter, setServiceFilter] = useState<string>('all');
  const [isAtBottom, setIsAtBottom] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  // Check if scrolled to bottom (within 50px threshold)
  const checkIfAtBottom = useCallback(() => {
    if (!contentRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = contentRef.current;
    return scrollHeight - scrollTop - clientHeight < 50;
  }, []);

  // Handle scroll events to detect if user scrolled away from bottom
  const handleScroll = useCallback(() => {
    setIsAtBottom(checkIfAtBottom());
  }, [checkIfAtBottom]);

  // Auto-scroll to bottom when new logs arrive, if we're at the bottom
  useEffect(() => {
    if (isAtBottom && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [logs, isAtBottom]);

  // Scroll to bottom on initial load
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (serviceFilter !== 'all' && log.service !== serviceFilter) return false;
    if (filter && !log.line.toLowerCase().includes(filter.toLowerCase())) return false;
    return true;
  });

  const formatTimestamp = (ts: string) => {
    return ts.substring(11, 19);
  };

  return (
    <div className="logs-section">
      <div className="logs-header">
        <h2>
          Logs
          {!connected && <span style={{ color: 'var(--warning)' }}> (disconnected)</span>}
        </h2>
        <div className="logs-controls">
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
          >
            <option value="all">All services</option>
            {services.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Filter..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          {!isAtBottom && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                if (contentRef.current) {
                  contentRef.current.scrollTop = contentRef.current.scrollHeight;
                  setIsAtBottom(true);
                }
              }}
            >
              ↓ Jump to bottom
            </button>
          )}
          <button className="btn btn-secondary" onClick={onClear}>
            Clear
          </button>
        </div>
      </div>
      <div className="logs-content" ref={contentRef} onScroll={handleScroll}>
        {filteredLogs.map((log, i) => (
          <div key={i} className={`log-line ${log.stream}`}>
            <span className="timestamp">{formatTimestamp(log.timestamp)}</span>{' '}
            <span className="service">[{log.service}]</span>{' '}
            <span className="content">{log.line}</span>
          </div>
        ))}
        {filteredLogs.length === 0 && (
          <div style={{ color: 'var(--text-secondary)', padding: '1rem' }}>
            No logs yet...
          </div>
        )}
      </div>
    </div>
  );
}
