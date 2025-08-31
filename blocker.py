#!/usr/bin/env python3
"""
Module de Blocage Actif pour NGFW-Congo.
Utilise nftables pour bloquer dynamiquement les IP malveillantes.
"""

import subprocess
import threading
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('NGFW-Blocker')

class IPBlocker:
    def __init__(self):
        self.blocked_ips = {}  # {ip: (timestamp, reason)}
        self.lock = threading.Lock()
        self.initialize_nftables()
        
    def initialize_nftables(self):
        """Initialise la table et chaîne nftables pour NGFW-Congo."""
        try:
            # Création de la table et chaîne nftables dédiées
            subprocess.run([
                'sudo', 'nft', 'add', 'table', 'ip', 'ngfw_congo'
            ], check=True, capture_output=True)
            
            subprocess.run([
                'sudo', 'nft', 'add', 'chain', 'ip', 'ngfw_congo', 'block_chain', 
                '{ type filter hook input priority 0; policy accept; }'
            ], check=True, capture_output=True)
            
            logger.info("Table et chaîne nftables initialisées.")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"nftables déjà configuré ou erreur: {e.stderr.decode()}")
    
    def block_ip(self, ip_address, reason="Anomalie détectée", duration_minutes=60):
        """
        Bloque une IP avec nftables pour une durée spécifiée.
        """
        if self.is_private_ip(ip_address):
            logger.warning(f"Tentative de blocage d'IP privée ignorée: {ip_address}")
            return False
            
        with self.lock:
            if ip_address in self.blocked_ips:
                # IP déjà bloquée, on met à jour le timestamp
                self.blocked_ips[ip_address] = (datetime.now(), reason)
                return True
                
            try:
                # Ajoute la règle de blocage
                subprocess.run([
                    'sudo', 'nft', 'add', 'rule', 'ip', 'ngfw_congo', 'block_chain',
                    'ip', 'saddr', ip_address, 'counter', 'drop'
                ], check=True, capture_output=True)
                
                self.blocked_ips[ip_address] = (datetime.now(), reason)
                logger.warning(f"🚫 IP BLOQUÉE: {ip_address} - Raison: {reason}")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Erreur lors du blocage de {ip_address}: {e.stderr.decode()}")
                return False
    
    def unblock_ip(self, ip_address):
        """Débloque une IP."""
        with self.lock:
            if ip_address in self.blocked_ips:
                try:
                    # Trouve et supprime la règle correspondante
                    result = subprocess.run([
                        'sudo', 'nft', 'list', 'ruleset'
                    ], capture_output=True, text=True)
                    
                    rules = result.stdout.split('\n')
                    for i, rule in enumerate(rules):
                        if ip_address in rule and 'drop' in rule:
                            # Supprime la règle par son handle
                            subprocess.run([
                                'sudo', 'nft', 'delete', 'rule', 'ip', 'ngfw_congo', 
                                'block_chain', 'handle', str(i+1)
                            ], check=True, capture_output=True)
                    
                    del self.blocked_ips[ip_address]
                    logger.info(f"✅ IP DÉBLOQUÉE: {ip_address}")
                    return True
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"Erreur lors du déblocage de {ip_address}: {e.stderr.decode()}")
                    return False
        return False
    
    def is_private_ip(self, ip_address):
        """Vérifie si une IP est dans une plage privée."""
        private_ranges = [
            ('10.0.0.0', '10.255.255.255'),
            ('172.16.0.0', '172.31.255.255'),
            ('192.168.0.0', '192.168.255.255')
        ]
        
        from ipaddress import ip_address as ip_obj
        ip = ip_obj(ip_address)
        
        for start, end in private_ranges:
            if ip >= ip_obj(start) and ip <= ip_obj(end):
                return True
        return False
    
    def cleanup_expired_blocks(self):
        """Nettoie les blocages expirés."""
        with self.lock:
            now = datetime.now()
            expired_ips = []
            
            for ip, (timestamp, reason) in self.blocked_ips.items():
                if now - timestamp > timedelta(minutes=60):  # 60 minutes par défaut
                    expired_ips.append(ip)
            
            for ip in expired_ips:
                self.unblock_ip(ip)
    
    def get_blocked_ips(self):
        """Retourne la liste des IPs actuellement bloquées."""
        with self.lock:
            return self.blocked_ips.copy()

# Instance globale du bloqueur
blocker = IPBlocker()

def init_blocker():
    """Initialise le bloqueur global."""
    global blocker
    # Démarre le thread de nettoyage périodique
    def cleanup_loop():
        while True:
            time.sleep(300)  # Toutes les 5 minutes
            blocker.cleanup_expired_blocks()
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    
    return blocker

# Test du module
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    blocker = init_blocker()
    
    # Test de blocage (remplacez par une IP de test)
    test_ip = "192.0.2.1"  # IP de test RFC 5737
    blocker.block_ip(test_ip, "Test de blocage", 1)  # 1 minute
    
    print("IP bloquée. Attente 70 secondes pour le déblocage automatique...")
    time.sleep(70)
    
    print("Test terminé.")
