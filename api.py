#!/usr/bin/env python3
"""
API REST pour NGFW-Congo - Fournit les données au dashboard React
"""
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY
from fastapi import Response
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
import threading
import os
from datetime import datetime
import socket
import requests
from dotenv import load_dotenv

load_dotenv()

# Métriques Prometheus
PACKETS_PROCESSED = Counter('ngfw_packets_total', 'Total packets processed')
ANOMALIES_DETECTED = Counter('ngfw_anomalies_total', 'Total anomalies detected')
IPS_BLOCKED = Counter('ngfw_ips_blocked_total', 'Total IPs blocked')
CURRENT_BLOCKS = Gauge('ngfw_current_blocks', 'Currently blocked IPs')
FLOWS_PROCESSED = Counter('ngfw_flows_total', 'Total flows processed')

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NGFW-API")

# Configuration de la base de données
DB_DIR = "/home/biraheka/ngfw-congo/data"
DB_PATH = f"{DB_DIR}/ngfw_congo.db"

# Assurez-vous que le dossier existe
os.makedirs(DB_DIR, exist_ok=True)

def init_database():
    """Initialise la base de données SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Table des événements
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            severity TEXT,
            source_ip TEXT,
            destination_ip TEXT,
            protocol TEXT,
            description TEXT,
            anomaly_score REAL,
            action_taken TEXT
        )
        ''')
        
        # Table des statistiques
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            packets_processed INTEGER,
            flows_processed INTEGER,
            anomalies_detected INTEGER,
            ips_blocked INTEGER
        )
        ''')
        
        # Table des IP bloquées
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_ips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE,
            blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            expires_at DATETIME
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Base de données initialisée")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    logger.info("API NGFW-Congo démarrée")
    yield
    # Shutdown
    logger.info("API NGFW-Congo arrêtée")

app = FastAPI(
    title="NGFW-Congo API", 
    version="1.0.0",
    lifespan=lifespan
)

# CORS pour permettre les requêtes depuis React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestion des connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

# Routes de l'API
@app.get("/")
async def root():
    return {"message": "NGFW-Congo API", "status": "online"}

@app.get("/stats/dashboard")
async def get_dashboard_stats():
    """Retourne les statistiques pour le dashboard."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Statistiques globales
        cursor.execute('''
        SELECT 
            SUM(packets_processed) as total_packets,
            SUM(flows_processed) as total_flows,
            SUM(anomalies_detected) as total_anomalies,
            SUM(ips_blocked) as total_blocks
        FROM statistics
        WHERE timestamp > datetime('now', '-24 hours')
        ''')
        
        stats = cursor.fetchone()
        
        # Dernières anomalies
        cursor.execute('''
        SELECT * FROM events 
        WHERE event_type = 'anomaly' 
        ORDER BY timestamp DESC 
        LIMIT 10
        ''')
        
        anomalies = cursor.fetchall()
        
        # IPs actuellement bloquées
        cursor.execute('''
        SELECT ip_address, blocked_at, reason 
        FROM blocked_ips 
        WHERE expires_at > datetime('now')
        ''')
        
        blocked_ips = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_packets": stats[0] or 0,
            "total_flows": stats[1] or 0,
            "total_anomalies": stats[2] or 0,
            "total_blocks": stats[3] or 0,
            "recent_anomalies": anomalies,
            "blocked_ips": blocked_ips
        }
    except Exception as e:
        logger.error(f"Erreur dans get_dashboard_stats: {e}")
        return {"error": str(e)}

# Nouveau endpoint pour les métriques
@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type="text/plain")


@app.get("/events/recent")
async def get_recent_events(limit: int = 50):
    """Retourne les événements récents."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM events 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        events = cursor.fetchall()
        conn.close()
        
        return {"events": events}
    except Exception as e:
        logger.error(f"Erreur dans get_recent_events: {e}")
        return {"error": str(e)}

@app.websocket("/ws/real-time")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour les données en temps réel."""
    await manager.connect(websocket)
    try:
        while True:
            # Envoi périodique de données
            await asyncio.sleep(1)
            stats = await get_dashboard_stats()
            await websocket.send_json({
                "type": "real_time_update",
                "data": stats
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Fonctions pour intégration avec le NGFW
def log_event(event_type: str, data: dict):
    """Log un événement dans la base de données."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO events 
        (event_type, severity, source_ip, destination_ip, protocol, description, anomaly_score, action_taken)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_type,
            data.get('severity'),
            data.get('source_ip'),
            data.get('destination_ip'),
            data.get('protocol'),
            data.get('description'),
            data.get('anomaly_score'),
            data.get('action_taken')
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erreur dans log_event: {e}")
        return False

def update_stats(stats_data: dict):
    """Met à jour les statistiques et les métriques Prometheus."""
    try:
        # Incrémente les compteurs Prometheus
        PACKETS_PROCESSED.inc(stats_data.get('packets_processed', 0))
        FLOWS_PROCESSED.inc(stats_data.get('flows_processed', 0))
        ANOMALIES_DETECTED.inc(stats_data.get('anomalies_detected', 0))
        IPS_BLOCKED.inc(stats_data.get('ips_blocked', 0))
        
        # Met à jour la gauge des blocs actuels
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE expires_at > datetime("now")')
        current_count = cursor.fetchone()[0]
        CURRENT_BLOCKS.set(current_count)
        conn.close()
        
        # Log dans la base (existant)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO statistics 
        (packets_processed, flows_processed, anomalies_detected, ips_blocked)
        VALUES (?, ?, ?, ?)
        ''', (
            stats_data.get('packets_processed', 0),
            stats_data.get('flows_processed', 0),
            stats_data.get('anomalies_detected', 0),
            stats_data.get('ips_blocked', 0)
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erreur dans update_stats: {e}")
        return False

def format_cef_event(anomaly_data):
    """
    Format un événement en CEF (Common Event Format)
    Standard ArcSight/CrowdStrike/Splunk
    """
    cef_version = "0"
    device_vendor = "NGFW Congo"
    device_product = "Behavioral NGFW"
    device_version = "1.0"
    signature_id = f"{anomaly_data.get('signature_id', '1000')}"
    name = anomaly_data.get('event_type', 'Network Anomaly').replace("|", "_")
    severity = anomaly_data.get('severity', '5')
    
    # Extension fields
    extensions = [
        f"src={anomaly_data.get('source_ip', '0.0.0.0')}",
        f"dst={anomaly_data.get('destination_ip', '0.0.0.0')}",
        f"proto={anomaly_data.get('protocol', 'UNKNOWN')}",
        f"srcPort={anomaly_data.get('source_port', '0')}",
        f"dstPort={anomaly_data.get('destination_port', '0')}",
        f"anomalyScore={anomaly_data.get('anomaly_score', '0')}",
        f"act={anomaly_data.get('action_taken', 'logged')}",
        f"msg={anomaly_data.get('description', '').replace('=', '_')}"
    ]
    
    return f"CEF:{cef_version}|{device_vendor}|{device_product}|{device_version}|{signature_id}|{name}|{severity}|{' '.join(extensions)}"

@app.get("/integration/status")
async def get_integration_status():
    """Retourne le statut de toutes les intégrations"""
    return {
        "siem_connected": siem_exporter.socket is not None,
        "soc_webhooks": {
            "slack": bool(soc_integration.webhook_urls['slack']),
            "teams": bool(soc_integration.webhook_urls['teams']),
            "webex": bool(soc_integration.webhook_urls['webex'])
        }
    }

@app.post("/integration/soc/alert")
async def send_soc_alert(anomaly_data: dict, platform: str = "slack"):
    """Envoie une alerte au SOC"""
    success = soc_integration.send_alert(anomaly_data, platform)
    return {"status": "success" if success else "failed", "platform": platform}

@app.post("/integration/siem/test")
async def test_siem_connection(host: str, port: int = 514):
    """Teste la connexion SIEM"""
    test_exporter = SIEMExporter(host, port)
    test_exporter.connect()
    return {"connected": test_exporter.socket is not None}

@app.get("/integration/cef/events")
async def get_cef_events(limit: int = 100):
    """Retourne les événements récents au format CEF"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events ORDER BY timestamp DESC LIMIT ?', (limit,))
    events = cursor.fetchall()
    conn.close()
    
    cef_events = []
    for event in events:
        event_dict = {
            'signature_id': event[0],
            'event_type': event[2],
            'severity': '7' if 'high' in event[3].lower() else '5' if 'medium' in event[3].lower() else '3',
            'source_ip': event[4],
            'destination_ip': event[5],
            'protocol': event[6],
            'description': event[7],
            'anomaly_score': event[8],
            'action_taken': event[9]
        }
        cef_events.append(format_cef_event(event_dict))
    
    return {"cef_events": cef_events}

class SIEMExporter:
    def __init__(self, siem_host: str = "siem.company.com", siem_port: int = 514):
        self.siem_host = siem_host
        self.siem_port = siem_port
        self.socket = None
        
    def connect(self):
        """Établit la connexion Syslog"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # self.socket.connect((self.siem_host, self.siem_port))  # Pour TCP
            logger.info(f"Connected to SIEM at {self.siem_host}:{self.siem_port}")
        except Exception as e:
            logger.error(f"SIEM connection failed: {e}")
            
    def send_cef(self, cef_message: str):
        """Envoie un message CEF via Syslog"""
        if not self.socket:
            self.connect()
            
        try:
            # Format Syslog avec header CEF
            timestamp = datetime.now().strftime("%b %d %H:%M:%S")
            hostname = socket.gethostname()
            syslog_message = f"<134>{timestamp} {hostname} {cef_message}"
            
            self.socket.sendto(syslog_message.encode(), (self.siem_host, self.siem_port))
            logger.info(f"SIEM event sent: {cef_message[:100]}...")
            
        except Exception as e:
            logger.error(f"SIEM send failed: {e}")
            self.socket = None  # Force reconnect next time

class SOCIntegration:
    def __init__(self):
        self.webhook_urls = {
            'slack': os.getenv('SLACK_WEBHOOK_URL', ''),
            'teams': os.getenv('TEAMS_WEBHOOK_URL', ''),
            'webex': os.getenv('WEBEX_WEBHOOK_URL', '')
        }
    
    def send_alert(self, anomaly_data: dict, platform: str = 'slack'):
        """Envoie une alerte au SOC"""
        webhook_url = self.webhook_urls.get(platform)
        if not webhook_url:
            return False
            
        payload = self._format_payload(anomaly_data, platform)
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SOC alert failed: {e}")
            return False
    
    def _format_payload(self, anomaly_data: dict, platform: str):
        """Formate le payload selon la plateforme"""
        if platform == 'slack':
            return {
                "text": "🚨 NGFW Alert",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 NGFW Congo Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Source:* {anomaly_data.get('source_ip')}"},
                            {"type": "mrkdwn", "text": f"*Destination:* {anomaly_data.get('destination_ip')}"},
                            {"type": "mrkdwn", "text": f"*Protocol:* {anomaly_data.get('protocol')}"},
                            {"type": "mrkdwn", "text": f"*Score:* {anomaly_data.get('anomaly_score')}"}
                        ]
                    }
                ]
            }
        
        elif platform == 'teams':
            return {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "FF0000",
                "summary": "NGFW Alert",
                "sections": [{
                    "activityTitle": "🚨 NGFW Congo Alert",
                    "facts": [
                        {"name": "Source IP:", "value": anomaly_data.get('source_ip')},
                        {"name": "Destination IP:", "value": anomaly_data.get('destination_ip')},
                        {"name": "Anomaly Score:", "value": str(anomaly_data.get('anomaly_score'))}
                    ]
                }]
            }

# Instance globale
soc_integration = SOCIntegration()

# Instance globale
siem_exporter = SIEMExporter(os.getenv('SIEM_HOST', 'localhost'),int(os.getenv('SIEM_PORT','514')))

@app.post("/integration/siem/send")
async def send_to_siem(anomaly_data: dict):
    """Endpoint pour envoyer des événements au SIEM"""
    cef_message = format_cef_event(anomaly_data)
    siem_exporter.send_cef(cef_message)
    return {"status": "sent", "cef_message": cef_message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
