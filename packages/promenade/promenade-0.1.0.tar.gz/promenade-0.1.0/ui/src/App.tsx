import { useServices } from './hooks/useServices';
import { useLogStream } from './hooks/useLogStream';
import { ServiceCard } from './components/ServiceCard';
import { LogViewer } from './components/LogViewer';

function App() {
  const {
    services,
    loading,
    error,
    startService,
    stopService,
    restartService,
    restartAll,
  } = useServices();

  const { logs, connected, clearLogs } = useLogStream();

  const serviceList = Object.values(services);
  const serviceNames = Object.keys(services);

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="header">
          <h1>Promenade</h1>
        </div>
        <div className="main">
          <div className="error">
            Error connecting to Promenade: {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="header">
        <h1>Promenade</h1>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={restartAll}>
            ⟳ Restart All
          </button>
        </div>
      </div>

      <div className="main">
        <div className="services-grid">
          {serviceList.map((service) => (
            <ServiceCard
              key={service.name}
              service={service}
              onStart={() => startService(service.name)}
              onStop={() => stopService(service.name)}
              onRestart={() => restartService(service.name)}
            />
          ))}
        </div>

        <LogViewer
          logs={logs}
          services={serviceNames}
          connected={connected}
          onClear={clearLogs}
        />
      </div>
    </div>
  );
}

export default App;
