import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
} from '@mui/material';
import {
  Block,
  LockOpen,
  AccessTime,
  Info,
  Delete,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { ngfwAPI } from '../services/api';

const BlockedIPs = ({ blockedIPs, onUnblock }) => {
  const [selectedIP, setSelectedIP] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleUnblock = async (ip) => {
    setLoading(true);
    try {
      await ngfwAPI.unblockIP(ip);
      setMessage(`IP ${ip} débloquée avec succès`);
      onUnblock();
      setDialogOpen(false);
    } catch (error) {
      setMessage(`Erreur lors du déblocage de ${ip}`);
      console.error('Unblock error:', error);
    }
    setLoading(false);
  };

  const columns = [
    {
      field: 'ip_address',
      headerName: 'Adresse IP',
      width: 150,
      renderCell: (params) => (
        <Chip
          icon={<Block color="error" />}
          label={params.value}
          color="error"
          variant="filled"
        />
      ),
    },
    {
      field: 'blocked_at',
      headerName: 'Bloquée à',
      width: 160,
      valueFormatter: (params) => new Date(params.value).toLocaleString(),
    },
    {
      field: 'reason',
      headerName: 'Raison',
      width: 200,
      renderCell: (params) => (
        <Tooltip title={params.value}>
          <Box
            sx={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: 200,
            }}
          >
            <Info sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
            {params.value}
          </Box>
        </Tooltip>
      ),
    },
    {
      field: 'expires_at',
      headerName: 'Expire à',
      width: 160,
      valueFormatter: (params) => new Date(params.value).toLocaleString(),
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          <AccessTime sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
          {new Date(params.value).toLocaleTimeString()}
        </Box>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      sortable: false,
      renderCell: (params) => (
        <Tooltip title="Débloquer cette IP">
          <IconButton
            size="small"
            onClick={() => {
              setSelectedIP(params.row.ip_address);
              setDialogOpen(true);
            }}
          >
            <LockOpen color="primary" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  const rows = blockedIPs.map((ip, index) => ({
    id: index,
    ...ip,
  }));

  return (
    <>
      <Paper elevation={2} sx={{ p: 3, height: 400 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <Block sx={{ mr: 1, color: 'error.main' }} />
          <Typography variant="h6" component="h2">
            IP Bloquées
          </Typography>
          <Chip
            icon={<Block />}
            label={`${blockedIPs.length} IP(s) bloquée(s)`}
            color="error"
            variant="outlined"
            size="small"
            sx={{ ml: 2 }}
          />
        </Box>

        {message && (
          <Alert severity={message.includes('Erreur') ? 'error' : 'success'} sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}

        <DataGrid
          rows={rows}
          columns={columns}
          pageSize={5}
          rowsPerPageOptions={[5]}
          sx={{
            border: 'none',
            '& .MuiDataGrid-cell': {
              borderBottom: '1px solid #e0e0e0',
            },
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: '#ffebee',
            },
          }}
        />
      </Paper>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Débloquer l'IP</DialogTitle>
        <DialogContent>
          <Typography>
            Êtes-vous sûr de vouloir débloquer l'IP {selectedIP} ?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button
            onClick={() => handleUnblock(selectedIP)}
            color="primary"
            disabled={loading}
            startIcon={<Delete />}
          >
            {loading ? 'Déblocage...' : 'Débloquer'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default BlockedIPs;
