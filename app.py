from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid
import os
import json

app = Flask(__name__)

class ElectricityDataGenerator:
    """Générateur de données électriques réalistes pour la Malaisie"""
    
    def __init__(self):
        # Types de bâtiments
        self.building_classes = [
            'Residential', 'Commercial', 'Industrial', 'Office', 
            'Retail', 'Hospital', 'School', 'Hotel', 'Restaurant',
            'Warehouse', 'Factory', 'Apartment'
        ]
        
        # Localisations réelles de Malaisie avec populations
        self.malaysia_locations = {
            # États (Negeri) - Grandes villes
            'Kuala Lumpur': {'population': 1800000, 'state': 'Federal Territory', 'region': 'Central'},
            'George Town': {'population': 708000, 'state': 'Penang', 'region': 'Northern'},
            'Ipoh': {'population': 657000, 'state': 'Perak', 'region': 'Northern'},
            'Shah Alam': {'population': 641000, 'state': 'Selangor', 'region': 'Central'},
            'Petaling Jaya': {'population': 613000, 'state': 'Selangor', 'region': 'Central'},
            'Johor Bahru': {'population': 497000, 'state': 'Johor', 'region': 'Southern'},
            'Subang Jaya': {'population': 469000, 'state': 'Selangor', 'region': 'Central'},
            'Klang': {'population': 440000, 'state': 'Selangor', 'region': 'Central'},
            'Kota Kinabalu': {'population': 452000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Malacca City': {'population': 455000, 'state': 'Malacca', 'region': 'Southern'},
            
            # Villes moyennes importantes
            'Alor Setar': {'population': 405000, 'state': 'Kedah', 'region': 'Northern'},
            'Seremban': {'population': 372000, 'state': 'Negeri Sembilan', 'region': 'Central'},
            'Kuantan': {'population': 366000, 'state': 'Pahang', 'region': 'East Coast'},
            'Iskandar Puteri': {'population': 360000, 'state': 'Johor', 'region': 'Southern'},
            'Tawau': {'population': 313000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Ampang Jaya': {'population': 315000, 'state': 'Selangor', 'region': 'Central'},
            'Miri': {'population': 300000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            'Kuching': {'population': 325000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            'Sandakan': {'population': 279000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Kuala Terengganu': {'population': 285000, 'state': 'Terengganu', 'region': 'East Coast'},
            
            # Villes petites et moyennes
            'Taiping': {'population': 245000, 'state': 'Perak', 'region': 'Northern'},
            'Batu Pahat': {'population': 239000, 'state': 'Johor', 'region': 'Southern'},
            'Kluang': {'population': 233000, 'state': 'Johor', 'region': 'Southern'},
            'Muar': {'population': 210000, 'state': 'Johor', 'region': 'Southern'},
            'Pasir Gudang': {'population': 200000, 'state': 'Johor', 'region': 'Southern'},
            'Kota Bharu': {'population': 491000, 'state': 'Kelantan', 'region': 'East Coast'},
            'Sungai Petani': {'population': 228000, 'state': 'Kedah', 'region': 'Northern'},
            'Sibu': {'population': 183000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            'Lahad Datu': {'population': 156000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Putrajaya': {'population': 109000, 'state': 'Federal Territory', 'region': 'Central'},
            
            # Villes plus petites mais importantes économiquement
            'Kulim': {'population': 145000, 'state': 'Kedah', 'region': 'Northern'},
            'Segamat': {'population': 138000, 'state': 'Johor', 'region': 'Southern'},
            'Temerloh': {'population': 135000, 'state': 'Pahang', 'region': 'East Coast'},
            'Bentong': {'population': 112000, 'state': 'Pahang', 'region': 'East Coast'},
            'Raub': {'population': 106000, 'state': 'Pahang', 'region': 'East Coast'},
            'Bintulu': {'population': 114000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            'Limbang': {'population': 86000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            'Keningau': {'population': 84000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Beaufort': {'population': 79000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Papar': {'population': 75000, 'state': 'Sabah', 'region': 'East Malaysia'},
            
            # Villes côtières et touristiques
            'Langkawi': {'population': 65000, 'state': 'Kedah', 'region': 'Northern'},
            'Kuala Perlis': {'population': 48000, 'state': 'Perlis', 'region': 'Northern'},
            'Kangar': {'population': 73000, 'state': 'Perlis', 'region': 'Northern'},
            'Port Dickson': {'population': 58000, 'state': 'Negeri Sembilan', 'region': 'Central'},
            'Mersing': {'population': 45000, 'state': 'Johor', 'region': 'Southern'},
            'Kuala Lipis': {'population': 42000, 'state': 'Pahang', 'region': 'East Coast'},
            'Jerantut': {'population': 39000, 'state': 'Pahang', 'region': 'East Coast'},
            'Kemaman': {'population': 52000, 'state': 'Terengganu', 'region': 'East Coast'},
            'Dungun': {'population': 48000, 'state': 'Terengganu', 'region': 'East Coast'},
            'Besut': {'population': 35000, 'state': 'Terengganu', 'region': 'East Coast'},
            
            # Centres industriels
            'Port Klang': {'population': 180000, 'state': 'Selangor', 'region': 'Central'},
            'Nilai': {'population': 125000, 'state': 'Negeri Sembilan', 'region': 'Central'},
            'Kajang': {'population': 342000, 'state': 'Selangor', 'region': 'Central'},
            'Cheras': {'population': 381000, 'state': 'Selangor', 'region': 'Central'},
            'Puchong': {'population': 388000, 'state': 'Selangor', 'region': 'Central'},
            'Cyberjaya': {'population': 65000, 'state': 'Selangor', 'region': 'Central'},
            'Bangi': {'population': 190000, 'state': 'Selangor', 'region': 'Central'},
            'Sepang': {'population': 95000, 'state': 'Selangor', 'region': 'Central'}
        }
        
        # Fuseau horaire de la Malaisie
        self.timezones = ['Asia/Kuala_Lumpur']
        
        # Patterns de consommation réalistes (en kWh basés sur votre dataset)
        self.consumption_patterns = {
            'Residential': {'base': 0.5, 'peak': 12.0, 'variance': 2.5, 'night_factor': 0.3},
            'Commercial': {'base': 5.0, 'peak': 80.0, 'variance': 15.0, 'night_factor': 0.2},
            'Industrial': {'base': 20.0, 'peak': 200.0, 'variance': 40.0, 'night_factor': 0.7},
            'Office': {'base': 3.0, 'peak': 45.0, 'variance': 8.0, 'night_factor': 0.1},
            'Retail': {'base': 2.0, 'peak': 35.0, 'variance': 6.0, 'night_factor': 0.15},
            'Hospital': {'base': 25.0, 'peak': 70.0, 'variance': 12.0, 'night_factor': 0.8},
            'School': {'base': 1.0, 'peak': 25.0, 'variance': 5.0, 'night_factor': 0.05},
            'Hotel': {'base': 8.0, 'peak': 40.0, 'variance': 8.0, 'night_factor': 0.6},
            'Restaurant': {'base': 3.0, 'peak': 60.0, 'variance': 15.0, 'night_factor': 0.2},
            'Warehouse': {'base': 2.0, 'peak': 30.0, 'variance': 8.0, 'night_factor': 0.4},
            'Factory': {'base': 30.0, 'peak': 150.0, 'variance': 35.0, 'night_factor': 0.6},
            'Apartment': {'base': 1.0, 'peak': 15.0, 'variance': 4.0, 'night_factor': 0.4}
        }
    
    def generate_unique_id(self):
        """Génère un ID unique au format de votre dataset"""
        return ''.join(random.choices('abcdef0123456789', k=16))
    
    def generate_coordinates(self, location):
        """Génère des coordonnées GPS réalistes pour la Malaisie"""
        # Coordonnées précises des villes de Malaisie
        coords = {
            # Péninsule malaise - Région centrale
            'Kuala Lumpur': {'lat': (3.1319, 3.1681), 'lon': (101.6841, 101.7381)},
            'Shah Alam': {'lat': (3.0667, 3.1167), 'lon': (101.4833, 101.5333)},
            'Petaling Jaya': {'lat': (3.1073, 3.1273), 'lon': (101.6063, 101.6263)},
            'Subang Jaya': {'lat': (3.0422, 3.0622), 'lon': (101.5814, 101.6014)},
            'Klang': {'lat': (3.0333, 3.0533), 'lon': (101.4333, 101.4533)},
            'Putrajaya': {'lat': (2.9167, 2.9367), 'lon': (101.6833, 101.7033)},
            'Cyberjaya': {'lat': (2.9167, 2.9367), 'lon': (101.6333, 101.6533)},
            'Kajang': {'lat': (2.9833, 3.0033), 'lon': (101.7833, 101.8033)},
            'Cheras': {'lat': (3.1167, 3.1367), 'lon': (101.7167, 101.7367)},
            'Puchong': {'lat': (3.0167, 3.0367), 'lon': (101.6167, 101.6367)},
            'Bangi': {'lat': (2.9167, 2.9367), 'lon': (101.7667, 101.7867)},
            'Ampang Jaya': {'lat': (3.1333, 3.1533), 'lon': (101.7333, 101.7533)},
            'Port Klang': {'lat': (3.0000, 3.0200), 'lon': (101.3833, 101.4033)},
            'Sepang': {'lat': (2.7167, 2.7367), 'lon': (101.7167, 101.7367)},
            
            # Région Nord
            'George Town': {'lat': (5.4000, 5.4300), 'lon': (100.3000, 100.3300)},
            'Ipoh': {'lat': (4.5833, 4.6033), 'lon': (101.0833, 101.1033)},
            'Alor Setar': {'lat': (6.1167, 6.1367), 'lon': (100.3667, 100.3867)},
            'Taiping': {'lat': (4.8500, 4.8700), 'lon': (100.7333, 100.7533)},
            'Sungai Petani': {'lat': (5.6167, 5.6367), 'lon': (100.4833, 100.5033)},
            'Kulim': {'lat': (5.3667, 5.3867), 'lon': (100.5667, 100.5867)},
            'Kangar': {'lat': (6.4333, 6.4533), 'lon': (100.1833, 100.2033)},
            'Kuala Perlis': {'lat': (6.4000, 6.4200), 'lon': (100.1333, 100.1533)},
            'Langkawi': {'lat': (6.3167, 6.3367), 'lon': (99.8167, 99.8367)},
            
            # Région Sud
            'Johor Bahru': {'lat': (1.4833, 1.5033), 'lon': (103.7333, 103.7533)},
            'Malacca City': {'lat': (2.1833, 2.2033), 'lon': (102.2500, 102.2700)},
            'Iskandar Puteri': {'lat': (1.4167, 1.4367), 'lon': (103.6167, 103.6367)},
            'Batu Pahat': {'lat': (1.8500, 1.8700), 'lon': (102.9333, 102.9533)},
            'Kluang': {'lat': (2.0333, 2.0533), 'lon': (103.3167, 103.3367)},
            'Muar': {'lat': (2.0333, 2.0533), 'lon': (102.5667, 102.5867)},
            'Pasir Gudang': {'lat': (1.4667, 1.4867), 'lon': (103.8833, 103.9033)},
            'Segamat': {'lat': (2.5167, 2.5367), 'lon': (102.8167, 102.8367)},
            'Mersing': {'lat': (2.4333, 2.4533), 'lon': (103.8333, 103.8533)},
            'Seremban': {'lat': (2.7167, 2.7367), 'lon': (101.9333, 101.9533)},
            'Nilai': {'lat': (2.8167, 2.8367), 'lon': (101.7833, 101.8033)},
            'Port Dickson': {'lat': (2.5167, 2.5367), 'lon': (101.7833, 101.8033)},
            
            # Côte Est
            'Kuantan': {'lat': (3.8167, 3.8367), 'lon': (103.3167, 103.3367)},
            'Kuala Terengganu': {'lat': (5.3167, 5.3367), 'lon': (103.1333, 103.1533)},
            'Kota Bharu': {'lat': (6.1167, 6.1367), 'lon': (102.2333, 102.2533)},
            'Temerloh': {'lat': (3.4500, 3.4700), 'lon': (102.4167, 102.4367)},
            'Bentong': {'lat': (3.5167, 3.5367), 'lon': (101.9000, 101.9200)},
            'Raub': {'lat': (3.7833, 3.8033), 'lon': (101.8667, 101.8867)},
            'Kemaman': {'lat': (4.2333, 4.2533), 'lon': (103.4167, 103.4367)},
            'Dungun': {'lat': (4.7667, 4.7867), 'lon': (103.4167, 103.4367)},
            'Besut': {'lat': (5.8167, 5.8367), 'lon': (102.5667, 102.5867)},
            'Kuala Lipis': {'lat': (4.1833, 4.2033), 'lon': (102.0500, 102.0700)},
            'Jerantut': {'lat': (3.9333, 3.9533), 'lon': (102.3667, 102.3867)},
            
            # Malaisie orientale - Sabah
            'Kota Kinabalu': {'lat': (5.9667, 5.9867), 'lon': (116.0667, 116.0867)},
            'Sandakan': {'lat': (5.8333, 5.8533), 'lon': (118.1167, 118.1367)},
            'Tawau': {'lat': (4.2333, 4.2533), 'lon': (117.8667, 117.8867)},
            'Lahad Datu': {'lat': (5.0167, 5.0367), 'lon': (118.3167, 118.3367)},
            'Keningau': {'lat': (5.3333, 5.3533), 'lon': (116.1500, 116.1700)},
            'Beaufort': {'lat': (5.3467, 5.3667), 'lon': (115.7417, 115.7617)},
            'Papar': {'lat': (5.7167, 5.7367), 'lon': (115.9333, 115.9533)},
            
            # Malaisie orientale - Sarawak
            'Kuching': {'lat': (1.5333, 1.5533), 'lon': (110.3333, 110.3533)},
            'Miri': {'lat': (4.3833, 4.4033), 'lon': (113.9833, 114.0033)},
            'Sibu': {'lat': (2.3000, 2.3200), 'lon': (111.8167, 111.8367)},
            'Bintulu': {'lat': (3.1667, 3.1867), 'lon': (113.0333, 113.0533)},
            'Limbang': {'lat': (4.7500, 4.7700), 'lon': (115.0000, 115.0200)}
        }
        
        if location in coords:
            lat_range = coords[location]['lat']
            lon_range = coords[location]['lon']
            lat = round(random.uniform(lat_range[0], lat_range[1]), 6)
            lon = round(random.uniform(lon_range[0], lon_range[1]), 6)
        else:
            # Coordonnées par défaut pour la Malaisie
            lat = round(random.uniform(1.0, 7.0), 6)  # Latitude Malaisie
            lon = round(random.uniform(99.5, 119.5), 6)  # Longitude Malaisie
        
        return lat, lon
    
    def generate_building_metadata(self, num_buildings=100, location_filter=None, custom_location=None):
        """Génère les métadonnées des bâtiments avec filtrage géographique"""
        buildings = []
        
        # Déterminer les localisations disponibles
        if custom_location:
            # Utiliser la localisation personnalisée
            available_locations = {custom_location['name']: custom_location}
        elif location_filter:
            # Filtrer selon les critères
            available_locations = {}
            for name, info in self.malaysia_locations.items():
                include = True
                
                if location_filter.get('city') and location_filter['city'] != 'all':
                    if name != location_filter['city']:
                        include = False
                
                if location_filter.get('state') and location_filter['state'] != 'all':
                    if info['state'] != location_filter['state']:
                        include = False
                
                if location_filter.get('region') and location_filter['region'] != 'all':
                    if info['region'] != location_filter['region']:
                        include = False
                
                if location_filter.get('population_min'):
                    if info['population'] < int(location_filter['population_min']):
                        include = False
                
                if location_filter.get('population_max'):
                    if info['population'] > int(location_filter['population_max']):
                        include = False
                
                if include:
                    available_locations[name] = info
        else:
            # Utiliser toutes les localisations
            available_locations = self.malaysia_locations
        
        if not available_locations:
            raise ValueError("Aucune localisation ne correspond aux critères de filtrage")
        
        # Obtenir la liste des villes avec pondération par population
        locations = list(available_locations.keys())
        populations = [available_locations[loc]['population'] for loc in locations]
        
        # Normaliser les poids
        total_pop = sum(populations)
        weights = [pop / total_pop for pop in populations]
        
        for i in range(num_buildings):
            unique_id = self.generate_unique_id()
            
            # Choisir une localisation pondérée par la population
            location = np.random.choice(locations, p=weights)
            location_info = available_locations[location]
            
            # Adapter le type de bâtiment selon la taille de la ville
            if location_info['population'] > 500000:  # Grandes villes
                building_class = random.choices(
                    self.building_classes,
                    weights=[15, 25, 15, 20, 10, 5, 3, 5, 2, 0, 0, 0]
                )[0]
            elif location_info['population'] > 200000:  # Villes moyennes
                building_class = random.choices(
                    self.building_classes,
                    weights=[25, 20, 10, 15, 15, 5, 5, 3, 2, 0, 0, 0]
                )[0]
            else:  # Petites villes
                building_class = random.choices(
                    self.building_classes,
                    weights=[35, 15, 8, 10, 12, 5, 10, 3, 2, 0, 0, 0]
                )[0]
            
            lat, lon = self.generate_coordinates(location)
            
            # Taille du cluster basée sur la population de la ville
            cluster_multiplier = min(location_info['population'] / 100000, 5.0)
            cluster_size = random.randint(1, max(1, int(50 * cluster_multiplier)))
            
            building = {
                'unique_id': unique_id,
                'dataset': 'malaysia_electricity_v1',
                'building_id': f'MY_{location_info["state"][:3].upper()}_{i+1:06d}',
                'location_id': f'MY_{hash(location) % 100000:05d}',
                'latitude': lat,
                'longitude': lon,
                'location': location,
                'state': location_info['state'],
                'region': location_info['region'],
                'population': location_info['population'],
                'timezone': 'Asia/Kuala_Lumpur',
                'building_class': building_class,
                'cluster_size': cluster_size,
                'freq': '30T'
            }
            buildings.append(building)
        
        return pd.DataFrame(buildings)
    
    def calculate_realistic_consumption(self, building_class, timestamp, location_info=None):
        """Calcule une consommation électrique ultra-réaliste pour la Malaisie"""
        pattern = self.consumption_patterns[building_class]
        
        hour = timestamp.hour
        day_of_week = timestamp.dayofweek  # 0=Lundi, 6=Dimanche
        month = timestamp.month
        is_weekend = day_of_week >= 5
        
        # Facteur climatique pour la Malaisie (climat tropical)
        climate_factor = 1.0
        if 11 <= hour <= 16:  # Heures les plus chaudes
            climate_factor = 1.4 + 0.3 * random.random()
        elif 17 <= hour <= 21:  # Soirée encore chaude
            climate_factor = 1.2 + 0.2 * random.random()
        elif 22 <= hour <= 6:  # Nuit plus fraîche
            climate_factor = 0.8 + 0.3 * random.random()
        
        # 1. Facteur horaire adapté au climat tropical malaisien
        if building_class == 'Residential':
            if 6 <= hour <= 8:  # Matin avant la chaleur
                hour_factor = 0.6 + 0.3 * np.sin((hour - 6) * np.pi / 2)
            elif 19 <= hour <= 23:  # Soir après la chaleur du jour
                hour_factor = 0.7 + 0.3 * np.sin((hour - 19) * np.pi / 4)
            elif 11 <= hour <= 16:  # Journée chaude - clim à fond
                hour_factor = 0.8 + 0.4 * random.random()
            elif 0 <= hour <= 5:  # Nuit
                hour_factor = pattern['night_factor'] * (0.8 + 0.4 * random.random())
            else:
                hour_factor = 0.4 + 0.3 * random.random()
                
        elif building_class in ['Commercial', 'Office', 'Retail']:
            if 8 <= hour <= 19:
                base_factor = 0.6 + 0.4 * np.sin((hour - 8) * np.pi / 11)
                if 11 <= hour <= 16:  # Climatisation intensive
                    hour_factor = base_factor * 1.3
                else:
                    hour_factor = base_factor
            elif 20 <= hour <= 22:  # Fermeture progressive
                hour_factor = 0.2 + 0.3 * random.random()
            else:
                hour_factor = pattern['night_factor'] * (0.5 + 0.5 * random.random())
                
        elif building_class in ['Industrial', 'Factory']:
            if 22 <= hour or hour <= 6:  # Nuit - tarif préférentiel
                hour_factor = 0.9 + 0.1 * random.random()
            elif 7 <= hour <= 10:  # Matin
                hour_factor = 0.8 + 0.2 * random.random()
            elif 11 <= hour <= 16:  # Éviter le pic (coût électricité)
                hour_factor = 0.5 + 0.3 * random.random()
            else:  # Fin d'après-midi/soirée
                hour_factor = 0.7 + 0.3 * random.random()
                
        elif building_class == 'Hospital':
            base_factor = 0.8 + 0.2 * random.random()
            if 11 <= hour <= 16:  # Climatisation renforcée
                hour_factor = base_factor * 1.2
            else:
                hour_factor = base_factor
                
        elif building_class == 'School':
            if 7 <= hour <= 15 and not is_weekend:
                if 11 <= hour <= 15:  # Clim pendant les heures chaudes
                    hour_factor = 0.8 + 0.4 * random.random()
                else:
                    hour_factor = 0.6 + 0.3 * random.random()
            else:
                hour_factor = 0.05 + 0.1 * random.random()
                
        elif building_class == 'Restaurant':
            if 18 <= hour <= 23:  # Pic du soir
                hour_factor = 0.8 + 0.4 * random.random()
            elif 7 <= hour <= 11:  # Service matin/déjeuner
                hour_factor = 0.6 + 0.3 * random.random()
            elif 12 <= hour <= 17:  # Fermeture après-midi (chaleur)
                hour_factor = 0.2 + 0.3 * random.random()
            else:
                hour_factor = pattern['night_factor'] + 0.2 * random.random()
                
        else:
            # Pattern par défaut adapté au climat tropical
            if 8 <= hour <= 18:
                hour_factor = 0.6 + 0.4 * random.random()
            else:
                hour_factor = pattern['night_factor'] + 0.3 * random.random()
        
        # 2. Facteur hebdomadaire adapté à la culture malaisienne
        if building_class in ['Commercial', 'Office']:
            # Vendredi après-midi moins actif (prière du vendredi)
            if day_of_week == 4 and hour >= 12:  # Vendredi après-midi
                week_factor = 0.7
            elif is_weekend:
                week_factor = 0.4  # Weekend moins actif
            else:
                week_factor = 1.0
        elif building_class == 'School':
            # Écoles fermées vendredi après-midi et weekend
            if (day_of_week == 4 and hour >= 12) or is_weekend:
                week_factor = 0.1
            else:
                week_factor = 1.0
        elif building_class == 'Residential':
            # Plus de consommation le weekend et vendredi après-midi
            if is_weekend or (day_of_week == 4 and hour >= 12):
                week_factor = 1.2
            else:
                week_factor = 1.0
        elif building_class in ['Hospital', 'Hotel']:
            week_factor = 1.0  # Constant toute la semaine
        else:
            week_factor = 0.8 if is_weekend else 1.0
        
        # 3. Facteur saisonnier pour la Malaisie
        if month in [11, 12, 1, 2]:  # Saison des pluies
            season_factor = 0.9 + 0.2 * random.random()  # Moins de clim
        elif month in [5, 6, 7, 8]:  # Saison sèche chaude
            season_factor = 1.3 + 0.4 * random.random()  # Plus de clim
        elif month in [3, 4]:  # Période de transition chaude
            season_factor = 1.2 + 0.3 * random.random()
        else:  # Octobre, septembre - variable
            season_factor = 1.0 + 0.3 * random.random()
        
        # 4. Facteur selon la taille de la ville
        if location_info:
            if location_info['population'] > 500000:  # Grandes villes
                city_factor = 1.2 + 0.2 * random.random()  # Plus développé
            elif location_info['population'] > 200000:  # Villes moyennes
                city_factor = 1.0 + 0.2 * random.random()
            else:  # Petites villes
                city_factor = 0.8 + 0.3 * random.random()  # Moins développé
        else:
            city_factor = 1.0
        
        # 5. Calcul de la consommation de base
        base_consumption = pattern['base'] + (pattern['peak'] - pattern['base']) * hour_factor
        
        # 6. Application de tous les facteurs
        consumption = (base_consumption * week_factor * season_factor * 
                      climate_factor * city_factor)
        
        # 7. Ajout de bruit réaliste
        noise = np.random.normal(0, pattern['variance'] * 0.15)
        consumption = max(0, consumption + noise)
        
        # 8. Événements spéciaux spécifiques à la Malaisie
        if random.random() < 0.003:  # 0.3% de chance de coupure de courant
            consumption = 0.0
        elif random.random() < 0.015:  # 1.5% de chance de pic (orage, etc.)
            consumption *= 1.4 + 0.8 * random.random()
        
        # 9. Période de Ramadan (consommation différente)
        if month in [3, 4] and building_class == 'Residential':
            if 4 <= hour <= 17:  # Jeûne pendant la journée
                consumption *= 0.6
            elif 18 <= hour <= 23:  # Iftar et activités nocturnes
                consumption *= 1.4
        
        return round(consumption, 3)
    
    def generate_timeseries_data(self, buildings_df, start_date, end_date, freq='30T'):
        """Génère les données de séries temporelles réalistes pour la Malaisie"""
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        timeseries_data = []
        
        print(f"Génération de {len(date_range)} points temporels pour {len(buildings_df)} bâtiments en Malaisie...")
        
        for idx, (_, building) in enumerate(buildings_df.iterrows()):
            if idx % 10 == 0:
                print(f"Traitement bâtiment {idx+1}/{len(buildings_df)} - {building['location']}")
                
            building_class = building['building_class']
            unique_id = building['unique_id']
            location_name = building['location']
            
            # Gérer le cas où la localisation pourrait être personnalisée
            if location_name in self.malaysia_locations:
                location_info = self.malaysia_locations[location_name]
            else:
                # Localisation personnalisée - utiliser les données du bâtiment
                location_info = {
                    'population': building.get('population', 100000),
                    'state': building.get('state', 'Custom'),
                    'region': building.get('region', 'Custom')
                }
            
            for timestamp in date_range:
                consumption = self.calculate_realistic_consumption(
                    building_class, timestamp, location_info
                )
                
                timeseries_data.append({
                    'unique_id': unique_id,
                    'timestamp': timestamp,
                    'y': consumption
                })
        
        return pd.DataFrame(timeseries_data)
    
    def get_unique_values(self):
        """Retourne les valeurs uniques pour les listes déroulantes"""
        cities = list(self.malaysia_locations.keys())
        states = list(set([info['state'] for info in self.malaysia_locations.values()]))
        regions = list(set([info['region'] for info in self.malaysia_locations.values()]))
        
        return {
            'cities': sorted(cities),
            'states': sorted(states),
            'regions': sorted(regions)
        }

# Instance globale
generator = ElectricityDataGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        num_buildings = data.get('num_buildings', 10)
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', '2024-01-07')
        freq = data.get('freq', '30T')
        
        # Gestion du filtrage géographique
        location_filter = data.get('location_filter')
        custom_location_data = data.get('custom_location')
        
        # Préparer la localisation personnalisée si fournie
        custom_location = None
        if custom_location_data and custom_location_data.get('name'):
            custom_loc_info = {
                'population': custom_location_data.get('population', 100000),
                'state': custom_location_data.get('state', 'Custom'),
                'region': custom_location_data.get('region', 'Custom')
            }
            custom_location = {custom_location_data['name']: custom_loc_info}
        
        # Générer les données avec filtrage
        buildings_df = generator.generate_building_metadata(
            num_buildings, location_filter, custom_location
        )
        timeseries_df = generator.generate_timeseries_data(buildings_df, start_date, end_date, freq)
        
        # Calculer les statistiques
        stats = {
            'total_records': len(timeseries_df),
            'buildings_count': num_buildings,
            'unique_locations': len(buildings_df['location'].unique()),
            'avg_consumption': round(timeseries_df['y'].mean(), 2),
            'max_consumption': round(timeseries_df['y'].max(), 2),
            'min_consumption': round(timeseries_df['y'].min(), 2),
            'zero_values': int((timeseries_df['y'] == 0).sum())
        }
        
        # Créer un résumé des localisations (format sérialisable)
        location_counts = buildings_df.groupby(['location', 'state', 'region']).size().reset_index(name='count')
        location_summary = []
        for _, row in location_counts.iterrows():
            location_summary.append({
                'location': row['location'],
                'state': row['state'],
                'region': row['region'],
                'count': int(row['count'])
            })
        
        return jsonify({
            'success': True,
            'buildings': buildings_df.to_dict('records'),
            'timeseries': timeseries_df.head(500).to_dict('records'),
            'stats': stats,
            'location_summary': location_summary
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erreur de génération: {error_details}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        num_buildings = data.get('num_buildings', 10)
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', '2024-01-31')
        freq = data.get('freq', '30T')
        
        # Gestion du filtrage géographique
        location_filter = data.get('location_filter')
        custom_location_data = data.get('custom_location')
        
        # Préparer la localisation personnalisée si fournie
        custom_location = None
        if custom_location_data and custom_location_data.get('name'):
            custom_loc_info = {
                'population': custom_location_data.get('population', 100000),
                'state': custom_location_data.get('state', 'Custom'),
                'region': custom_location_data.get('region', 'Custom')
            }
            custom_location = {custom_location_data['name']: custom_loc_info}
        
        # Générer les données avec filtrage
        buildings_df = generator.generate_building_metadata(
            num_buildings, location_filter, custom_location
        )
        timeseries_df = generator.generate_timeseries_data(buildings_df, start_date, end_date, freq)
        
        # Créer le dossier de sortie s'il n'existe pas
        output_dir = 'generated_data'
        os.makedirs(output_dir, exist_ok=True)
        
        # Noms des fichiers avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Définir le nom selon le type de génération
        if custom_location:
            location_name = list(custom_location.keys())[0].replace(' ', '_').replace('/', '_')
            buildings_filename = f'{output_dir}/malaysia_buildings_{location_name}_{timestamp}.parquet'
            timeseries_filename = f'{output_dir}/malaysia_demand_{location_name}_{timestamp}.parquet'
        elif location_filter and any(v != 'all' for v in [location_filter.get('city', 'all'), location_filter.get('state', 'all'), location_filter.get('region', 'all')]):
            filter_name = "filtered"
            if location_filter.get('city') and location_filter['city'] != 'all':
                filter_name = location_filter['city'].replace(' ', '_').replace('/', '_')
            elif location_filter.get('state') and location_filter['state'] != 'all':
                filter_name = location_filter['state'].replace(' ', '_').replace('/', '_')
            elif location_filter.get('region') and location_filter['region'] != 'all':
                filter_name = location_filter['region'].replace(' ', '_').replace('/', '_')
            
            buildings_filename = f'{output_dir}/malaysia_buildings_{filter_name}_{timestamp}.parquet'
            timeseries_filename = f'{output_dir}/malaysia_demand_{filter_name}_{timestamp}.parquet'
        else:
            buildings_filename = f'{output_dir}/malaysia_buildings_{timestamp}.parquet'
            timeseries_filename = f'{output_dir}/malaysia_demand_{timestamp}.parquet'
        
        # Sauvegarder les fichiers
        buildings_df.to_parquet(buildings_filename, index=False)
        timeseries_df.to_parquet(timeseries_filename, index=False)
        
        # Créer le résumé des localisations
        location_summary = buildings_df.groupby(['location', 'state', 'region']).size().reset_index(name='count')
        location_text = "\n".join([
            f"   • {row['location']} ({row['state']}) - {row['count']} bâtiments"
            for _, row in location_summary.iterrows()
        ])
        
        message = f"""📁 Fichiers générés pour la MALAISIE:
        
🏢 Métadonnées: {buildings_filename}
   - {len(buildings_df)} bâtiments répartis dans {buildings_df['location'].nunique()} villes
   
🗺️ Répartition géographique:
{location_text}
        
⚡ Séries temporelles: {timeseries_filename}
   - {len(timeseries_df):,} observations
   - Période: {start_date} à {end_date}
   - Fréquence: {freq}
   - Patterns climatiques tropicaux intégrés
        
📊 Statistiques:
   - Consommation moyenne: {timeseries_df['y'].mean():.2f} kWh
   - Consommation maximale: {timeseries_df['y'].max():.2f} kWh
   - Valeurs nulles: {(timeseries_df['y'] == 0).sum()} ({(timeseries_df['y'] == 0).sum() / len(timeseries_df) * 100:.1f}%)
   
🌴 Spécificités Malaisie incluses:
   - Climat tropical avec pics de climatisation
   - Patterns culturels (Vendredi, Ramadan)
   - Distribution basée sur population réelle"""
        
        return jsonify({
            'success': True,
            'message': message,
            'files': {
                'buildings': buildings_filename,
                'timeseries': timeseries_filename
            },
            'location_summary': [
                {
                    'location': row['location'],
                    'state': row['state'], 
                    'region': row['region'],
                    'count': int(row['count'])
                }
                for _, row in location_summary.iterrows()
            ]
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erreur de téléchargement: {error_details}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/sample')
def sample():
    try:
        # Générer un petit échantillon pour démonstration
        buildings_df = generator.generate_building_metadata(5)
        timeseries_df = generator.generate_timeseries_data(buildings_df, '2024-01-01', '2024-01-02', '30T')
        
        stats = {
            'total_records': len(timeseries_df),
            'buildings_count': len(buildings_df),
            'avg_consumption': round(timeseries_df['y'].mean(), 2),
            'max_consumption': round(timeseries_df['y'].max(), 2),
            'min_consumption': round(timeseries_df['y'].min(), 2),
            'zero_values': int((timeseries_df['y'] == 0).sum())
        }
        
        return jsonify({
            'success': True,
            'buildings': buildings_df.to_dict('records'),
            'timeseries': timeseries_df.to_dict('records'),
            'stats': stats,
            'building_classes': generator.building_classes,
            'malaysia_locations': list(generator.malaysia_locations.keys())
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """API pour obtenir des statistiques sur les types de données générables"""
    return jsonify({
        'success': True,
        'building_classes': generator.building_classes,
        'malaysia_locations': {
            name: {
                'population': info['population'],
                'state': info['state'],
                'region': info['region']
            } for name, info in generator.malaysia_locations.items()
        },
        'consumption_patterns': {
            class_name: {
                'description': f"Consommation de base: {pattern['base']} kWh, Pic: {pattern['peak']} kWh",
                'base': pattern['base'],
                'peak': pattern['peak']
            } for class_name, pattern in generator.consumption_patterns.items()
        },
        'supported_frequencies': ['30T', '1H', '15T', '5T'],
        'malaysia_specific_features': [
            'Climat tropical avec pics de climatisation',
            'Patterns culturels (Vendredi après-midi, Ramadan)',
            'Saison des pluies vs saison sèche',
            'Distribution basée sur la population réelle des villes',
            'Coordonnées GPS précises de Malaisie',
            'Tarification électrique par tranche horaire',
            'Événements climatiques (orages tropicaux)',
            f'{len(generator.malaysia_locations)} villes de toutes tailles'
        ]
    })

if __name__ == '__main__':
    print("🇲🇾 Démarrage du générateur de données électriques pour la MALAISIE...")
    print(f"🏙️ {len(generator.malaysia_locations)} villes de Malaisie disponibles")
    print("🌆 Principales villes:", ", ".join(list(generator.malaysia_locations.keys())[:8]) + "...")
    print("📊 Types de bâtiments supportés:", ", ".join(generator.building_classes))
    print("🌴 Caractéristiques spéciales: Climat tropical, Ramadan, Saisons des pluies")
    print("⚡ Serveur démarré sur http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)