import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  DataGrid,
  gridClasses,
  gridPageCountSelector,
  gridPageSelector,
  useGridApiContext,
  useGridSelector,
} from '@mui/x-data-grid';
import {
  Warning,
  Error,
  Info,
  Block,
  Visibility,
} from '@mui/icons-material';
import { Pagination } from '@mui/material';

function CustomPagination() {
  const apiRef = useGridApiContext();
  const page = useGridSelector(apiRef, gridPageSelector);
  const pageCount = useGridSelector(apiRef, gridPageCountSelector);

  return (
    <Pagination
      color="primary"
      count={pageCount}
      page={page + 1}
      onChange={(event, value) => apiRef.current.setPage(value - 1)}
    />
  );
}

const AlertsTable = ({ anomalies }) => {
  const getSeverityIcon = (score) => {
    if (score > 0.7) return <Error color="error" />;
    if (score > 0.4) return <Warning color="warning" />;
    return <Info color="info" />;
  };

  const getSeverityColor = (score) => {
    if (score > 0.7) return 'error';
    if (score > 0.4) return 'warning';
    return 'info';
  };

  const columns = [
    {
      field: 'severity',
      headerName: 'Sévérité',
      width: 120,
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          {getSeverityIcon(params.row.anomaly_score)}
          <Chip
            label={params.row.anomaly_score > 0.7 ? 'Haute' : params.row.anomaly_score > 0.4 ? 'Moyenne' : 'Basse'}
            color={getSeverityColor(params.row.anomaly_score)}
            size="small"
            sx={{ ml: 1 }}
          />
        </Box>
      ),
    },
    {
      field: 'timestamp',
      headerName: 'Heure',
      width: 160,
      valueFormatter: (params) => new Date(params.value).toLocaleTimeString(),
    },
    {
      field: 'source_ip',
      headerName: 'IP Source',
      width: 130,
      renderCell: (params) => (
        <Chip
          label={params.value}
          variant="outlined"
          size="small"
        />
      ),
    },
    {
      field: 'destination_ip',
      headerName: 'IP Destination',
      width: 150,
      renderCell: (params) => (
        <Chip
          label={params.value}
          variant="outlined"
          size="small"
          color="primary"
        />
      ),
    },
    {
      field: 'protocol',
      headerName: 'Protocole',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value}
          variant="filled"
          size="small"
          color="secondary"
        />
      ),
    },
    {
      field: 'anomaly_score',
      headerName: 'Score',
      width: 100,
      renderCell: (params) => (
        <Box
          sx={{
            bgcolor: params.value > 0.7 ? '#ffebee' : params.value > 0.4 ? '#fff3e0' : '#e3f2fd',
            px: 1,
            py: 0.5,
            borderRadius: 1,
            fontWeight: 'bold',
            color: params.value > 0.7 ? '#c62828' : params.value > 0.4 ? '#f57c00' : '#1976d2',
          }}
        >
          {params.value.toFixed(3)}
        </Box>
      ),
    },
    {
      field: 'action_taken',
      headerName: 'Action',
      width: 120,
      renderCell: (params) => (
        <Chip
          icon={<Block />}
          label={params.value === 'blocked' ? 'Bloqué' : 'Loggé'}
          color={params.value === 'blocked' ? 'error' : 'default'}
          variant="filled"
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 80,
      sortable: false,
      renderCell: (params) => (
        <Tooltip title="Voir les détails">
          <IconButton size="small">
            <Visibility />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  const rows = anomalies.map((anomaly, index) => ({
    id: index,
    ...anomaly,
  }));

  return (
    <Paper elevation={2} sx={{ p: 3, height: 400 }}>
      <Box display="flex" alignItems="center" mb={2}>
        <Warning sx={{ mr: 1, color: 'warning.main' }} />
        <Typography variant="h6" component="h2">
          Alertes Récentes
        </Typography>
        <Chip
          label={`${anomalies.length} alertes`}
          color="primary"
          variant="outlined"
          size="small"
          sx={{ ml: 2 }}
        />
      </Box>

      <DataGrid
        rows={rows}
        columns={columns}
        pageSize={5}
        rowsPerPageOptions={[5]}
        components={{
          Pagination: CustomPagination,
        }}
        sx={{
          border: 'none',
          [`& .${gridClasses.cell}`]: {
            borderBottom: '1px solid #e0e0e0',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: '#f5f5f5',
          },
        }}
      />
    </Paper>
  );
};

export default AlertsTable;
