#!/usr/bin/env python3
"""
Script Principal NGFW-Congo - Orchestre capture, extraction et détection.
"""
# CONFIGURATION DU LOGGING - DOIT ÊTRE LA PREMIÈRE CHOSE
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ngfw_congo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('NGFW-Main')
logger.info("🛠️ DEBUT DE L'IMPORT DES MODULES")  


import time
import json
from scapy.all import sniff
from feature_extractor import packet_to_features, FlowGenerator
from detector import init_detector, detect_anomaly
from blocker import init_blocker
import logging
import threading
from queue import Queue
from api import log_event, update_stats

# File d'attente pour passer les features du thread de capture au thread de détection
features_queue = Queue(maxsize=1000)

# Compteurs pour les statistiques
stats = {
    'packets_captured': 0,
    'flows_processed': 0,
    'anomalies_detected': 0,
    'start_time': time.time()
}

def packet_handler(packet):
    """
    Callback appelé par Scapy pour chaque paquet capturé.
    """
    stats['packets_captured'] += 1
    
    try:
        # Traite le paquet et obtient les features des flux expirés
        expired_flows = packet_to_features(packet)
        
        if expired_flows:
            for flow_features in expired_flows:
                # Met en file d'attente pour le traitement par le détecteur
                features_queue.put(flow_features)
                
    except Exception as e:
        logger.error(f"Erreur dans packet_handler: {e}")

def detection_worker():
    """
    Worker qui traite les features des flux depuis la file d'attente.
    """
    logger.info("Thread de détection démarré.")
    
    while True:
        try:
            # Attend un flux à traiter
            flow_features = features_queue.get()
            
            if flow_features is None:  # Signal d'arrêt
                break
                
            # DEBUG: Afficher périodiquement les flux traités
            if stats['flows_processed'] % 5 == 0:  # Log tous les 5 flux
                logger.info(f"📋 Flux traité: {json.dumps(flow_features, indent=2)}")
            
            # Fait la prédiction avec le modèle IA
            detection_result = detect_anomaly(flow_features)
            
            stats['flows_processed'] += 1
            
            # Log les résultats si anomalie détectée
            if detection_result.get('is_anomaly', False):
                stats['anomalies_detected'] += 1
                logger.warning(f"🚨 ANOMALIE DÉTECTÉE! Score: {detection_result['anomaly_score']:.3f}")
                # Log dans la base de données
                log_event("anomaly", {
                    "severity": "high",
                    "source_ip": flow_features.get('Src IP'),
                    "destination_ip": flow_features.get('Dst IP'),
                    "protocol": flow_features.get('Protocol'),
                    "description": "Anomalie réseau détectée",
                    "anomaly_score": detection_result['anomaly_score'],
                    "action_taken": "blocked" if 'Src IP' in flow_features else "logged"
                })
                # BLOQUAGE AUTOMATIQUE de l'IP source
                if 'Src IP' in flow_features:
                    src_ip = flow_features['Src IP']
                    # Importation locale pour éviter les dépendances circulaires
                    from blocker import blocker
                    blocker.block_ip(src_ip, f"Anomalie détectée (score: {detection_result['anomaly_score']:.3f})")
                
                logger.warning(f"   Détails du flux: {json.dumps(flow_features, indent=2)}")
                logger.warning(f"   Résultat complet: {json.dumps(detection_result, indent=2)}")
                
            # Log périodique des statistiques
            if stats['flows_processed'] % 10 == 0:  # Log tous les 10 flux
                log_stats()
                
            features_queue.task_done()
            
        except Exception as e:
            logger.error(f"Erreur dans detection_worker: {e}")

def log_stats():
    """
    Log les statistiques courantes du système.
    """
    uptime = time.time() - stats['start_time']
    hours, rem = divmod(uptime, 3600)
    minutes, seconds = divmod(rem, 60)
    
    logger.info(f"📊 STATS - Uptime: {int(hours)}h{int(minutes)}m{int(seconds)}s | "
                f"Paquets: {stats['packets_captured']} | "
                f"Flux: {stats['flows_processed']} | "
                f"Anomalies: {stats['anomalies_detected']}")

def main():
    """
    Fonction principale.
    """
    logger.info("🚀 Démarrage de NGFW-Congo...")
    
    # Initialisation du détecteur
    try:
        detector = init_detector()
        logger.info("Détecteur initialisé avec succès.")
    except Exception as e:
        logger.error(f"Échec de l'initialisation du détecteur: {e}")
        return
    
    # Initialisation du bloqueur
    try:
        blocker = init_blocker()
        logger.info("Bloqueur initialisé avec succès.")
    except Exception as e:
        logger.error(f"Échec de l'initialisation du bloqueur: {e}")
        return
    
    # Démarrage du thread de détection
    detection_thread = threading.Thread(target=detection_worker, daemon=True)
    detection_thread.start()
    logger.info("Thread de détection démarré.")
    
    # Configuration de la capture
    interface = "enp0s3"  # Remplacez par votre interface réseau
    logger.info(f"Démarrage de la capture sur l'interface {interface}...")
    
    try:
        # Capture en continu (appelle packet_handler pour chaque paquet)
        sniff(iface=interface, prn=packet_handler, store=0)
        
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur.")
    except PermissionError:
        logger.error("Permissions insuffisantes. Lancez avec sudo.")
    except Exception as e:
        logger.error(f"Erreur de capture: {e}")
    finally:
        # Nettoyage
        logger.info("Nettoyage et arrêt...")
        features_queue.put(None)  # Signal d'arrêt pour le thread
        detection_thread.join(timeout=5)
        log_stats()
        logger.info("NGFW-Congo arrêté.")

if __name__ == "__main__":
    # Vérification des privilèges
    import os
    if os.geteuid() != 0:
        print("❌ Erreur: Ce script doit être exécuté avec sudo (pour la capture réseau)")
        exit(1)
    
    main()
