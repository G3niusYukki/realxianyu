import { api } from './index';

export const getSystemStatus = () => api.get('/status');

export const getDashboardSummary = () => api.get('/summary');

export const getTrendData = (metric, days = 30) =>
  api.get(`/trend?metric=${metric}&days=${days}`);

export const getTopProducts = (limit = 12) =>
  api.get(`/top-products?limit=${limit}`);

export const getRecentOperations = (limit = 20) =>
  api.get(`/recent-operations?limit=${limit}`);

export const serviceControl = (action) =>
  api.post('/service/control', { action });

export const moduleControl = (action, target) =>
  api.post('/module/control', { action, target });
