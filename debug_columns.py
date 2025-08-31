#!/usr/bin/env python3

import pandas as pd
import os

dataset_path = "CIC-IDS-2017"
all_files = []
for root, dirs, files in os.walk(dataset_path):
    for file in files:
        if file.endswith(".csv"):
            all_files.append(os.path.join(root, file))

if not all_files:
    print("Aucun fichier CSV trouvé.")
    exit(1)

# Prenons le premier fichier qui a causé l'erreur
file_path = all_files[0]
print(f"Fichier : {os.path.basename(file_path)}")

# Charge juste les premières lignes pour voir les colonnes
df = pd.read_csv(file_path, nrows=5)
print("\n=== COLONNES DANS CE FICHIER ===")
print(df.columns.tolist())

print("\n=== 5 PREMIÈRES LIGNES ===")
print(df.head())

# Cherchons une colonne qui pourrait être le label
possible_label_names = ['Label', 'label', 'Attack', 'attack', 'Class', 'class']
for col in df.columns:
    if any(name in col for name in possible_label_names):
        print(f"\n Colonne candidate pour le label : '{col}'")
        print(f" Valeurs uniques dans cette colonne : {df[col].unique()}")
