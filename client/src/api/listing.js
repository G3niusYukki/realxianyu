import { api } from './index';

export const getTemplates = () => api.get('/listing/templates');

export const previewListing = (data) => api.post('/listing/preview', data);

export const publishListing = (data) => api.post('/listing/publish', data);
