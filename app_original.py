from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid
import os
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import sécurisé du distributeur de bâtiments
try:
    from building_distribution import BuildingDistributor
    BUILDING_DISTRIBUTOR_AVAILABLE = True
    logger.info("✅ BuildingDistributor importé avec succès")
except ImportError as e:
    logger.error(f"❌ Erreur import BuildingDistributor: {e}")
    BUILDING_DISTRIBUTOR_AVAILABLE = False

# Import du système de validation avec gestion d'erreurs
VALIDATION_ENABLED = False  # Initialisation par défaut
try:
    from integration_validation import IntegratedValidator
    VALIDATION_ENABLED = True
    logger.info("✅ Système de validation chargé")
except ImportError as e:
    logger.warning(f"⚠️ Validation non disponible: {e}")
    VALIDATION_ENABLED = False

app = Flask(__name__)


class MockBuildingDistributor:
    """Distributeur mock en cas d'absence du module building_distribution"""
    
    def __init__(self):
        # Distribution basique par défaut
        self.basic_distribution = {
            'Residential': 0.65,
            'Commercial': 0.12,
            'Industrial': 0.08,
            'Office': 0.05,
            'Retail': 0.04,
            'School': 0.03,
            'Hospital': 0.01,
            'Clinic': 0.02
        }
    
    def calculate_building_distribution(self, city_name, population, region, total_buildings):
        """Distribution basique selon la population"""
        distribution = {}
        
        # Ajuster selon la taille de la ville
        if population > 500000:  # Grande ville
            distribution = {
                'Residential': 0.60,
                'Commercial': 0.15,
                'Office': 0.08,
                'Industrial': 0.05,
                'Retail': 0.05,
                'School': 0.03,
                'Hospital': 0.015,
                'Clinic': 0.025,
                'Hotel': 0.02
            }
        elif population > 100000:  # Ville moyenne
            distribution = {
                'Residential': 0.70,
                'Commercial': 0.10,
                'Industrial': 0.08,
                'Retail': 0.04,
                'School': 0.04,
                'Hospital': 0.01,
                'Clinic': 0.02,
                'Hotel': 0.01
            }
        else:  # Petite ville
            distribution = {
                'Residential': 0.75,
                'Commercial': 0.08,
                'Industrial': 0.05,
                'Retail': 0.06,
                'School': 0.04,
                'Clinic': 0.02
            }
        
        # Convertir en nombres
        building_counts = {}
        for building_type, percentage in distribution.items():
            count = max(0, int(percentage * total_buildings))
            building_counts[building_type] = count
        
        # Ajuster pour avoir le total exact
        total_assigned = sum(building_counts.values())
        if total_assigned < total_buildings:
            building_counts['Residential'] += (total_buildings - total_assigned)
        
        return building_counts


class ElectricityDataGenerator:
    """Générateur de données électriques réalistes pour la Malaisie"""
    
    def __init__(self):
        # Instance du distributeur de bâtiments (avec fallback)
        if BUILDING_DISTRIBUTOR_AVAILABLE:
            self.building_distributor = BuildingDistributor()
            logger.info("🏗️ BuildingDistributor chargé")
        else:
            self.building_distributor = MockBuildingDistributor()
            logger.warning("🏗️ MockBuildingDistributor utilisé (distribution basique)")
        
        # Instance du validateur (si disponible)
        self.validation_enabled = VALIDATION_ENABLED  # Stocker localement
        if self.validation_enabled:
            try:
                self.validator = IntegratedValidator()
                logger.info("🔍 Validateur intégré activé")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation validateur: {e}")
                self.validator = None
                self.validation_enabled = False
        else:
            self.validator = None
            logger.warning("⚠️ Validateur non disponible - fonctionnement en mode standard")
        
        # Types de bâtiments supportés
        self.building_classes = [
            'Residential', 'Commercial', 'Industrial', 'Office', 
            'Retail', 'Hospital', 'Clinic', 'School', 'Hotel', 'Restaurant',
            'Warehouse', 'Factory', 'Apartment'
        ]
        
        # Localisations réelles de Malaisie avec populations
        self.malaysia_locations = {
            # Métropoles et grandes villes
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
            
            # Villes plus petites
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
            
            # Villes côtières et touristiques
            'Langkawi': {'population': 65000, 'state': 'Kedah', 'region': 'Northern'},
            'Port Klang': {'population': 180000, 'state': 'Selangor', 'region': 'Central'},
            'Cyberjaya': {'population': 65000, 'state': 'Selangor', 'region': 'Central'},
            'Kajang': {'population': 342000, 'state': 'Selangor', 'region': 'Central'},
            'Cheras': {'population': 381000, 'state': 'Selangor', 'region': 'Central'},
            'Puchong': {'population': 388000, 'state': 'Selangor', 'region': 'Central'}
        }
        
        # Fuseau horaire de la Malaisie
        self.timezones = ['Asia/Kuala_Lumpur']
        
        # Patterns de consommation réalistes pour climat tropical
        self.consumption_patterns = {
            'Residential': {'base': 0.5, 'peak': 12.0, 'variance': 2.5, 'night_factor': 0.3},
            'Commercial': {'base': 5.0, 'peak': 80.0, 'variance': 15.0, 'night_factor': 0.2},
            'Industrial': {'base': 20.0, 'peak': 200.0, 'variance': 40.0, 'night_factor': 0.7},
            'Office': {'base': 3.0, 'peak': 45.0, 'variance': 8.0, 'night_factor': 0.1},
            'Retail': {'base': 2.0, 'peak': 35.0, 'variance': 6.0, 'night_factor': 0.15},
            'Hospital': {'base': 25.0, 'peak': 70.0, 'variance': 12.0, 'night_factor': 0.8},
            'Clinic': {'base': 2.0, 'peak': 15.0, 'variance': 3.0, 'night_factor': 0.1},
            'School': {'base': 1.0, 'peak': 25.0, 'variance': 5.0, 'night_factor': 0.05},
            'Hotel': {'base': 8.0, 'peak': 40.0, 'variance': 8.0, 'night_factor': 0.6},
            'Restaurant': {'base': 3.0, 'peak': 60.0, 'variance': 15.0, 'night_factor': 0.2},
            'Warehouse': {'base': 2.0, 'peak': 30.0, 'variance': 8.0, 'night_factor': 0.4},
            'Factory': {'base': 30.0, 'peak': 150.0, 'variance': 35.0, 'night_factor': 0.6},
            'Apartment': {'base': 1.0, 'peak': 15.0, 'variance': 4.0, 'night_factor': 0.4}
        }
    
    def generate_unique_id(self):
        """Génère un ID unique compatible avec le format existant"""
        return ''.join(random.choices('abcdef0123456789', k=16))
    
    def generate_coordinates(self, location):
        """Génère des coordonnées GPS réalistes pour la Malaisie"""
        # Coordonnées précises des principales villes
        coords = {
            'Kuala Lumpur': {'lat': (3.1319, 3.1681), 'lon': (101.6841, 101.7381)},
            'George Town': {'lat': (5.4000, 5.4300), 'lon': (100.3000, 100.3300)},
            'Ipoh': {'lat': (4.5833, 4.6033), 'lon': (101.0833, 101.1033)},
            'Shah Alam': {'lat': (3.0667, 3.1167), 'lon': (101.4833, 101.5333)},
            'Petaling Jaya': {'lat': (3.1073, 3.1273), 'lon': (101.6063, 101.6263)},
            'Johor Bahru': {'lat': (1.4833, 1.5033), 'lon': (103.7333, 103.7533)},
            'Langkawi': {'lat': (6.3167, 6.3367), 'lon': (99.8167, 99.8367)},
            'Kota Kinabalu': {'lat': (5.9667, 5.9867), 'lon': (116.0667, 116.0867)},
            'Kuching': {'lat': (1.5333, 1.5533), 'lon': (110.3333, 110.3533)},
            'Cyberjaya': {'lat': (2.9167, 2.9367), 'lon': (101.6333, 101.6533)}
        }
        
        if location in coords:
            lat_range = coords[location]['lat']
            lon_range = coords[location]['lon']
            lat = round(random.uniform(lat_range[0], lat_range[1]), 6)
            lon = round(random.uniform(lon_range[0], lon_range[1]), 6)
        else:
            # Coordonnées par défaut pour la Malaisie
            lat = round(random.uniform(1.0, 7.0), 6)
            lon = round(random.uniform(99.5, 119.5), 6)
        
        return lat, lon
    
    def generate_building_metadata(self, num_buildings=100, location_filter=None, custom_location=None):
        """Génère les métadonnées des bâtiments avec distribution réaliste"""
        buildings = []
        
        try:
            # Déterminer les localisations disponibles
            if custom_location:
                available_locations = {custom_location['name']: custom_location}
            elif location_filter:
                available_locations = self._filter_locations(location_filter)
            else:
                available_locations = self.malaysia_locations
            
            if not available_locations:
                raise ValueError("Aucune localisation ne correspond aux critères de filtrage")
            
            # Calculer la répartition des bâtiments par ville (pondérée par population)
            city_building_counts = self._distribute_buildings_by_city(available_locations, num_buildings)
            
            # Générer les bâtiments pour chaque ville
            building_id_counter = 1
            
            for location, building_count in city_building_counts.items():
                if building_count <= 0:
                    continue
                
                location_info = available_locations[location]
                
                # Obtenir la distribution réaliste pour cette ville
                building_distribution = self.building_distributor.calculate_building_distribution(
                    location, location_info['population'], location_info['region'], building_count
                )
                
                # Créer les bâtiments selon la distribution
                building_types_list = self._create_building_types_list(building_distribution)
                
                # Générer les bâtiments individuels
                for i in range(building_count):
                    building = self._create_building(
                        location, location_info, building_types_list, i, building_id_counter
                    )
                    buildings.append(building)
                    building_id_counter += 1
            
            # Afficher le résumé de génération
            self._print_generation_summary(buildings)
            
            return pd.DataFrame(buildings)
            
        except Exception as e:
            logger.error(f"Erreur génération métadonnées: {e}")
            # Génération basique en cas d'erreur
            return self._generate_basic_buildings(num_buildings)
    
    def _filter_locations(self, location_filter):
        """Filtre les localisations selon les critères"""
        available_locations = {}
        
        for name, info in self.malaysia_locations.items():
            include = True
            
            # Filtres géographiques
            if location_filter.get('city') and location_filter['city'] != 'all':
                if name != location_filter['city']:
                    include = False
            
            if location_filter.get('state') and location_filter['state'] != 'all':
                if info['state'] != location_filter['state']:
                    include = False
            
            if location_filter.get('region') and location_filter['region'] != 'all':
                if info['region'] != location_filter['region']:
                    include = False
            
            # Filtres de population
            if location_filter.get('population_min'):
                if info['population'] < int(location_filter['population_min']):
                    include = False
            
            if location_filter.get('population_max'):
                if info['population'] > int(location_filter['population_max']):
                    include = False
            
            if include:
                available_locations[name] = info
        
        return available_locations
    
    def _distribute_buildings_by_city(self, available_locations, num_buildings):
        """Distribue les bâtiments aux villes selon leur population"""
        locations = list(available_locations.keys())
        populations = [available_locations[loc]['population'] for loc in locations]
        total_pop = sum(populations)
        weights = [pop / total_pop for pop in populations]
        
        # Distribuer les bâtiments
        city_building_counts = {}
        for i, location in enumerate(locations):
            count = max(1, int(num_buildings * weights[i]))
            city_building_counts[location] = count
        
        # Ajuster pour avoir exactement num_buildings
        total_assigned = sum(city_building_counts.values())
        if total_assigned != num_buildings:
            largest_city = max(locations, key=lambda x: available_locations[x]['population'])
            city_building_counts[largest_city] += (num_buildings - total_assigned)
        
        return city_building_counts
    
    def _create_building_types_list(self, building_distribution):
        """Crée une liste ordonnée des types de bâtiments"""
        building_types_list = []
        for building_type, count in building_distribution.items():
            building_types_list.extend([building_type] * count)
        
        # Mélanger pour éviter les patterns
        random.shuffle(building_types_list)
        return building_types_list
    
    def _create_building(self, location, location_info, building_types_list, index, building_id_counter):
        """Crée un bâtiment individuel"""
        unique_id = self.generate_unique_id()
        
        # Sélectionner le type de bâtiment
        if index < len(building_types_list):
            building_class = building_types_list[index]
        else:
            building_class = 'Residential'  # Fallback
        
        lat, lon = self.generate_coordinates(location)
        
        # Taille du cluster basée sur la population
        cluster_multiplier = min(location_info['population'] / 100000, 5.0)
        cluster_size = random.randint(1, max(1, int(50 * cluster_multiplier)))
        
        return {
            'unique_id': unique_id,
            'dataset': 'malaysia_electricity_v1',
            'building_id': f'MY_{location_info["state"][:3].upper()}_{building_id_counter:06d}',
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
    
    def _print_generation_summary(self, buildings):
        """Affiche un résumé de la génération"""
        try:
            # Résumé par ville
            city_counts = {}
            for building in buildings:
                city = building['location']
                city_counts[city] = city_counts.get(city, 0) + 1
            
            logger.info("🏙️ Répartition des bâtiments par ville:")
            for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {city}: {count} bâtiments")
            
            # Distribution finale des types
            type_counts = {}
            for building in buildings:
                building_type = building['building_class']
                type_counts[building_type] = type_counts.get(building_type, 0) + 1
            
            logger.info(f"\n📋 Distribution finale totale ({len(buildings)} bâtiments):")
            for building_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(buildings)) * 100
                logger.info(f"  - {building_type}: {count} ({percentage:.1f}%)")
                
        except Exception as e:
            logger.error(f"Erreur affichage résumé: {e}")
    
    def _generate_basic_buildings(self, num_buildings):
        """Génération basique en cas d'erreur"""
        logger.warning("🔄 Génération basique activée")
        
        buildings = []
        basic_types = ['Residential', 'Commercial', 'Industrial', 'Office', 'Retail']
        basic_location = 'Kuala Lumpur'
        
        for i in range(num_buildings):
            unique_id = self.generate_unique_id()
            building_class = random.choice(basic_types)
            lat, lon = self.generate_coordinates(basic_location)
            
            building = {
                'unique_id': unique_id,
                'dataset': 'malaysia_electricity_basic',
                'building_id': f'MY_BASIC_{i+1:06d}',
                'location_id': f'MY_00001',
                'latitude': lat,
                'longitude': lon,
                'location': basic_location,
                'state': 'Federal Territory',
                'region': 'Central',
                'population': 1800000,
                'timezone': 'Asia/Kuala_Lumpur',
                'building_class': building_class,
                'cluster_size': random.randint(1, 50),
                'freq': '30T'
            }
            buildings.append(building)
        
        return pd.DataFrame(buildings)
    
    def calculate_realistic_consumption(self, building_class, timestamp, location_info=None):
        """Calcule une consommation électrique réaliste pour le climat tropical malaisien"""
        
        # Vérifier si le type de bâtiment existe
        if building_class not in self.consumption_patterns:
            logger.warning(f"Type de bâtiment '{building_class}' non trouvé, utilisation de Residential")
            building_class = 'Residential'
        
        pattern = self.consumption_patterns[building_class]
        
        # Variables temporelles
        hour = timestamp.hour
        day_of_week = timestamp.dayofweek  # 0=Lundi, 6=Dimanche
        month = timestamp.month
        is_weekend = day_of_week >= 5
        
        # Facteur climatique tropical - très important en Malaisie
        climate_factor = 1.0
        if 11 <= hour <= 16:  # Heures les plus chaudes - climatisation intensive
            climate_factor = 1.4 + 0.3 * random.random()
        elif 17 <= hour <= 21:  # Soirée encore chaude
            climate_factor = 1.2 + 0.2 * random.random()
        elif 22 <= hour <= 6:  # Nuit plus fraîche
            climate_factor = 0.8 + 0.3 * random.random()
        
        # Facteur horaire spécialisé par type de bâtiment
        hour_factor = self._calculate_hour_factor(building_class, hour, is_weekend)
        
        # Facteur hebdomadaire adapté à la culture malaisienne
        week_factor = self._calculate_week_factor(building_class, day_of_week, hour)
        
        # Facteur saisonnier pour la Malaisie
        season_factor = self._calculate_season_factor(month)
        
        # Facteur selon la taille de la ville
        city_factor = self._calculate_city_factor(location_info)
        
        # Calcul de la consommation de base
        base_consumption = pattern['base'] + (pattern['peak'] - pattern['base']) * hour_factor
        
        # Application de tous les facteurs
        consumption = (base_consumption * week_factor * season_factor * 
                      climate_factor * city_factor)
        
        # Ajout de bruit réaliste
        noise = np.random.normal(0, pattern['variance'] * 0.15)
        consumption = max(0, consumption + noise)
        
        # Événements spéciaux pour la Malaisie
        consumption = self._apply_special_events(consumption, month, hour, building_class)
        
        return round(consumption, 3)
    
    def _calculate_hour_factor(self, building_class, hour, is_weekend):
        """Calcule le facteur horaire selon le type de bâtiment"""
        
        pattern = self.consumption_patterns[building_class]
        
        if building_class == 'Residential':
            if 6 <= hour <= 8:  # Matin
                return 0.6 + 0.3 * np.sin((hour - 6) * np.pi / 2)
            elif 19 <= hour <= 23:  # Soir
                return 0.7 + 0.3 * np.sin((hour - 19) * np.pi / 4)
            elif 11 <= hour <= 16:  # Journée chaude
                return 0.8 + 0.4 * random.random()
            elif 0 <= hour <= 5:  # Nuit
                return pattern['night_factor'] * (0.8 + 0.4 * random.random())
            else:
                return 0.4 + 0.3 * random.random()
        
        elif building_class in ['Commercial', 'Office', 'Retail']:
            if 8 <= hour <= 19:
                base_factor = 0.6 + 0.4 * np.sin((hour - 8) * np.pi / 11)
                if 11 <= hour <= 16:  # Climatisation intensive
                    return base_factor * 1.3
                else:
                    return base_factor
            elif 20 <= hour <= 22:  # Fermeture progressive
                return 0.2 + 0.3 * random.random()
            else:
                return pattern['night_factor'] * (0.5 + 0.5 * random.random())
        
        elif building_class in ['Industrial', 'Factory']:
            if 22 <= hour or hour <= 6:  # Nuit - tarif préférentiel
                return 0.9 + 0.1 * random.random()
            elif 7 <= hour <= 10:  # Matin
                return 0.8 + 0.2 * random.random()
            elif 11 <= hour <= 16:  # Éviter le pic tarifaire
                return 0.5 + 0.3 * random.random()
            else:  # Fin d'après-midi/soirée
                return 0.7 + 0.3 * random.random()
        
        elif building_class in ['Hospital', 'Clinic']:
            base_factor = 0.8 + 0.2 * random.random()
            if building_class == 'Hospital':
                # Hôpitaux - fonctionnement constant
                if 11 <= hour <= 16:  # Climatisation renforcée
                    return base_factor * 1.2
                else:
                    return base_factor
            else:
                # Cliniques - heures d'ouverture
                if 7 <= hour <= 19:
                    if 11 <= hour <= 16:  # Clim pendant heures chaudes
                        return base_factor * 1.3
                    else:
                        return base_factor
                else:
                    return 0.1 + 0.1 * random.random()
        
        elif building_class == 'School':
            if 7 <= hour <= 15 and not is_weekend:
                if 11 <= hour <= 15:  # Clim pendant heures chaudes
                    return 0.8 + 0.4 * random.random()
                else:
                    return 0.6 + 0.3 * random.random()
            else:
                return 0.05 + 0.1 * random.random()
        
        else:
            # Pattern par défaut
            if 8 <= hour <= 18:
                return 0.6 + 0.4 * random.random()
            else:
                return pattern['night_factor'] + 0.3 * random.random()
    
    def _calculate_week_factor(self, building_class, day_of_week, hour):
        """Calcule le facteur hebdomadaire selon la culture malaisienne"""
        
        is_weekend = day_of_week >= 5
        
        if building_class in ['Commercial', 'Office', 'Clinic']:
            # Vendredi après-midi moins actif (prière du vendredi)
            if day_of_week == 4 and hour >= 12:  # Vendredi après-midi
                return 0.7
            elif is_weekend:
                return 0.4  # Weekend moins actif
            else:
                return 1.0
        elif building_class == 'School':
            # Écoles fermées vendredi après-midi et weekend
            if (day_of_week == 4 and hour >= 12) or is_weekend:
                return 0.1
            else:
                return 1.0
        elif building_class == 'Residential':
            # Plus de consommation le weekend et vendredi après-midi
            if is_weekend or (day_of_week == 4 and hour >= 12):
                return 1.2
            else:
                return 1.0
        elif building_class in ['Hospital', 'Hotel']:
            return 1.0  # Constant toute la semaine
        else:
            return 0.8 if is_weekend else 1.0
    
    def _calculate_season_factor(self, month):
        """Calcule le facteur saisonnier pour la Malaisie"""
        
        if month in [11, 12, 1, 2]:  # Saison des pluies
            return 0.9 + 0.2 * random.random()  # Moins de clim
        elif month in [5, 6, 7, 8]:  # Saison sèche chaude
            return 1.3 + 0.4 * random.random()  # Plus de clim
        elif month in [3, 4]:  # Période de transition chaude
            return 1.2 + 0.3 * random.random()
        else:  # Octobre, septembre - variable
            return 1.0 + 0.3 * random.random()
    
    def _calculate_city_factor(self, location_info):
        """Calcule le facteur selon la taille de la ville"""
        
        if not location_info:
            return 1.0
        
        population = location_info.get('population', 100000)
        
        if population > 500000:  # Grandes villes
            return 1.2 + 0.2 * random.random()  # Plus développé
        elif population > 200000:  # Villes moyennes
            return 1.0 + 0.2 * random.random()
        else:  # Petites villes
            return 0.8 + 0.3 * random.random()  # Moins développé
    
    def _apply_special_events(self, consumption, month, hour, building_class):
        """Applique les événements spéciaux spécifiques à la Malaisie"""
        
        # Coupures de courant occasionnelles
        if random.random() < 0.003:  # 0.3% de chance
            return 0.0
        
        # Pics lors d'orages tropicaux
        elif random.random() < 0.015:  # 1.5% de chance
            consumption *= 1.4 + 0.8 * random.random()
        
        # Période de Ramadan (consommation différente)
        if month in [3, 4] and building_class == 'Residential':
            if 4 <= hour <= 17:  # Jeûne pendant la journée
                consumption *= 0.6
            elif 18 <= hour <= 23:  # Iftar et activités nocturnes
                consumption *= 1.4
        
        return consumption
    
    def generate_timeseries_data(self, buildings_df, start_date, end_date, freq='30T'):
        """Génère les données de séries temporelles réalistes pour la Malaisie"""
        
        try:
            date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
            timeseries_data = []
            
            logger.info(f"⚡ Génération de {len(date_range)} points temporels pour {len(buildings_df)} bâtiments")
            
            for idx, (_, building) in enumerate(buildings_df.iterrows()):
                if idx % 10 == 0:
                    logger.info(f"Traitement bâtiment {idx+1}/{len(buildings_df)} - {building['location']}")
                
                building_class = building['building_class']
                unique_id = building['unique_id']
                location_name = building['location']
                
                # Obtenir les informations de localisation
                if location_name in self.malaysia_locations:
                    location_info = self.malaysia_locations[location_name]
                else:
                    # Localisation personnalisée
                    location_info = {
                        'population': building.get('population', 100000),
                        'state': building.get('state', 'Custom'),
                        'region': building.get('region', 'Custom')
                    }
                
                # Générer les points temporels
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
            
        except Exception as e:
            logger.error(f"Erreur génération séries temporelles: {e}")
            # Retourner un DataFrame vide en cas d'erreur
            return pd.DataFrame(columns=['unique_id', 'timestamp', 'y'])
    
    def get_building_analysis(self, city_name=None):
        """Retourne une analyse des types de bâtiments pour une ville"""
        
        try:
            if city_name and city_name in self.malaysia_locations:
                location_info = self.malaysia_locations[city_name]
                if hasattr(self.building_distributor, 'get_building_summary'):
                    return self.building_distributor.get_building_summary(
                        city_name, location_info['population']
                    )
            return None
        except Exception as e:
            logger.error(f"Erreur analyse bâtiments: {e}")
            return None


# Instance globale du générateur
try:
    generator = ElectricityDataGenerator()
    logger.info("✅ Générateur initialisé avec succès")
except Exception as e:
    logger.error(f"❌ Erreur initialisation générateur: {e}")
    raise


# Routes Flask
@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Génère et affiche les données avec validation automatique"""
    
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
        
        logger.info(f"🏗️ Génération - {num_buildings} bâtiments, {start_date} à {end_date}")
        
        # Générer les données
        buildings_df = generator.generate_building_metadata(
            num_buildings, location_filter, custom_location
        )
        timeseries_df = generator.generate_timeseries_data(buildings_df, start_date, end_date, freq)
        
        # Validation automatique intégrée (si disponible)
        validation_results = None
        if generator.validation_enabled and generator.validator:
            try:
                logger.info("🔍 Validation automatique en cours...")
                validation_results = generator.validator.validate_generation(
                    buildings_df, 
                    timeseries_df, 
                    auto_adjust=False
                )
                logger.info(f"✅ Validation terminée - Score: {validation_results['overall_quality']['score']}%")
            except Exception as e:
                logger.error(f"Erreur validation: {e}")
                validation_results = None
        
        # Calculer les statistiques
        stats = {
            'total_records': len(timeseries_df),
            'buildings_count': num_buildings,
            'unique_locations': len(buildings_df['location'].unique()),
            'avg_consumption': round(timeseries_df['y'].mean(), 2) if len(timeseries_df) > 0 else 0,
            'max_consumption': round(timeseries_df['y'].max(), 2) if len(timeseries_df) > 0 else 0,
            'min_consumption': round(timeseries_df['y'].min(), 2) if len(timeseries_df) > 0 else 0,
            'zero_values': int((timeseries_df['y'] == 0).sum()) if len(timeseries_df) > 0 else 0
        }
        
        # Analyser la distribution des types de bâtiments
        building_type_stats = buildings_df['building_class'].value_counts().to_dict()
        
        # Analyser par localisation
        location_analysis = []
        for location in buildings_df['location'].unique():
            location_buildings = buildings_df[buildings_df['location'] == location]
            location_info = {
                'location': location,
                'state': location_buildings.iloc[0]['state'],
                'region': location_buildings.iloc[0]['region'],
                'population': int(location_buildings.iloc[0]['population']),
                'building_count': len(location_buildings),
                'building_types': location_buildings['building_class'].value_counts().to_dict()
            }
            location_analysis.append(location_info)
        
        # Trier par nombre de bâtiments
        location_analysis.sort(key=lambda x: x['building_count'], reverse=True)
        
        # Préparer la réponse
        response_data = {
            'success': True,
            'buildings': buildings_df.to_dict('records'),
            'timeseries': timeseries_df.head(500).to_dict('records'),
            'stats': stats,
            'building_type_distribution': building_type_stats,
            'location_analysis': location_analysis
        }
        
        # Ajouter les résultats de validation si disponibles
        if validation_results:
            response_data['validation'] = {
                'enabled': True,
                'quality_score': validation_results['overall_quality']['score'],
                'grade': validation_results['overall_quality']['grade'],
                'cities_validated': validation_results['overall_quality']['cities_validated'],
                'recommendations': validation_results['recommendations'][:3],
                'report_summary': validation_results['report'][:500] + "..." if len(validation_results['report']) > 500 else validation_results['report'],
                'timestamp': validation_results['timestamp']
            }
        else:
            response_data['validation'] = {
                'enabled': False,
                'message': 'Validation non disponible'
            }
        
        logger.info(f"🎉 Génération réussie - {len(buildings_df)} bâtiments, {len(timeseries_df)} observations")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur génération: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/download', methods=['POST'])
def download():
    """Génère et télécharge les données avec validation complète"""
    
    try:
        data = request.get_json()
        num_buildings = data.get('num_buildings', 10)
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', '2024-01-31')
        freq = data.get('freq', '30T')
        
        # Gestion du filtrage géographique
        location_filter = data.get('location_filter')
        custom_location_data = data.get('custom_location')
        
        # Préparer la localisation personnalisée
        custom_location = None
        if custom_location_data and custom_location_data.get('name'):
            custom_loc_info = {
                'population': custom_location_data.get('population', 100000),
                'state': custom_location_data.get('state', 'Custom'),
                'region': custom_location_data.get('region', 'Custom')
            }
            custom_location = {custom_location_data['name']: custom_loc_info}
        
        logger.info(f"📦 Téléchargement - {num_buildings} bâtiments")
        
        # Générer les données
        buildings_df = generator.generate_building_metadata(
            num_buildings, location_filter, custom_location
        )
        timeseries_df = generator.generate_timeseries_data(buildings_df, start_date, end_date, freq)
        
        # Validation pour le téléchargement (plus complète)
        validation_results = None
        if generator.validation_enabled and generator.validator:
            try:
                logger.info("🔍 Validation complète avant téléchargement...")
                validation_results = generator.validator.validate_generation(
                    buildings_df, 
                    timeseries_df, 
                    auto_adjust=True  # Ajustements automatiques pour téléchargement
                )
                
                # Exporter les métriques de validation
                generator.validator.export_validation_metrics()
            except Exception as e:
                logger.error(f"Erreur validation téléchargement: {e}")
                validation_results = None
        
        # Créer le dossier de sortie
        output_dir = 'generated_data'
        os.makedirs(output_dir, exist_ok=True)
        
        # Noms des fichiers avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Déterminer le nom selon le type de génération
        if custom_location:
            location_name = list(custom_location.keys())[0].replace(' ', '_').replace('/', '_')
            prefix = f'malaysia_{location_name}'
        elif location_filter and any(v != 'all' for v in [location_filter.get('city', 'all'), location_filter.get('state', 'all'), location_filter.get('region', 'all')]):
            filter_name = "filtered"
            if location_filter.get('city') and location_filter['city'] != 'all':
                filter_name = location_filter['city'].replace(' ', '_').replace('/', '_')
            elif location_filter.get('state') and location_filter['state'] != 'all':
                filter_name = location_filter['state'].replace(' ', '_').replace('/', '_')
            elif location_filter.get('region') and location_filter['region'] != 'all':
                filter_name = location_filter['region'].replace(' ', '_').replace('/', '_')
            prefix = f'malaysia_{filter_name}'
        else:
            prefix = 'malaysia'
        
        buildings_filename = f'{output_dir}/{prefix}_buildings_{timestamp}.parquet'
        timeseries_filename = f'{output_dir}/{prefix}_demand_{timestamp}.parquet'
        validation_filename = f'{output_dir}/{prefix}_validation_{timestamp}.txt'
        
        # Sauvegarder les fichiers
        buildings_df.to_parquet(buildings_filename, index=False)
        timeseries_df.to_parquet(timeseries_filename, index=False)
        
        # Sauvegarder le rapport de validation
        if validation_results:
            with open(validation_filename, 'w', encoding='utf-8') as f:
                f.write(validation_results['report'])
        
        # Créer le message de résumé
        message = f"""📁 Fichiers générés pour la MALAISIE:
        
🏢 Métadonnées: {buildings_filename}
   - {len(buildings_df)} bâtiments répartis dans {buildings_df['location'].nunique()} villes
        
⚡ Séries temporelles: {timeseries_filename}
   - {len(timeseries_df):,} observations
   - Période: {start_date} à {end_date}
   - Fréquence: {freq}
        
📈 Statistiques:
   - Consommation moyenne: {timeseries_df['y'].mean():.2f} kWh
   - Consommation maximale: {timeseries_df['y'].max():.2f} kWh
   - Valeurs nulles: {(timeseries_df['y'] == 0).sum()} ({(timeseries_df['y'] == 0).sum() / len(timeseries_df) * 100:.1f}%)
        
🌴 Réalisme: Distribution basée sur la taille et le type de chaque ville"""
        
        if validation_results:
            message += f"""
            
🔍 VALIDATION: Score {validation_results['overall_quality']['score']}% ({validation_results['overall_quality']['grade']})
📋 Rapport: {validation_filename}"""
        
        files_generated = {
            'buildings': buildings_filename,
            'timeseries': timeseries_filename
        }
        
        if validation_results:
            files_generated['validation_report'] = validation_filename
        
        response_data = {
            'success': True,
            'message': message,
            'files': files_generated
        }
        
        logger.info("✅ Téléchargement préparé avec succès!")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/sample')
def sample():
    """Génère un échantillon de démonstration"""
    
    try:
        logger.info("🔬 Génération d'un échantillon...")
        
        buildings_df = generator.generate_building_metadata(5)
        timeseries_df = generator.generate_timeseries_data(buildings_df, '2024-01-01', '2024-01-02', '30T')
        
        stats = {
            'total_records': len(timeseries_df),
            'buildings_count': len(buildings_df),
            'avg_consumption': round(timeseries_df['y'].mean(), 2) if len(timeseries_df) > 0 else 0,
            'max_consumption': round(timeseries_df['y'].max(), 2) if len(timeseries_df) > 0 else 0,
            'min_consumption': round(timeseries_df['y'].min(), 2) if len(timeseries_df) > 0 else 0,
            'zero_values': int((timeseries_df['y'] == 0).sum()) if len(timeseries_df) > 0 else 0
        }
        
        building_type_stats = buildings_df['building_class'].value_counts().to_dict()
        
        return jsonify({
            'success': True,
            'buildings': buildings_df.to_dict('records'),
            'timeseries': timeseries_df.to_dict('records'),
            'stats': stats,
            'building_types': generator.building_classes,
            'building_type_distribution': building_type_stats,
            'malaysia_locations': list(generator.malaysia_locations.keys()),
            'validation_enabled': generator.validation_enabled
        })
        
    except Exception as e:
        logger.error(f"Erreur échantillon: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stats')
def api_stats():
    """API pour obtenir des statistiques sur les données générables"""
    
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
                'description': f"Base: {pattern['base']} kWh, Pic: {pattern['peak']} kWh",
                'base': pattern['base'],
                'peak': pattern['peak']
            } for class_name, pattern in generator.consumption_patterns.items()
        },
        'supported_frequencies': ['30T', '1H', '15T', '5T'],
        'validation_enabled': generator.validation_enabled,
        'building_distributor_available': BUILDING_DISTRIBUTOR_AVAILABLE,
        'realistic_features': [
            'Distribution basée sur la taille réelle des villes',
            'Climat tropical avec pics de climatisation',
            'Patterns culturels (Vendredi, Ramadan)',
            'Coordonnées GPS précises de Malaisie',
            f'{len(generator.malaysia_locations)} villes disponibles',
            'Validation automatique' if generator.validation_enabled else 'Validation non disponible'
        ]
    })


@app.route('/api/city-analysis/<city_name>')
def api_city_analysis(city_name):
    """API pour obtenir l'analyse détaillée d'une ville"""
    
    try:
        analysis = generator.get_building_analysis(city_name)
        if analysis:
            return jsonify({
                'success': True,
                'city_name': city_name,
                'analysis': analysis
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Ville '{city_name}' non trouvée ou analyse non disponible"
            })
    except Exception as e:
        logger.error(f"Erreur analyse ville: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/validation-history')
def get_validation_history():
    """API pour consulter l'historique de validation"""
    
    if not generator.validation_enabled or not generator.validator:
        return jsonify({
            'success': False,
            'error': 'Validation non disponible'
        })
    
    try:
        trend = generator.validator.get_quality_trend(days=30)
        return jsonify({
            'success': True,
            'validation_enabled': True,
            'trend': trend,
            'recent_validations': generator.validator.validation_history[-10:],
            'total_validations': len(generator.validator.validation_history)
        })
    except Exception as e:
        logger.error(f"Erreur historique validation: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/validation-metrics')
def get_validation_metrics():
    """API pour obtenir les métriques de validation"""
    
    if not generator.validation_enabled or not generator.validator:
        return jsonify({
            'success': False,
            'error': 'Validation non disponible'
        })
    
    try:
        metrics_df = generator.validator.export_validation_metrics()
        return jsonify({
            'success': True,
            'metrics_file': 'validation_metrics.csv',
            'summary': {
                'total_validations': len(metrics_df),
                'average_score': metrics_df['overall_score'].mean() if not metrics_df.empty else 0,
                'best_score': metrics_df['overall_score'].max() if not metrics_df.empty else 0,
                'cities_analyzed': metrics_df['city_name'].nunique() if not metrics_df.empty else 0
            }
        })
    except Exception as e:
        logger.error(f"Erreur métriques validation: {e}")
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("🇲🇾 Démarrage du générateur de données électriques pour la MALAISIE...")
    print(f"🏙️ {len(generator.malaysia_locations)} villes disponibles")
    print("📊 Distribution réaliste des bâtiments selon les caractéristiques urbaines")
    print("🌴 Patterns climatiques tropicaux intégrés")
    
    if generator.validation_enabled:
        print("✅ VALIDATION AUTOMATIQUE ACTIVÉE")
        print("   - Validation en temps réel de chaque génération")
        print("   - Scores de qualité basés sur données Malaysia")
        print("   - APIs: /api/validation-history, /api/validation-metrics")
    else:
        print("⚠️ Validation non disponible - mode standard")
    
    if BUILDING_DISTRIBUTOR_AVAILABLE:
        print("✅ Distribution réaliste activée")
    else:
        print("⚠️ Distribution basique utilisée")
    
    print("⚡ Serveur prêt sur http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)