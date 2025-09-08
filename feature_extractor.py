#!/usr/bin/env python3
"""
Module d'Extraction de Features pour NGFW-Congo.
Transforme les paquets en flux NetFlow-like et calcule des caractéristiques.
"""

from scapy.all import IP, TCP, UDP
from datetime import datetime
import pandas as pd
import numpy as np
import logging

# Désactive les logs verbeux
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

class FlowGenerator:
    """
    Génère des flux à partir de paquets et calcule leurs caractéristiques.
    """
    def __init__(self, inactive_timeout=15, active_timeout=1800):
        # Dictionnaire pour stocker les flux en cours
        self.flows = {}
        # Timeout pour considérer un flux comme terminé (en secondes)
        self.inactive_timeout = inactive_timeout
        self.active_timeout = active_timeout

    def get_flow_id(self, packet):
        """
        Génère un identifiant unique pour un flux basé sur la 5-tuple :
        (Src IP, Dst IP, Src Port, Dst Port, Protocol)
        """
        if not packet.haslayer(IP):
            return None

        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        proto = packet[IP].proto

        # Gestion des ports pour TCP/UDP et autres protocoles
        src_port = 0
        dst_port = 0
        if packet.haslayer(TCP):
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif packet.haslayer(UDP):
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport

        # Crée un identifiant unique pour le flux
        flow_id = (src_ip, dst_ip, src_port, dst_port, proto)
        # Crée aussi un ID inverse pour gérer le trafic bidirectionnel
        reverse_flow_id = (dst_ip, src_ip, dst_port, src_port, proto)

        # Retourne les deux IDs pour vérifier si le flux existe déjà dans un sens ou dans l'autre
        return flow_id, reverse_flow_id

    def update_flow(self, packet, flow_id, timestamp):
        """
        Met à jour les statistiques d'un flux avec un nouveau paquet.
        """
        if flow_id not in self.flows:
            # Initialisation d'un nouveau flux
            self.flows[flow_id] = {
                'Start Time': timestamp,
                'Last Seen': timestamp,
                'Fwd Packets': 0,
                'Bwd Packets': 0,
                'Fwd Bytes': 0,
                'Bwd Bytes': 0,
                'Protocol': flow_id[4],  # Le protocole est le 5ème élément du tuple
                'Src IP': flow_id[0],
                'Dst IP': flow_id[1],
                'Src Port': flow_id[2],
                'Dst Port': flow_id[3],
            }

        flow = self.flows[flow_id]
        packet_length = len(packet)

        # Détermine la direction du paquet (Forward = Source -> Destination)
        if packet[IP].src == flow_id[0]:
            flow['Fwd Packets'] += 1
            flow['Fwd Bytes'] += packet_length
        else:
            flow['Bwd Packets'] += 1
            flow['Bwd Bytes'] += packet_length

        flow['Last Seen'] = timestamp

    def check_timeouts(self, current_time):
        """
        Vérifie et retourne les flux qui ont expiré (inactifs ou trop longs).
        """
        expired_flows = []
        for flow_id, flow_data in list(self.flows.items()):
            duration = (current_time - flow_data['Start Time']).total_seconds()
            inactive_time = (current_time - flow_data['Last Seen']).total_seconds()

            if inactive_time > self.inactive_timeout or duration > self.active_timeout:
                expired_flows.append((flow_id, flow_data))
                del self.flows[flow_id]

        return expired_flows

    def process_packet(self, packet):
        """
        Traite un paquet : l'ajoute à un flux existant ou crée un nouveau flux.
        Retourne une liste de flux expirés (terminés) à cause de ce paquet.
        """
        if not packet.haslayer(IP):
            return []  # Ignore les paquets non-IP

        timestamp = datetime.now()
        flow_id_tuple = self.get_flow_id(packet)

        if not flow_id_tuple:
            return []

        flow_id, reverse_flow_id = flow_id_tuple

        # Vérifie si le flux existe déjà dans un sens ou dans l'autre
        if flow_id in self.flows:
            self.update_flow(packet, flow_id, timestamp)
        elif reverse_flow_id in self.flows:
            # Le paquet est dans le sens inverse du flux enregistré
            self.update_flow(packet, reverse_flow_id, timestamp)
        else:
            # C'est un tout nouveau flux
            self.update_flow(packet, flow_id, timestamp)

        # Vérifie les timeouts après la mise à jour
        expired_flows = self.check_timeouts(timestamp)
        return expired_flows

# Instance globale du générateur de flux
flow_gen = FlowGenerator()

def filter_numeric_features(features_dict):
    """
    Filtre et ne garde que les features numériques pour le modèle IA.
    Supprime les adresses IP, ports, etc. qui ne sont pas dans le format d'entraînement.
    """
    # Liste des clés à SUPPRIMER (non numériques ou non utilisées pendant l'entraînement)
    keys_to_remove = [
        'Src IP', 'Dst IP', 'Src Port', 'Dst Port', 'Protocol',
        'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol'
    ]
    
    # Crée une nouvelle copie avec seulement les features numériques
    numeric_features = {}
    for key, value in features_dict.items():
        if key not in keys_to_remove:
            numeric_features[key] = value
    
    return numeric_features

def packet_to_features(packet):
    """
    Fonction principale appelée pour chaque paquet.
    Reçoit un paquet, le donne au générateur de flux.
    Si le paquet a provoqué l'expiration d'un flux, on retourne les features de ce flux.
    """
    expired_flows = flow_gen.process_packet(packet)

    def packet_to_features(packet):
        """
        Fonction principale appelée pour chaque paquet.
        Reçoit un paquet, le donne au générateur de flux.
        Si le paquet a provoqué l'expiration d'un flux, on retourne les features de ce flux.
        """
        expired_flows = flow_gen.process_packet(packet)

        features_list = []
        for flow_id, flow_data in expired_flows:
            # Calcule la durée du flux
            duration = (flow_data['Last Seen'] - flow_data['Start Time']).total_seconds()

            # Crée un dictionnaire de features pour ce flux AVEC TOUTES LES INFORMATIONS
            flow_features = {
                # Features numériques pour le modèle IA
                'Duration': duration,
                'Tot Fwd Pkts': flow_data['Fwd Packets'],
                'Tot Bwd Pkts': flow_data['Bwd Packets'],
                'TotLen Fwd Pkts': flow_data['Fwd Bytes'],
                'TotLen Bwd Pkts': flow_data['Bwd Bytes'],
                'Flow Bytes/s': (flow_data['Fwd Bytes'] + flow_data['Bwd Bytes']) / duration if duration > 0 else 0,
                'Flow Packets/s': (flow_data['Fwd Packets'] + flow_data['Bwd Packets']) / duration if duration > 0 else 0,
                
                # Informations critiques pour le logging et blocage (DOIT ÊTRE INCLUS)
                'Src IP': flow_data['Src IP'],
                'Dst IP': flow_data['Dst IP'], 
                'Protocol': flow_data['Protocol'],
                'Src Port': flow_data['Src Port'],
                'Dst Port': flow_data['Dst Port'],
                'Start Time': flow_data['Start Time'].isoformat(),
                'Last Seen': flow_data['Last Seen'].isoformat()
            }
            features_list.append(flow_features)

        return features_list

# Test simple si le script est exécuté directement
if __name__ == "__main__":
    print("Module d'extraction de features chargé. Prêt à être importé.")
    print("Il sera utilisé par le prochain script qui combine capture et extraction.")
