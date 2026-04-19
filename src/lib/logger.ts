type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LEVEL_ORDER: Record<LogLevel, number> = { debug: 0, info: 1, warn: 2, error: 3 };

function getMinLevel(): LogLevel {
  const fromEnv = (process.env.LOG_LEVEL as LogLevel | undefined) ?? 'info';
  return LEVEL_ORDER[fromEnv] !== undefined ? fromEnv : 'info';
}

function shouldLog(level: LogLevel): boolean {
  return LEVEL_ORDER[level] >= LEVEL_ORDER[getMinLevel()];
}

function write(level: LogLevel, message: string, meta?: Record<string, unknown>): void {
  if (!shouldLog(level)) return;
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...(meta ?? {}),
  };
  // Structured JSON — pipe to any log aggregator
  // eslint-disable-next-line no-console
  console[level === 'debug' ? 'log' : level](JSON.stringify(entry));
}

export const logger = {
  debug: (msg: string, meta?: Record<string, unknown>): void => write('debug', msg, meta),
  info: (msg: string, meta?: Record<string, unknown>): void => write('info', msg, meta),
  warn: (msg: string, meta?: Record<string, unknown>): void => write('warn', msg, meta),
  error: (msg: string, meta?: Record<string, unknown>): void => write('error', msg, meta),
};
