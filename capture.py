#!/usr/bin/env python3
"""
Module de Capture NGFW-Congo
Capture le trafic réseau en temps réel avec Scapy.
"""

import argparse
from scapy.all import sniff, Ether, IP, TCP, UDP, ICMP
from datetime import datetime

# Désactive les messages d'erreur trop verbeux de Scapy
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# Compteur de paquets global (pour l'exemple)
packet_count = 0

def process_packet(packet):
    """
    Fonction de rappel (callback) appelée pour chaque paquet capturé.
    Pour l'instant, on se contente d'afficher des infos basiques.
    """
    global packet_count
    packet_count += 1

    # Heure de capture
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Initialisation des variables pour les infos du paquet
    proto = "Other"
    src_ip = "N/A"
    dst_ip = "N/A"
    sport = "N/A"
    dport = "N/A"

    # Extraction des informations de couche 2 (Ethernet)
    if packet.haslayer(Ether):
        src_mac = packet[Ether].src
        dst_mac = packet[Ether].dst
    else:
        src_mac = "N/A"
        dst_mac = "N/A"

    # Extraction des informations de couche 3 (IP)
    if packet.haslayer(IP):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        proto = packet[IP].proto

        # Décodage du numéro de protocole pour avoir un nom
        if proto == 6:
            proto_name = "TCP"
        elif proto == 17:
            proto_name = "UDP"
        elif proto == 1:
            proto_name = "ICMP"
        else:
            proto_name = f"IP-{proto}"

        # Extraction des informations de couche 4 (TCP/UDP)
        if packet.haslayer(TCP):
            sport = packet[TCP].sport
            dport = packet[TCP].dport
        elif packet.haslayer(UDP):
            sport = packet[UDP].sport
            dport = packet[UDP].sport

        # Affichage des informations essentielles du paquet
        print(f"[{current_time}] Packet #{packet_count:6}: {src_ip:15} -> {dst_ip:15} | {proto_name:4} | SPort: {sport:5} | DPort: {dport:5} | Length: {len(packet):4} bytes")

    # On pourrait ici, plus tard, envoyer le paquet vers une file d'attente
    # pour qu'il soit traité par le module d'extraction.

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description='Captureur de paquets simple pour NGFW-Congo')
    parser.add_argument('-i', '--interface', type=str, help='Interface réseau à écouter (ex: eth0)', required=True)
    parser.add_argument('-c', '--count', type=int, default=0, help='Nombre de paquets à capturer (0 = infini)')
    args = parser.parse_args()

    print(f"[*] Démarrage de la capture sur l'interface {args.interface}...")
    print("[*] Appuyez sur Ctrl+C pour arrêter.\n")

    # Lance la capture en continue
    # 'prn' est la fonction à appeler pour chaque paquet
    # 'store=0' signifie qu'on ne stocke pas les paquets en mémoire, on les traite et on les jette.
    try:
        sniff(iface=args.interface, prn=process_packet, count=args.count, store=0)
    except KeyboardInterrupt:
        print("\n[*] Capture interrompue par l'utilisateur.")
    except PermissionError:
        print("[!] Erreur de permissions. Essayez de lancer le script avec 'sudo'.")
    except Exception as e:
        print(f"[!] Une erreur s'est produite: {e}")

if __name__ == "__main__":
    main()
