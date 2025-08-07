#!/usr/bin/env python3
"""
Générateur de Données Électriques pour la MALAISIE
Basé sur l'analyse de votre dataset avec localisation en Malaisie

Instructions d'installation:
1. pip install -r requirements.txt
2. python run.py
3. Ouvrir http://localhost:5000

Fonctionnalités spéciales Malaisie:
- 60+ vraies villes malaisiennes avec populations réelles
- Climat tropical avec pics de climatisation
- Patterns culturels (Ramadan, Vendredi après-midi)
- Saisons des pluies vs saisons sèches
- Coordonnées GPS précises de chaque ville
- Tarification électrique par tranche horaire
- Événements climatiques tropicaux
"""

import os
import sys

def check_dependencies():
    """Vérifier que toutes les dépendances sont installées"""
    required = ['flask', 'pandas', 'numpy', 'pyarrow']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Dépendances manquantes:", ", ".join(missing))
        print("Installez avec: pip install -r requirements.txt")
        return False
    
    return True

def create_directories():
    """Créer les dossiers nécessaires"""
    directories = ['generated_data', 'templates', 'static']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Dossier créé: {directory}")

def show_malaysia_info():
    """Afficher les informations sur les données de Malaisie"""
    try:
        from app import generator
        
        print("\n🇲🇾 INFORMATIONS MALAISIE")
        print("=" * 60)
        
        # Afficher les plus grandes villes
        sorted_cities = sorted(
            generator.malaysia_locations.items(), 
            key=lambda x: x[1]['population'], 
            reverse=True
        )
        
        print("TOP 10 DES VILLES PAR POPULATION:")
        for i, (city, info) in enumerate(sorted_cities[:10]):
            print(f"   {i+1:2d}. {city:<20} {info['population']:>8,} habitants ({info['state']})")
        
        print(f"\nRÉPARTITION PAR RÉGION:")
        regions = {}
        for city, info in generator.malaysia_locations.items():
            region = info['region']
            if region not in regions:
                regions[region] = []
            regions[region].append(city)
        
        for region, cities in regions.items():
            print(f"   • {region:<20} {len(cities):2d} villes")
        
        print(f"\n CARACTÉRISTIQUES SPÉCIALES:")
        print("   • Climat tropical avec pics de climatisation 11h-16h")
        print("   • Patterns culturels: Vendredi après-midi, période Ramadan")
        print("   • Saisons: Pluies (Nov-Fév) vs Sèche chaude (Mai-Août)")
        print("   • Tarifs électriques variables selon l'heure")
        print("   • Distribution réaliste selon la population des villes")
        
    except ImportError:
        print("Informations Malaisie disponibles après démarrage")

def main():
    print("GÉNÉRATEUR DE DONNÉES ÉLECTRIQUES - MALAISIE")
    print("=" * 70)
    
    # Vérifications préliminaires
    if not check_dependencies():
        sys.exit(1)
    
    create_directories()
    show_malaysia_info()
    
    # Importer et démarrer l'application
    try:
        from app import app, generator
        
        print(" Application initialisée avec succès!")
        print(f" {len(generator.malaysia_locations)} villes de Malaisie disponibles")
        print(f" {len(generator.building_classes)} types de bâtiments")
        print("Patterns tropicaux ultra-réalistes intégrés")
        
        print("\n Démarrage du serveur...")
        print("Interface principale: http://localhost:5000")
        print("API statistiques:     http://localhost:5000/api/stats")
        print("\n Conseil: Testez d'abord avec un échantillon de 5-10 bâtiments")
        print(" Période suggérée: 1 mois pour voir les patterns saisonniers")
        print("-" * 70)
        
        # Démarrer l'application Flask
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f" Erreur d'import: {e}")
        print(" Assurez-vous que le fichier 'app.py' existe dans ce dossier")
    except Exception as e:
        print(f" Erreur: {e}")

if __name__ == '__main__':
    main()