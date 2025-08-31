#!/usr/bin/env python3
"""
Script d'entraînement du modèle IA pour NGFW-Congo.
Utilise le dataset CIC-IDS2017 pour entraîner un Isolation Forest.
"""

import pandas as pd
import numpy as np
import os
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import warnings
warnings.filterwarnings('ignore')

# 1. ===== CONFIGURATION =====
print("[+] Configuration de l'entraînement...")
dataset_path = "CIC-IDS-2017"  # Chemin vers le dossier du dataset
model_filename = "isolation_forest_model.pkl"
test_size = 0.3  # 30% des données pour le test
random_state = 42 # Seed pour la reproductibilité

# 2. ===== CHARGEMENT DES DONNÉES =====
print("[+] Chargement des données...")
# Trouve tous les fichiers CSV dans le dossier du dataset
all_files = []
for root, dirs, files in os.walk(dataset_path):
    for file in files:
        if file.endswith(".csv"):
            all_files.append(os.path.join(root, file))

if not all_files:
    print("[!] Aucun fichier CSV trouvé dans le dossier. Vérifiez le chemin.")
    exit(1)

print(f"    {len(all_files)} fichiers CSV trouvés.")

# Charge le premier fichier pour commencer
file_path = all_files[0]
print(f"    Chargement du fichier : {os.path.basename(file_path)}")

try:
    df = pd.read_csv(file_path)
    print(f"    Données chargées : {df.shape[0]} lignes, {df.shape[1]} colonnes.")
except Exception as e:
    print(f"[!] Erreur lors du chargement du CSV : {e}")
    exit(1)

# 3. ===== NETTOYAGE DES DONNÉES =====
print("[+] Nettoyage des données...")

# Étape 1: Identifier la colonne de label AVANT de nettoyer
print("    Identification de la colonne de label...")
label_column = None
possible_labels = ['Label', 'label', 'Attack', 'attack', 'Class', 'class', ' Label']
for col in df.columns:
    if any(possible in col for possible in possible_labels):
        label_column = col
        print(f"    Colonne de label identifiée : '{label_column}'")
        break

if label_column is None:
    print("[!] Impossible de trouver une colonne de label. Vérifiez le dataset.")
    print(f"    Colonnes disponibles : {df.columns.tolist()}")
    exit(1)

# Étape 2: Supprimer les colonnes non numériques problématiques
cols_to_drop = [
    'Timestamp', ' Timestamp',  # Les deux versions
    'Flow ID', 
    'Src IP', 'Dst IP', 
    ' Source IP', ' Destination IP'  # Les versions avec espaces
]
# Ne garde que les colonnes qui existent dans le DataFrame
cols_to_drop = [col for col in cols_to_drop if col in df.columns]
df_clean = df.drop(columns=cols_to_drop, errors='ignore')

# Étape 3: Conversion forcée des colonnes en numérique (SAUF le label)
print("    Conversion forcée des colonnes en valeurs numériques...")
for col in df_clean.columns:
    if col == label_column:  # Ne pas convertir la colonne de label
        continue
    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

# Remplacer les NaN par 0 après conversion
df_clean = df_clean.fillna(0)
print("    Conversion terminée.")
print(f"    Données après nettoyage : {df_clean.shape}")

# 4. ===== PRÉPARATION DES LABELS =====
print("[+] Préparation des labels...")
# Conversion des labels: 'BENIGN' -> 0, tout autre chose (attaque) -> 1
df_clean['Label'] = df_clean[label_column].apply(lambda x: 0 if x == 'BENIGN' else 1)

# Séparation des features (X) et du label (y)
X = df_clean.drop([label_column, 'Label'], axis=1, errors='ignore')  # Supprime l'ancienne colonne et la nouvelle
y = df_clean['Label']  # On utilise notre nouvelle colonne

print(f"    Features initiales (X) : {X.shape}")
print(f"    Labels (y) : {y.shape}")

# 5. ===== SELECTION DES FEATURES =====
print("[+] Sélection des features compatibles temps réel...")

# Liste des features que notre extracteur temps réel peut générer
realtime_features = [
    ' Flow Duration',           # Correspond à 'Duration'
    ' Total Fwd Packets',       # Correspond à 'Tot Fwd Pkts'
    ' Total Backward Packets',  # Correspond à 'Tot Bwd Pkts'
    'Total Length of Fwd Packets',  # Correspond à 'TotLen Fwd Packets'
    ' Total Length of Bwd Packets', # Correspond à 'TotLen Bwd Packets'
    'Flow Bytes/s',
    ' Flow Packets/s'
]

# Trouver les features disponibles qui correspondent
available_features = [col for col in X.columns if col in realtime_features]
print(f"    Features disponibles pour temps réel : {available_features}")

if len(available_features) < 3:  # Au moins 3 features pour que ça vaille la peine
    print("[!] Trop peu de features compatibles temps réel. Utilisation de toutes les features.")
    available_features = X.columns.tolist()
else:
    # Réduire X aux features compatibles temps réel
    X = X[available_features]
    print(f"    Dataset réduit à {X.shape[1]} features compatibles temps réel.")

print(f"    Features finales : {list(X.columns)}")

# 6. ===== ENTRAÎNEMENT DU MODÈLE =====
print("[+] Entraînement du modèle Isolation Forest...")
model = IsolationForest(
    n_estimators=100,
    max_samples='auto',
    contamination='auto',
    random_state=random_state,
    n_jobs=-1  # Utilise tous les coeurs CPU
)

model.fit(X)
print("    Entraînement terminé.")

# 7. ===== ÉVALUATION DU MODÈLE =====
print("[+] Évaluation du modèle...")
y_pred = model.predict(X)
y_pred = [1 if x == -1 else 0 for x in y_pred]  # Convertit -1->1 (attaque), 1->0 (normal)

accuracy = accuracy_score(y, y_pred)
print(f"    Précision sur l'ensemble d'entraînement : {accuracy:.4f}")

print("\n" + "="*50)
print("RAPPORT DE CLASSIFICATION :")
print("="*50)
print(classification_report(y, y_pred, target_names=['BENIGN', 'ATTACK']))

print("\nMATRICE DE CONFUSION :")
print(confusion_matrix(y, y_pred))

# 8. ===== SAUVEGARDE DU MODÈLE =====
print("[+] Sauvegarde du modèle...")
joblib.dump(model, model_filename)
print(f"    Modèle sauvegardé sous : {model_filename}")

print("\n[+] Entraînement terminé avec succès ! Le modèle est prêt pour la détection en temps réel.")
