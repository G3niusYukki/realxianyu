import { api } from './index';

export const getSystemConfig = () => api.get('/config');

export const saveSystemConfig = (updates) => api.put('/config', updates);

export const getConfigSections = () => api.get('/config/sections');
