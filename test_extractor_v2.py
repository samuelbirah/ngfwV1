#!/usr/bin/env python3

from scapy.all import sniff, IP, TCP, Ether
from feature_extractor import packet_to_features, flow_gen
import json
import time

def test_callback(packet):
    """Fonction de test qui affiche les features des flux expirés."""
    features = packet_to_features(packet)
    if features:
        print("=== FLUX TERMINÉ DÉTECTÉ ===")
        for flow in features:
            print(json.dumps(flow, indent=2))

# Capture quelques paquets pour tester
print("Démarrage du test de l'extracteur... Capture de 100 paquets.")
sniff(count=100, prn=test_callback, store=0)

# Attendre un peu pour que certains flux puissent expirer
print("\nCapture terminée. Attente de 20 secondes pour l'expiration des flux...")
time.sleep(20)

# FORCE la vérification des timeouts pour tous les flux restants
# Cela simule ce qui se passerait en temps normal avec le timeout
current_time = time.time()
expired_flows = flow_gen.check_timeouts(current_time)

if expired_flows:
    print("\n=== FLUX EXPIRÉS FORCÉS À LA FIN ===")
    for flow_id, flow_data in expired_flows:
        duration = (flow_data['Last Seen'] - flow_data['Start Time']).total_seconds()
        flow_features = {
            'Duration': duration,
            'Protocol': flow_data['Protocol'],
            'Src IP': flow_data['Src IP'],
            'Dst IP': flow_data['Dst IP'],
            'Tot Fwd Pkts': flow_data['Fwd Packets'],
            'Tot Bwd Pkts': flow_data['Bwd Packets'],
            'TotLen Fwd Pkts': flow_data['Fwd Bytes'],
            'TotLen Bwd Pkts': flow_data['Bwd Bytes'],
        }
        print(json.dumps(flow_features, indent=2))
else:
    print("\nAucun flux n'a été généré pendant la capture. Génération de trafic (pings, pages web) et réessayez.")

print("Test terminé.")
