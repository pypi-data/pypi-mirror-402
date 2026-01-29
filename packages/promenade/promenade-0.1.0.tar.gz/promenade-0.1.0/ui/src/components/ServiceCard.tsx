import type { Service } from '../types';

interface ServiceCardProps {
  service: Service;
  onStart: () => void;
  onStop: () => void;
  onRestart: () => void;
}

export function ServiceCard({ service, onStart, onStop, onRestart }: ServiceCardProps) {
  const isRunning = service.status === 'running';
  const isStopped = ['stopped', 'failed', 'gave_up', 'pending'].includes(service.status);
  const isTransitioning = ['starting', 'stopping', 'retrying'].includes(service.status);

  const formatUptime = (seconds: number | null) => {
    if (seconds === null) return null;
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <div className="service-card">
      <div className="service-header">
        <div className="service-name">
          <span className={`status-dot ${service.status}`} />
          <h3>{service.name}</h3>
        </div>
        <div>
          <span className={`service-status ${service.status}`}>
            {service.status}
          </span>
          {service.health !== 'unknown' && (
            <span className={`service-status ${service.health}`}>
              {' '}({service.health})
            </span>
          )}
        </div>
      </div>

      <div className="service-details">
        <div><code>{service.command}</code></div>
        {service.pid && <div>PID: {service.pid}</div>}
        {service.uptime_seconds !== null && (
          <div>Uptime: {formatUptime(service.uptime_seconds)}</div>
        )}
        {service.restart_count > 0 && (
          <div>Restarts: {service.restart_count}</div>
        )}
      </div>

      {service.url && (
        <div className="service-url">
          <a href={service.url} target="_blank" rel="noopener noreferrer">
            {service.url} ↗
          </a>
        </div>
      )}

      <div className="service-actions">
        {isStopped && (
          <button className="btn btn-success" onClick={onStart} disabled={isTransitioning}>
            ▶ Start
          </button>
        )}
        {isRunning && (
          <>
            <button className="btn btn-secondary" onClick={onRestart} disabled={isTransitioning}>
              ⟳ Restart
            </button>
            <button className="btn btn-danger" onClick={onStop} disabled={isTransitioning}>
              ■ Stop
            </button>
          </>
        )}
        {isTransitioning && (
          <span className="service-status">{service.status}...</span>
        )}
      </div>
    </div>
  );
}
