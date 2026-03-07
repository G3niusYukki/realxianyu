import { api } from './index';

export const getAccounts = () => api.get('/accounts');
