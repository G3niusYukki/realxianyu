import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/index';

const POLL_INTERVAL = 60_000;

const EMPTY = {
  loading: true,
  lastChecked: null,
  node:   { ok: false, message: '检查中...' },
  python: { ok: false, message: '检查中...' },
  cookie: { ok: false, message: '检查中...' },
  ai:     { ok: false, message: '检查中...' },
  xgj:    { ok: false, message: '检查中...' },
};

export default function useHealthCheck(enabled = true) {
  const [health, setHealth] = useState(EMPTY);
  const timerRef = useRef(null);
  const mountedRef = useRef(true);

  const check = useCallback(async () => {
    const next = { loading: false, lastChecked: new Date().toISOString() };

    try {
      const res = await api.get('/health/check');
      const d = res.data;
      next.node   = d.node   || { ok: true, message: '运行中' };
      next.python = d.services?.python || { ok: true, message: '运行中' };
      next.xgj    = d.xgj    || { ok: false, message: '未检查' };
      next.cookie  = d.cookie || { ok: false, message: '未知' };
      next.ai      = d.ai     || { ok: false, message: '未知' };
    } catch {
      next.node   = { ok: false, message: '不可达' };
      next.python = { ok: false, message: '不可达' };
      next.xgj    = { ok: false, message: '未知' };
      next.cookie = { ok: false, message: '后端不可达' };
      next.ai     = { ok: false, message: '后端不可达' };
    }

    if (mountedRef.current) setHealth(next);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (!enabled) return;
    check();
    timerRef.current = setInterval(check, POLL_INTERVAL);
    return () => {
      mountedRef.current = false;
      clearInterval(timerRef.current);
    };
  }, [enabled, check]);

  return { ...health, refresh: check };
}
