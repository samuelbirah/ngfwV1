#!/usr/bin/env python3

from scapy.all import sniff, IP, TCP, Ether
from feature_extractor import packet_to_features
import json

def test_callback(packet):
    """Fonction de test qui affiche les features des flux expirés."""
    features = packet_to_features(packet)
    if features:
        print("=== FLUX TERMINÉ DÉTECTÉ ===")
        for flow in features:
            print(json.dumps(flow, indent=2))

# Capture quelques paquets pour tester
print("Démarrage du test de l'extracteur... Capture de 50 paquets.")
sniff(count=50, prn=test_callback, store=0)
print("Test terminé.")
