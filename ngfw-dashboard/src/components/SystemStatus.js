import React from 'react';
import {
  Paper,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Memory,
  Storage,
  NetworkCheck,
  Security,
  Speed,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';

const SystemStatus = ({ stats }) => {
  const systemMetrics = [
    {
      icon: <Memory />,
      label: 'Utilisation CPU',
      value: '23%',
      status: 'success',
      color: '#4caf50',
    },
    {
      icon: <Storage />,
      label: 'Utilisation Mémoire',
      value: '45%',
      status: 'success',
      color: '#4caf50',
    },
    {
      icon: <NetworkCheck />,
      label: 'Bande passante',
      value: '1.2 Gbps',
      status: 'warning',
      color: '#ff9800',
    },
    {
      icon: <Security />,
      label: 'Règles actives',
      value: '142',
      status: 'success',
      color: '#4caf50',
    },
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle color="success" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'error':
        return <Error color="error" />;
      default:
        return <CheckCircle />;
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 3, height: 400 }}>
      <Box display="flex" alignItems="center" mb={2}>
        <Speed sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" component="h2">
          Status Système
        </Typography>
        <Chip
          label="Online"
          color="success"
          variant="filled"
          size="small"
          sx={{ ml: 2 }}
        />
      </Box>

      <List dense>
        {systemMetrics.map((metric, index) => (
          <React.Fragment key={index}>
            <ListItem>
              <ListItemIcon>{metric.icon}</ListItemIcon>
              <ListItemText
                primary={metric.label}
                secondary={
                  <Box display="flex" alignItems="center">
                    <LinearProgress
                      variant="determinate"
                      value={metric.label.includes('Utilisation') ? parseInt(metric.value) : 0}
                      sx={{
                        width: 60,
                        mr: 2,
                        backgroundColor: '#e0e0e0',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: metric.color,
                        },
                      }}
                    />
                    {metric.value}
                  </Box>
                }
              />
              <Box ml={2}>
                {getStatusIcon(metric.status)}
              </Box>
            </ListItem>
            {index < systemMetrics.length - 1 && <Divider variant="inset" component="li" />}
          </React.Fragment>
        ))}
      </List>

      <Box mt={3} p={2} bgcolor="#f5f5f5" borderRadius={1}>
        <Typography variant="subtitle2" gutterBottom>
          Performances NGFW
        </Typography>
        <Box display="flex" justifyContent="space-between" mt={1}>
          <Box textAlign="center">
            <Typography variant="h6" color="primary">
              {((stats.total_anomalies / Math.max(stats.total_flows, 1)) * 100).toFixed(2)}%
            </Typography>
            <Typography variant="caption">Taux de détection</Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="h6" color="primary">
              {stats.total_packets > 1000 ? `${(stats.total_packets / 1000).toFixed(1)}K` : stats.total_packets}
            </Typography>
            <Typography variant="caption">Paquets/min</Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="h6" color="primary">
              {"<5ms"}
            </Typography>
            <Typography variant="caption">Latence</Typography>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
};

export default SystemStatus;
