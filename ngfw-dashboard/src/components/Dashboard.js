import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Security,
  NetworkCheck,
  Warning,
  Block,
  Refresh,
} from '@mui/icons-material';
import { ngfwAPI } from '../services/api';
import TrafficChart from './TrafficChart';
import AlertsTable from './AlertsTable';
import BlockedIPs from './BlockedIPs';
import SystemStatus from './SystemStatus';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_packets: 0,
    total_flows: 0,
    total_anomalies: 0,
    total_blocks: 0,
    recent_anomalies: [],
    blocked_ips: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await ngfwAPI.getDashboardStats();
      setStats(response.data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError('Erreur de connexion à l\'API');
      console.error('API Error:', err);
    } finally {
      setError(null);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // Configuration du WebSocket pour les mises à jour temps réel
    const ws = ngfwAPI.createWebSocket();
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'real_time_update') {
        setStats(data.data);
        setLastUpdate(new Date());
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    return () => {
      ws.close();
    };
  }, [fetchData]);

  const StatCard = ({ icon, title, value, color, subtitle }) => (
    <Card className="stat-card" sx={{ bgcolor: color }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          {icon}
          <Typography variant="h6" component="div" ml={1}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" component="div" className="stat-value">
          {value.toLocaleString()}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress size={60} />
        <Typography variant="h6" ml={2}>
          Chargement du dashboard...
        </Typography>
      </Box>
    );
  }

  return (
    <Box className="dashboard-container">
      {/* Header */}
      <Paper elevation={3} className="dashboard-header">
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center">
            <Security sx={{ fontSize: 40, mr: 2 }} />
            <Box>
              <Typography variant="h4" component="h1" fontWeight="bold">
                NGFW Congo Dashboard
              </Typography>
              <Typography variant="subtitle1" color="text.secondary">
                Surveillance réseau en temps réel
              </Typography>
            </Box>
          </Box>
          <Box display="flex" alignItems="center">
            <Chip
              icon={<Refresh />}
              label={`Mis à jour: ${lastUpdate.toLocaleTimeString()}`}
              variant="outlined"
              onClick={fetchData}
            />
            <Chip
              label="Système Actif"
              color="success"
              variant="filled"
              sx={{ ml: 1 }}
            />
          </Box>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={<NetworkCheck sx={{ fontSize: 30 }} />}
            title="Paquets Traités"
            value={stats.total_packets}
            color="#e3f2fd"
            subtitle="24 dernières heures"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={<NetworkCheck sx={{ fontSize: 30 }} />}
            title="Flux Analysés"
            value={stats.total_flows}
            color="#e8f5e8"
            subtitle="24 dernières heures"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={<Warning sx={{ fontSize: 30 }} />}
            title="Anomalies"
            value={stats.total_anomalies}
            color="#ffebee"
            subtitle="24 dernières heures"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={<Block sx={{ fontSize: 30 }} />}
            title="IP Bloquées"
            value={stats.total_blocks}
            color="#fbe9e7"
            subtitle="Actuellement"
          />
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Graphiques */}
        <Grid item xs={12} lg={8}>
          <TrafficChart data={stats} />
        </Grid>

        {/* Status système */}
        <Grid item xs={12} lg={4}>
          <SystemStatus stats={stats} />
        </Grid>

        {/* Alertes récentes */}
        <Grid item xs={12} lg={6}>
          <AlertsTable anomalies={stats.recent_anomalies} />
        </Grid>

        {/* IP bloquées */}
        <Grid item xs={12} lg={6}>
          <BlockedIPs blockedIPs={stats.blocked_ips} onUnblock={fetchData} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
