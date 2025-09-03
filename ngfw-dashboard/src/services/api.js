import axios from 'axios';

const API_BASE_URL = 'http://192.168.218.200:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const ngfwAPI = {
  // Statistiques du dashboard
  getDashboardStats: () => api.get('/stats/dashboard'),
  
  // Événements récents
  getRecentEvents: (limit = 50) => api.get(`/events/recent?limit=${limit}`),
  
  // WebSocket pour les mises à jour temps réel
  createWebSocket: () => new WebSocket(`ws://192.168.49.200:8000/ws/real-time`),
  
  // Actions de gestion
  blockIP: (ip, reason) => api.post('/admin/block-ip', { ip, reason }),
  unblockIP: (ip) => api.post('/admin/unblock-ip', { ip }),
};

export default api;
