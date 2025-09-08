import axios from 'axios';

// Utilisez localhost ou votre IP correcte
const API_BASE_URL = 'http://localhost:8000'; // ou 'http://192.168.x.x:8000'

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
  createWebSocket: () => new WebSocket(`ws://localhost:8000/ws/real-time`),
  
  // Actions de gestion (vous devez ajouter ces endpoints à votre API Python)
  blockIP: (ip, reason) => api.post('/admin/block-ip', { ip, reason }),
  unblockIP: (ip) => api.post('/admin/unblock-ip', { ip }),
  
  // Nouveau: Récupérer les métriques Prometheus
  getMetrics: () => api.get('/metrics'),
};

export default api;