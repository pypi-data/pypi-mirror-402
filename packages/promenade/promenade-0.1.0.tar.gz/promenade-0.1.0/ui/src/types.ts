export interface Service {
  name: string;
  status: 'pending' | 'starting' | 'running' | 'stopping' | 'stopped' | 'failed' | 'retrying' | 'gave_up';
  health: 'unknown' | 'waiting' | 'healthy' | 'unhealthy';
  pid: number | null;
  port: number | null;
  hostname: string | null;
  url: string | null;
  uptime_seconds: number | null;
  restart_count: number;
  last_exit_code: number | null;
  command: string;
}

export interface StatusResponse {
  services: Record<string, Service>;
  config_path: string;
  config_last_modified: string;
  manager_uptime_seconds: number | null;
}

export interface LogLine {
  timestamp: string;
  service: string;
  stream: 'stdout' | 'stderr';
  line: string;
}
