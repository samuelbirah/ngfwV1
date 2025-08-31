#!/usr/bin/env python3
"""
Module de Détection en Temps Réel pour NGFW-Congo.
Charge le modèle IA et prédit si un flux est normal ou anormal.
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import logging
import json
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NGFWDetector:
    def __init__(self, model_path):
        """
        Initialise le détecteur avec le modèle entraîné.
        """
        logger.info(f"Chargement du modèle depuis {model_path}...")
        try:
            self.model = joblib.load(model_path)
            logger.info("Modèle chargé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle : {e}")
            raise

        # Scaler pour normaliser les features (important pour de bonnes performances)
        self.scaler = StandardScaler()
        # Nous allons l'adapter avec les premières données reçues
        self.is_scaler_fitted = False

        # Seuil de décision (peut être ajusté)
        self.threshold = -0.2  # Valeurs en dessous de ce seuil sont considérées comme des anomalies

        # Statistiques
        self.total_flows_processed = 0
        self.anomalies_detected = 0

    def preprocess_features(self, features_dict):
        """
        Transforme un dictionnaire de features en format adapté pour le modèle.
        Effectue également la normalisation.
        """
        # Crée un DataFrame d'une seule ligne avec les features
        single_flow_df = pd.DataFrame([features_dict])
        
        # Si le scaler n'est pas encore ajusté, on l'ajuste sur les premières données
        if not self.is_scaler_fitted:
            self.scaler.fit(single_flow_df)
            self.is_scaler_fitted = True
            logger.info("Scaler ajusté avec les premières données.")
        
        # Normalise les features
        normalized_features = self.scaler.transform(single_flow_df)
        return normalized_features

    def predict(self, features_dict):
        """
        Fait une prédiction sur un seul flux réseau.
        Retourne le score d'anomalie et la décision.
        """
        self.total_flows_processed += 1

        try:
            # Prétraitement des features
            processed_features = self.preprocess_features(features_dict)
            
            # Prédiction avec le modèle Isolation Forest
            # Isolation Forest retourne un score: plus il est négatif, plus c'est anormal
            anomaly_score = self.model.decision_function(processed_features)[0]
            
            # Prise de décision basée sur le seuil
            is_anomaly = anomaly_score < self.threshold
            
            # Mise à jour des statistiques
            if is_anomaly:
                self.anomalies_detected += 1

            return {
                'anomaly_score': float(anomaly_score),
                'is_anomaly': bool(is_anomaly),
                'decision_threshold': float(self.threshold)
            }

        except Exception as e:
            logger.error(f"Erreur lors de la prédiction : {e}")
            return {
                'anomaly_score': 0.0,
                'is_anomaly': False,
                'error': str(e)
            }

    def get_stats(self):
        """
        Retourne les statistiques de détection.
        """
        return {
            'total_flows_processed': self.total_flows_processed,
            'anomalies_detected': self.anomalies_detected,
            'anomaly_rate': self.anomalies_detected / self.total_flows_processed if self.total_flows_processed > 0 else 0
        }

# Instance globale du détecteur
detector = None

def init_detector(model_path="isolation_forest_model.pkl"):
    """
    Initialise le détecteur global.
    """
    global detector
    detector = NGFWDetector(model_path)
    return detector

def detect_anomaly(features_dict):
    """
    Fonction principale pour détecter une anomalie dans un flux.
    """
    global detector
    if detector is None:
        init_detector()
    
    return detector.predict(features_dict)

# Test du détecteur
if __name__ == "__main__":
    print("Testing NGFW-Congo Detector...")
    
    # Initialisation
    detector = init_detector()
    
    # Création d'un exemple de flux normal (similaire à ce que produit notre extracteur)
    sample_normal_flow = {
        'Duration': 1.5,
        'Protocol': 6,  # TCP
        'Src Port': 54321,
        'Dst Port': 80,  # HTTP
        'Tot Fwd Pkts': 10,
        'Tot Bwd Pkts': 8,
        'TotLen Fwd Pkts': 1500,
        'TotLen Bwd Pkts': 1200,
        'Flow Bytes/s': 1800.5,
        'Flow Packets/s': 12.2
    }
    
    print("\n1. Test avec un flux normal :")
    result = detector.predict(sample_normal_flow)
    print(f"Résultat : {json.dumps(result, indent=2)}")
    
    # Création d'un exemple de flux potentiellement anormal
    sample_anomalous_flow = {
        'Duration': 0.001,  # Très courte durée
        'Protocol': 6,
        'Src Port': 12345,
        'Dst Port': 22,  # SSH
        'Tot Fwd Pkts': 1000,  # Beaucoup de paquets
        'Tot Bwd Pkts': 1,
        'TotLen Fwd Pkts': 50000,  # Beaucoup de données
        'TotLen Bwd Pkts': 100,
        'Flow Bytes/s': 50000000.0,  # Débit très élevé
        'Flow Packets/s': 1000000.0  # Très haut taux de paquets
    }
    
    print("\n2. Test avec un flux potentiellement anormal :")
    result = detector.predict(sample_anomalous_flow)
    print(f"Résultat : {json.dumps(result, indent=2)}")
    
    print("\n3. Statistiques :")
    print(json.dumps(detector.get_stats(), indent=2))
    
    print("\nTest terminé. Le détecteur est fonctionnel !")
