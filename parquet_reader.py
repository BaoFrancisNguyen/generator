# read_parquet.py
"""
Script simple pour lire les fichiers .parquet
"""

import pandas as pd
import os

def read_parquet_files():
    """Lit tous les fichiers parquet du dossier generated_data"""
    
    # Dossier des données
    data_folder = 'generated_data'
    
    if not os.path.exists(data_folder):
        print(f"❌ Dossier '{data_folder}' non trouvé")
        return
    
    # Lister les fichiers .parquet
    parquet_files = [f for f in os.listdir(data_folder) if f.endswith('.parquet')]
    
    if not parquet_files:
        print("❌ Aucun fichier .parquet trouvé")
        return
    
    print("📁 Fichiers trouvés:")
    for f in parquet_files:
        print(f"   • {f}")
    
    # Lire chaque fichier
    for filename in parquet_files:
        filepath = os.path.join(data_folder, filename)
        
        print(f"\n📊 Lecture de {filename}:")
        print("-" * 50)
        
        try:
            # Charger le fichier
            df = pd.read_parquet(filepath)
            
            # Infos de base
            print(f"Lignes: {len(df):,}")
            print(f"Colonnes: {len(df.columns)}")
            print(f"Colonnes: {list(df.columns)}")
            
            # Aperçu des données
            print("\n🔍 Aperçu (50 premières lignes):")
            print(df.head(50))
            
            # Stats rapides si c'est des données de consommation
            if 'y' in df.columns:
                print(f"\n📈 Stats consommation:")
                print(f"   Moyenne: {df['y'].mean():.2f} kW")
                print(f"   Maximum: {df['y'].max():.2f} kW")
                print(f"   Minimum: {df['y'].min():.2f} kW")
            
            # Stats par type de bâtiment
            if 'building_class' in df.columns:
                print(f"\n🏢 Types de bâtiments:")
                counts = df['building_class'].value_counts()
                for building_type, count in counts.items():
                    print(f"   {building_type}: {count}")
            
            # Villes
            if 'location' in df.columns:
                print(f"\n🌍 Villes (top 5):")
                cities = df['location'].value_counts().head()
                for city, count in cities.items():
                    print(f"   {city}: {count}")
                    
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    read_parquet_files()