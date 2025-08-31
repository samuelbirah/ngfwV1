import React from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from 'recharts';
import { Paper, Typography, Box, ToggleButtonGroup, ToggleButton } from '@mui/material';
import { Timeline, BarChart as BarChartIcon } from '@mui/icons-material';

const TrafficChart = ({ data }) => {
  const [chartType, setChartType] = React.useState('line');

  // Données simulées pour la démo (à remplacer par des données réelles)
  const chartData = [
    { hour: '00:00', packets: 1200, anomalies: 12 },
    { hour: '02:00', packets: 1800, anomalies: 8 },
    { hour: '04:00', packets: 1500, anomalies: 5 },
    { hour: '06:00', packets: 2200, anomalies: 15 },
    { hour: '08:00', packets: 3500, anomalies: 25 },
    { hour: '10:00', packets: 4200, anomalies: 18 },
    { hour: '12:00', packets: 3800, anomalies: 22 },
    { hour: '14:00', packets: 3200, anomalies: 16 },
    { hour: '16:00', packets: 2800, anomalies: 14 },
    { hour: '18:00', packets: 2500, anomalies: 10 },
    { hour: '20:00', packets: 1900, anomalies: 8 },
    { hour: '22:00', packets: 1600, anomalies: 6 },
  ];

  const handleChartTypeChange = (event, newChartType) => {
    if (newChartType !== null) {
      setChartType(newChartType);
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 3, height: 400 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6" component="h2">
          Traffic Network en Temps Réel
        </Typography>
        <ToggleButtonGroup
          value={chartType}
          exclusive
          onChange={handleChartTypeChange}
          aria-label="chart type"
        >
          <ToggleButton value="line" aria-label="line chart">
            <Timeline />
          </ToggleButton>
          <ToggleButton value="bar" aria-label="bar chart">
            <BarChartIcon />
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <ResponsiveContainer width="100%" height="85%">
        {chartType === 'line' ? (
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="packets" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
            <Area type="monotone" dataKey="anomalies" stroke="#ff7300" fill="#ff7300" fillOpacity={0.3} />
          </AreaChart>
        ) : (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="packets" fill="#8884d8" />
            <Bar dataKey="anomalies" fill="#ff7300" />
          </BarChart>
        )}
      </ResponsiveContainer>
    </Paper>
  );
};

export default TrafficChart;
