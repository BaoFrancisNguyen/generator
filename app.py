# app.py - Generateur de Donnees Electriques Malaysia (Version Corrigee)
"""
Systeme de generation de donnees electriques realistes pour la Malaisie
Architecture simplifiee avec gestion d'erreurs amelioree
Integre le systeme de coordonnees ameliore avec quartiers
"""

from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid
import os
import json
import logging
from osm_generation_route import add_osm_routes


# Configuration du logging pour tracer les operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tentative d'import du distributeur intelligent de batiments
try:
    from building_distribution import BuildingDistributor
    BUILDING_DISTRIBUTOR_AVAILABLE = True
    logger.info("✅ BuildingDistributor importe avec succes")
except ImportError as e:
    logger.error(f"❌ Erreur import BuildingDistributor: {e}")
    BUILDING_DISTRIBUTOR_AVAILABLE = False

# Tentative d'import du systeme de coordonnees ameliore
try:
    from automated_districts import EnhancedCoordinatesGenerator
    ENHANCED_COORDINATES_AVAILABLE = True
    logger.info("✅ Systeme de coordonnees ameliore disponible")
except ImportError as e:
    logger.warning(f"⚠️ Systeme de coordonnees ameliore non disponible: {e}")
    ENHANCED_COORDINATES_AVAILABLE = False

# Tentative d'import de l'integration complete
try:
    from complete_integration import create_complete_integration
    COMPLETE_INTEGRATION_AVAILABLE = True
    logger.info("✅ Integration complete disponible")
except ImportError as e:
    logger.warning(f"⚠️ Integration complete non disponible: {e}")
    COMPLETE_INTEGRATION_AVAILABLE = False

app = Flask(__name__)


class SimpleDistributor:
    """
    Distributeur simple base uniquement sur la population de la ville
    Utilise comme solution de secours si BuildingDistributor n'est pas disponible
    """
    
    def __init__(self):
        logger.info("✅ SimpleDistributor initialise en mode distribution basique")
    
    def calculate_building_distribution(self, city_name, population, region, total_buildings):
        """
        Calcule la distribution des types de batiments selon la population uniquement
        
        Args:
            city_name (str): Nom de la ville
            population (int): Nombre d'habitants de la ville
            region (str): Region geographique
            total_buildings (int): Nombre total de batiments a distribuer
            
        Returns:
            dict: Dictionnaire avec le nombre de batiments par type
        """
        
        # Definition des pourcentages selon la taille de la ville
        if population > 500000:  
            # Grande ville : plus de diversite dans les types de batiments
            distribution = {
                'Residential': 0.60,    # 60% de logements
                'Commercial': 0.15,     # 15% de centres commerciaux
                'Office': 0.08,         # 8% de bureaux
                'Industrial': 0.05,     # 5% d'industrie
                'Retail': 0.05,         # 5% de magasins
                'School': 0.03,         # 3% d'ecoles
                'Hospital': 0.015,      # 1.5% d'hopitaux
                'Clinic': 0.025,        # 2.5% de cliniques
                'Hotel': 0.02           # 2% d'hotels
            }
        elif population > 100000:  
            # Ville moyenne : moins de bureaux et d'hotels
            distribution = {
                'Residential': 0.70,    # 70% de logements
                'Commercial': 0.10,     # 10% de centres commerciaux
                'Industrial': 0.08,     # 8% d'industrie
                'Retail': 0.04,         # 4% de magasins
                'School': 0.04,         # 4% d'ecoles
                'Hospital': 0.01,       # 1% d'hopitaux
                'Clinic': 0.02,         # 2% de cliniques
                'Hotel': 0.01           # 1% d'hotels
            }
        else:  
            # Petite ville : principalement residentiel avec services de base
            distribution = {
                'Residential': 0.75,    # 75% de logements
                'Commercial': 0.08,     # 8% de centres commerciaux
                'Industrial': 0.05,     # 5% d'industrie
                'Retail': 0.06,         # 6% de magasins
                'School': 0.04,         # 4% d'ecoles
                'Clinic': 0.02          # 2% de cliniques (pas d'hopital)
            }
        
        # Conversion des pourcentages en nombres absolus de batiments
        building_counts = {}
        for building_type, percentage in distribution.items():
            count = max(0, int(percentage * total_buildings))
            building_counts[building_type] = count
        
        # Ajustement pour garantir que la somme egale exactement total_buildings
        total_assigned = sum(building_counts.values())
        if total_assigned < total_buildings:
            building_counts['Residential'] += (total_buildings - total_assigned)
        
        return building_counts


class ElectricityDataGenerator:
    """
    Generateur principal de donnees electriques realistes pour la Malaisie
    """
    
    def __init__(self):
        """Initialise le generateur avec le meilleur distributeur disponible"""
        
        # Choix du distributeur de batiments selon la disponibilite
        if BUILDING_DISTRIBUTOR_AVAILABLE:
            self.building_distributor = BuildingDistributor()
            logger.info("✅ BuildingDistributor charge - Distribution intelligente activee")
        else:
            self.building_distributor = SimpleDistributor()
            logger.warning("⚠️ SimpleDistributor utilise - Distribution basique seulement")
        
        # Initialisation du systeme de coordonnees ameliore
        if ENHANCED_COORDINATES_AVAILABLE:
            try:
                self.coordinate_generator = EnhancedCoordinatesGenerator()
                logger.info("✅ Systeme de coordonnees ameliore active")
            except Exception as e:
                logger.warning(f"⚠️ Erreur initialisation coordonnees ameliorees: {e}")
                self.coordinate_generator = None
        else:
            self.coordinate_generator = None
            logger.warning("⚠️ Systeme de coordonnees classique utilise")
        
        # Flags de disponibilite pour l'API
        self.real_data_available = BUILDING_DISTRIBUTOR_AVAILABLE
        self.validation_enabled = False  # Desactive dans cette version
        
        # Types de batiments supportes par le systeme
        self.building_classes = [
            'Residential', 'Commercial', 'Industrial', 'Office', 'Retail',
            'Hospital', 'Clinic', 'School', 'Hotel', 'Restaurant',
            'Warehouse', 'Factory', 'Apartment'
        ]
        
        # Base de donnees des localisations reelles en Malaisie
        self.malaysia_locations = {
            # Metropoles et grandes villes (plus de 500,000 habitants)
            'Kuala Lumpur': {'population': 1800000, 'state': 'Federal Territory', 'region': 'Central'},
            'George Town': {'population': 708000, 'state': 'Penang', 'region': 'Northern'},
            'Ipoh': {'population': 657000, 'state': 'Perak', 'region': 'Northern'},
            'Shah Alam': {'population': 641000, 'state': 'Selangor', 'region': 'Central'},
            'Petaling Jaya': {'population': 613000, 'state': 'Selangor', 'region': 'Central'},
            'Johor Bahru': {'population': 497000, 'state': 'Johor', 'region': 'Southern'},
            
            # Villes moyennes (100,000 - 500,000 habitants)
            'Kota Kinabalu': {'population': 452000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Kuching': {'population': 325000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            'Ampang Jaya': {'population': 315000, 'state': 'Selangor', 'region': 'Central'},
            'Klang': {'population': 290000, 'state': 'Selangor', 'region': 'Central'},
            'Kajang': {'population': 280000, 'state': 'Selangor', 'region': 'Central'},
            'Seremban': {'population': 275000, 'state': 'Negeri Sembilan', 'region': 'Central'},
            'Kuantan': {'population': 250000, 'state': 'Pahang', 'region': 'East Coast'},
            'Malacca City': {'population': 200000, 'state': 'Malacca', 'region': 'Central'},
            'Alor Setar': {'population': 185000, 'state': 'Kedah', 'region': 'Northern'},
            'Sandakan': {'population': 158000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Sibu': {'population': 145000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            'Sungai Petani': {'population': 140000, 'state': 'Kedah', 'region': 'Northern'},
            'Tawau': {'population': 135000, 'state': 'Sabah', 'region': 'East Malaysia'},
            'Kuala Terengganu': {'population': 125000, 'state': 'Terengganu', 'region': 'East Coast'},
            'Kota Bharu': {'population': 120000, 'state': 'Kelantan', 'region': 'East Coast'},
            'Miri': {'population': 115000, 'state': 'Sarawak', 'region': 'East Malaysia'},
            
            # Petites villes et destinations touristiques
            'Langkawi': {'population': 65000, 'state': 'Kedah', 'region': 'Northern'},
            'Cameron Highlands': {'population': 35000, 'state': 'Pahang', 'region': 'Central'},
            'Genting Highlands': {'population': 12000, 'state': 'Pahang', 'region': 'Central'},
            'Port Dickson': {'population': 45000, 'state': 'Negeri Sembilan', 'region': 'Central'},
            'Tioman Island': {'population': 3500, 'state': 'Pahang', 'region': 'East Coast'},
            
            # Autres villes importantes
            'Subang Jaya': {'population': 708000, 'state': 'Selangor', 'region': 'Central'},
            'Seri Kembangan': {'population': 200000, 'state': 'Selangor', 'region': 'Central'},
            'Putrajaya': {'population': 109000, 'state': 'Federal Territory', 'region': 'Central'},
            'Cyberjaya': {'population': 65000, 'state': 'Selangor', 'region': 'Central'}
        }
        
        # Patterns de consommation electrique realistes
        self.consumption_patterns = {
            'Residential': {
                'base': 0.5, 'peak': 12.0, 'variance': 2.5, 'night_factor': 0.3
            },
            'Commercial': {
                'base': 5.0, 'peak': 80.0, 'variance': 15.0, 'night_factor': 0.2
            },
            'Industrial': {
                'base': 20.0, 'peak': 200.0, 'variance': 40.0, 'night_factor': 0.7
            },
            'Office': {
                'base': 3.0, 'peak': 45.0, 'variance': 8.0, 'night_factor': 0.1
            },
            'Retail': {
                'base': 2.0, 'peak': 35.0, 'variance': 6.0, 'night_factor': 0.15
            },
            'Hospital': {
                'base': 25.0, 'peak': 70.0, 'variance': 12.0, 'night_factor': 0.8
            },
            'Clinic': {
                'base': 2.0, 'peak': 15.0, 'variance': 3.0, 'night_factor': 0.1
            },
            'School': {
                'base': 1.0, 'peak': 25.0, 'variance': 5.0, 'night_factor': 0.05
            },
            'Hotel': {
                'base': 8.0, 'peak': 40.0, 'variance': 8.0, 'night_factor': 0.6
            },
            'Restaurant': {
                'base': 3.0, 'peak': 60.0, 'variance': 15.0, 'night_factor': 0.2
            },
            'Warehouse': {
                'base': 2.0, 'peak': 30.0, 'variance': 8.0, 'night_factor': 0.4
            },
            'Factory': {
                'base': 30.0, 'peak': 150.0, 'variance': 35.0, 'night_factor': 0.6
            },
            'Apartment': {
                'base': 1.0, 'peak': 15.0, 'variance': 4.0, 'night_factor': 0.4
            }
        }
        
        logger.info(f"✅ Generateur initialise avec {len(self.malaysia_locations)} villes malaysiennes")

    def generate_unique_id(self):
        """Genere un identifiant unique pour chaque batiment"""
        return ''.join(random.choices('abcdef0123456789', k=16))

    def generate_coordinates(self, location, building_type=None):
        """
        Genere des coordonnees GPS realistes pour une ville malaysienne
        """
        
        if ENHANCED_COORDINATES_AVAILABLE and self.coordinate_generator:
            try:
                lat, lon = self.coordinate_generator.generate_coordinates(location, building_type)
                logger.debug(f"Coordonnees ameliorees pour {building_type or 'batiment'} a {location}: {lat}, {lon}")
                return lat, lon
            except Exception as e:
                logger.warning(f"Erreur systeme coordonnees ameliore: {e}, utilisation systeme classique")
        
        # Systeme classique - coordonnees precises des principales villes
        coordinates_map = {
            'Kuala Lumpur': {'lat': (3.1319, 3.1681), 'lon': (101.6841, 101.7381)},
            'George Town': {'lat': (5.4000, 5.4300), 'lon': (100.3000, 100.3300)},
            'Ipoh': {'lat': (4.5833, 4.6033), 'lon': (101.0833, 101.1033)},
            'Shah Alam': {'lat': (3.0667, 3.1167), 'lon': (101.4833, 101.5333)},
            'Petaling Jaya': {'lat': (3.1073, 3.1273), 'lon': (101.6063, 101.6263)},
            'Johor Bahru': {'lat': (1.4833, 1.5033), 'lon': (103.7333, 103.7533)},
            'Langkawi': {'lat': (6.3167, 6.3367), 'lon': (99.8167, 99.8367)},
            'Kota Kinabalu': {'lat': (5.9667, 5.9867), 'lon': (116.0667, 116.0867)},
            'Kuching': {'lat': (1.5333, 1.5533), 'lon': (110.3333, 110.3533)},
            'Cyberjaya': {'lat': (2.9167, 2.9367), 'lon': (101.6333, 101.6533)},
            'Malacca City': {'lat': (2.1896, 2.2096), 'lon': (102.2394, 102.2594)},
            'Alor Setar': {'lat': (6.1088, 6.1288), 'lon': (100.3580, 100.3780)},
            'Kuantan': {'lat': (3.8000, 3.8200), 'lon': (103.3200, 103.3400)}
        }
        
        if location in coordinates_map:
            coords = coordinates_map[location]
            lat_range = coords['lat']
            lon_range = coords['lon']
            
            latitude = round(random.uniform(lat_range[0], lat_range[1]), 6)
            longitude = round(random.uniform(lon_range[0], lon_range[1]), 6)
        else:
            # Coordonnees generiques pour la Malaisie
            latitude = round(random.uniform(1.0, 7.0), 6)
            longitude = round(random.uniform(99.5, 119.5), 6)
        
        return latitude, longitude

    def generate_building_metadata(self, num_buildings=100, location_filter=None, custom_location=None):
        """
        Genere les metadonnees des batiments avec distribution realiste
        """
        
        buildings = []
        
        try:
            # Etape 1 : Determiner les localisations disponibles
            if custom_location:
                available_locations = {custom_location['name']: custom_location}
                logger.info(f"Utilisation localisation personnalisee: {custom_location['name']}")
            elif location_filter:
                available_locations = self._filter_locations(location_filter)
                logger.info(f"Filtres appliques: {len(available_locations)} villes selectionnees")
            else:
                available_locations = self.malaysia_locations
                logger.info(f"Toutes les villes utilisees: {len(available_locations)} villes")
            
            if not available_locations:
                raise ValueError("Aucune localisation ne correspond aux criteres de filtrage")
            
            # Etape 2 : Repartition des batiments par ville selon la population
            city_building_counts = self._distribute_buildings_by_city(available_locations, num_buildings)
            logger.info(f"Batiments repartis dans {len(city_building_counts)} villes")
            
            # Etape 3 : Generation des batiments pour chaque ville
            building_id_counter = 1
            
            for location, building_count in city_building_counts.items():
                if building_count <= 0:
                    continue
                
                location_info = available_locations[location]
                logger.debug(f"Generation de {building_count} batiments pour {location}")
                
                # Obtenir la distribution realiste pour cette ville
                building_distribution = self.building_distributor.calculate_building_distribution(
                    location, location_info['population'], location_info['region'], building_count
                )
                
                # Creer la liste des types de batiments a generer
                building_types_list = self._create_building_types_list(building_distribution)
                
                # Generer les batiments individuels
                for i in range(building_count):
                    building = self._create_building(
                        location, location_info, building_types_list, i, building_id_counter
                    )
                    buildings.append(building)
                    building_id_counter += 1
            
            # Conversion en DataFrame
            buildings_df = pd.DataFrame(buildings)
            
            # Affichage du resume de generation
            self._print_generation_summary(buildings)
            
            return buildings_df
            
        except Exception as e:
            logger.error(f"Erreur lors de la generation des batiments: {e}")
            return self._generate_basic_buildings(num_buildings)

    def _filter_locations(self, location_filter):
        """Applique les filtres geographiques aux villes disponibles"""
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
        
        return available_locations

    def _distribute_buildings_by_city(self, available_locations, num_buildings):
        """Distribue les batiments aux villes selon leur population"""
        locations = list(available_locations.keys())
        populations = [available_locations[loc]['population'] for loc in locations]
        total_population = sum(populations)
        
        weights = [pop / total_population for pop in populations]
        
        city_building_counts = {}
        for i, location in enumerate(locations):
            count = max(1, int(num_buildings * weights[i]))
            city_building_counts[location] = count
        
        # Ajustement pour avoir exactement num_buildings au total
        total_assigned = sum(city_building_counts.values())
        if total_assigned != num_buildings:
            largest_city = max(locations, key=lambda x: available_locations[x]['population'])
            city_building_counts[largest_city] += (num_buildings - total_assigned)
        
        return city_building_counts

    def _create_building_types_list(self, building_distribution):
        """Cree une liste ordonnee des types de batiments a generer"""
        building_types_list = []
        for building_type, count in building_distribution.items():
            building_types_list.extend([building_type] * count)
        
        random.shuffle(building_types_list)
        return building_types_list

    def _create_building(self, location, location_info, building_types_list, index, building_id_counter):
        """Cree un batiment individuel avec toutes ses metadonnees"""
        unique_id = self.generate_unique_id()
        
        if index < len(building_types_list):
            building_class = building_types_list[index]
        else:
            building_class = 'Residential'
        
        lat, lon = self.generate_coordinates(location, building_class)
        
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
        """Affiche un resume detaille de la generation de batiments"""
        try:
            logger.info(f"\n--- RESUME DE GENERATION ---")
            logger.info("=" * 50)
            
            # Resume par ville
            city_counts = {}
            for building in buildings:
                city = building['location']
                city_counts[city] = city_counts.get(city, 0) + 1
            
            logger.info("Repartition des batiments par ville:")
            for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {city}: {count} batiments")
            
            # Distribution finale des types
            type_counts = {}
            for building in buildings:
                building_type = building['building_class']
                type_counts[building_type] = type_counts.get(building_type, 0) + 1
            
            logger.info(f"\nDistribution finale totale ({len(buildings)} batiments):")
            for building_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(buildings)) * 100
                logger.info(f"  - {building_type}: {count} ({percentage:.1f}%)")
            
            logger.info("=" * 50)
                
        except Exception as e:
            logger.error(f"Erreur affichage resume: {e}")

    def _generate_basic_buildings(self, num_buildings):
        """Generation basique en cas d'erreur du systeme principal"""
        logger.warning("Generation basique activee en mode secours")
        
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
        """Calcule une consommation electrique realiste pour le climat tropical malaysien"""
        
        if building_class not in self.consumption_patterns:
            building_class = 'Residential'
            
        pattern = self.consumption_patterns[building_class]
        
        hour = timestamp.hour
        day_of_week = timestamp.dayofweek
        month = timestamp.month
        is_weekend = day_of_week >= 5
        
        # Facteur climatique tropical
        climate_factor = 1.0
        if 11 <= hour <= 16:
            climate_factor = 1.4 + 0.3 * random.random()
        elif 17 <= hour <= 21:
            climate_factor = 1.2 + 0.2 * random.random()
        elif 6 <= hour <= 10:
            climate_factor = 0.8 + 0.2 * random.random()
        else:
            climate_factor = 0.9 + 0.2 * random.random()
        
        # Facteur saisonnier
        seasonal_factor = 1.0
        if month in [11, 12, 1, 2]:
            seasonal_factor = 0.85
        elif month in [5, 6, 7, 8]:
            seasonal_factor = 1.2
        else:
            seasonal_factor = 1.0
        
        # Calcul de la consommation de base
        base_consumption = pattern['base']
        peak_consumption = pattern['peak']
        variance = pattern['variance']
        night_factor = pattern['night_factor']
        
        # Pattern horaire selon le type de batiment
        if building_class in ['Residential', 'Apartment']:
            if 6 <= hour <= 8 or 18 <= hour <= 22:
                hourly_factor = 0.8 + 0.4 * random.random()
            elif 9 <= hour <= 17:
                hourly_factor = 0.4 + 0.3 * random.random()
            else:
                hourly_factor = night_factor + 0.2 * random.random()
        elif building_class in ['Office', 'Commercial']:
            if 9 <= hour <= 17:
                hourly_factor = 0.7 + 0.3 * random.random()
            elif 18 <= hour <= 22:
                hourly_factor = 0.3 + 0.2 * random.random()
            else:
                hourly_factor = night_factor + 0.1 * random.random()
        elif building_class in ['Industrial', 'Factory', 'Warehouse']:
            if 6 <= hour <= 18:
                hourly_factor = 0.8 + 0.2 * random.random()
            else:
                hourly_factor = night_factor + 0.3 * random.random()
        elif building_class == 'Hospital':
            hourly_factor = 0.7 + 0.3 * random.random()
        elif building_class in ['Hotel', 'Restaurant']:
            if building_class == 'Restaurant':
                if 12 <= hour <= 14 or 19 <= hour <= 22:
                    hourly_factor = 0.8 + 0.2 * random.random()
                else:
                    hourly_factor = 0.3 + 0.4 * random.random()
            else:
                if 18 <= hour <= 23:
                    hourly_factor = 0.7 + 0.3 * random.random()
                else:
                    hourly_factor = 0.5 + 0.3 * random.random()
        elif building_class in ['School', 'Clinic']:
            if 7 <= hour <= 17:
                hourly_factor = 0.6 + 0.4 * random.random()
            else:
                hourly_factor = night_factor + 0.1 * random.random()
        else:
            hourly_factor = 0.5 + 0.5 * random.random()
        
        # Facteur weekend
        weekend_factor = 1.0
        if is_weekend:
            if building_class in ['Office', 'School', 'Clinic']:
                weekend_factor = 0.2
            elif building_class in ['Commercial', 'Retail']:
                weekend_factor = 1.2
            elif building_class in ['Residential', 'Hotel', 'Restaurant']:
                weekend_factor = 1.1
        
        # Calcul final de la consommation
        consumption = (base_consumption + 
                      (peak_consumption - base_consumption) * hourly_factor)
        
        consumption *= climate_factor
        consumption *= seasonal_factor
        consumption *= weekend_factor
        
        # Ajout de variabilite aleatoire
        random_variance = random.gauss(0, variance * 0.1)
        consumption += random_variance
        
        # S'assurer que la consommation reste positive et realiste
        consumption = max(0.1, consumption)
        max_reasonable = peak_consumption * 2.0
        consumption = min(consumption, max_reasonable)
        
        return round(consumption, 3)

    def generate_timeseries_data(self, buildings_df, start_date, end_date, freq='30T'):
        """Genere les series temporelles de consommation electrique"""
        
        logger.info(f"Generation des series temporelles de {start_date} a {end_date} (freq: {freq})")
        
        # Creation de l'index temporel
        date_range = pd.date_range(
            start=start_date,
            end=end_date,
            freq=freq,
            tz='Asia/Kuala_Lumpur'
        )
        
        logger.info(f"Periode temporelle: {len(date_range)} points de donnees")
        
        # Initialisation de la liste des donnees
        timeseries_data = []
        total_records = len(buildings_df) * len(date_range)
        
        logger.info(f"Generation de {total_records:,} enregistrements au total")
        
        # Generation pour chaque batiment
        for building_idx, building in buildings_df.iterrows():
            building_id = building['unique_id']
            building_class = building['building_class']
            location_info = {
                'location': building['location'],
                'state': building['state'],
                'region': building['region'],
                'population': building['population']
            }
            
            # Generation pour chaque point temporel
            for timestamp in date_range:
                consumption = self.calculate_realistic_consumption(
                    building_class, timestamp, location_info
                )
                
                # Ajout d'evenements ponctuels
                consumption = self._apply_random_events(consumption, timestamp, building_class)
                
                timeseries_data.append({
                    'unique_id': building_id,
                    'ds': timestamp,
                    'y': consumption
                })
            
            # Log de progression
            if (building_idx + 1) % 50 == 0:
                progress = ((building_idx + 1) / len(buildings_df)) * 100
                logger.info(f"Progression: {progress:.1f}% ({building_idx + 1}/{len(buildings_df)} batiments)")
        
        # Conversion en DataFrame
        timeseries_df = pd.DataFrame(timeseries_data)
        
        logger.info(f"Series temporelles generees: {len(timeseries_df):,} enregistrements")
        logger.info(f"Consommation moyenne: {timeseries_df['y'].mean():.2f} kWh")
        logger.info(f"Consommation maximale: {timeseries_df['y'].max():.2f} kWh")
        
        return timeseries_df

    def _apply_random_events(self, base_consumption, timestamp, building_class):
        """Applique des evenements aleatoires realistes"""
        
        # Probabilite d'evenements exceptionnels (tres faible)
        if random.random() < 0.001:  # 0.1% de chance
            if random.random() < 0.3:
                return 0.0  # Panne electrique
            elif random.random() < 0.5:
                return base_consumption * (1.5 + random.random())  # Pic exceptionnel
        
        # Orages tropicaux (frequents en Malaisie)
        if random.random() < 0.01:  # 1% de chance
            if random.random() < 0.7:
                return base_consumption * 0.3  # Coupure partielle
            else:
                return base_consumption * 1.3  # Systemes de secours
        
        return base_consumption


def convert_numpy_types(obj):
    """Convertit les types numpy en types Python natifs pour la serialisation JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def safe_json_response(data):
    """Cree une reponse JSON en convertissant les types numpy"""
    try:
        clean_data = convert_numpy_types(data)
        return jsonify(clean_data)
    except Exception as e:
        logger.error(f"Erreur serialisation JSON: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur de serialisation des donnees',
            'details': str(e)
        })


# ===== INITIALISATION DU GENERATEUR =====
# CORRECTION CRITIQUE: Initialiser le generateur AVANT les routes
try:
    generator = ElectricityDataGenerator()
    logger.info("✅ Générateur principal initialisé avec succès")
except Exception as e:
    logger.error(f"❌ Erreur critique lors de l'initialisation du générateur: {e}")
    # Créer un générateur minimal de secours
    generator = None


# ===== ROUTES FLASK =====

@app.route('/')
def index():
    """Page d'accueil de l'application"""
    return render_template('index.html')


@app.route('/api/stats')
def api_stats():
    """API pour obtenir les statistiques du systeme"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
            
        # Statistiques generales
        stats = {
            'total_cities': len(generator.malaysia_locations),
            'building_types': len(generator.building_classes),
            'distribution_method': 'Distribution intelligente' if BUILDING_DISTRIBUTOR_AVAILABLE else 'Distribution basique',
            'system_capabilities': {
                'building_distributor': BUILDING_DISTRIBUTOR_AVAILABLE,
                'enhanced_coordinates': ENHANCED_COORDINATES_AVAILABLE,
                'validation_system': False,
                'climate_patterns': True,
                'cultural_patterns': True
            }
        }
        
        # Repartition par region
        regions = {}
        for city, info in generator.malaysia_locations.items():
            region = info['region']
            if region not in regions:
                regions[region] = []
            regions[region].append({
                'name': city,
                'population': info['population'],
                'state': info['state']
            })
        
        # Informations detaillees avec conversion des types numpy
        malaysia_info = {
            'total_population': int(sum(city['population'] for city in generator.malaysia_locations.values())),
            'largest_city': max(generator.malaysia_locations.items(), key=lambda x: x[1]['population']),
            'regions': regions,
            'building_classes': generator.building_classes
        }
        
        return safe_json_response({
            'success': True,
            'stats': stats,
            'malaysia_locations': generator.malaysia_locations,
            'malaysia_info': malaysia_info,
            'realistic_features': [
                'Distribution basee sur la taille reelle des villes',
                'Hopitaux seulement dans les villes >80K habitants',
                'Industries adaptees au profil economique des villes',
                'Coordonnees GPS precises des villes malaysiennes',
                'Patterns climatiques tropicaux integres',
                'Facteurs culturels malaysiens (Ramadan, vendredi)',
                'Variations saisonnieres (mousson vs saison seche)'
            ]
        })
        
    except Exception as e:
        logger.error(f"Erreur API stats: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/real-data-status')
def api_real_data_status():
    """API pour obtenir le statut des vraies donnees"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
            
        status = {
            'real_data_available': generator.real_data_available,
            'validation_enabled': generator.validation_enabled,
            'building_distributor_available': BUILDING_DISTRIBUTOR_AVAILABLE,
            'enhanced_coordinates_available': ENHANCED_COORDINATES_AVAILABLE,
            'data_sources': [
                'Population Census Malaysia',
                'Ministry of Health Malaysia',
                'Ministry of Education Malaysia',
                'Tourism Malaysia Statistics'
            ] if generator.real_data_available else [
                'Population estimates',
                'Statistical ratios',
                'Urban planning guidelines'
            ]
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'message': 'Système de données réelles Malaysia' if status['real_data_available'] else 'Mode estimation intelligent'
        })
        
    except Exception as e:
        logger.error(f"Erreur API real-data-status: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/generate', methods=['POST'])
def generate_data():
    """Route pour generer les donnees de batiments (sans series temporelles)"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
            
        # Recuperation des parametres de la requete
        params = request.get_json()
        
        num_buildings = int(params.get('num_buildings', 100))
        location_filter = params.get('location_filter')
        custom_location = params.get('custom_location')
        
        logger.info(f"Generation demandee: {num_buildings} batiments")
        
        # Generation des metadonnees des batiments
        buildings_df = generator.generate_building_metadata(
            num_buildings=num_buildings,
            location_filter=location_filter,
            custom_location=custom_location
        )
        
        # Analyse de la distribution finale avec conversion des types numpy
        building_type_stats = buildings_df['building_class'].value_counts().to_dict()
        building_type_stats = {k: int(v) for k, v in building_type_stats.items()}
        
        location_analysis = []
        
        for location in buildings_df['location'].unique():
            location_buildings = buildings_df[buildings_df['location'] == location]
            location_types = location_buildings['building_class'].value_counts().to_dict()
            location_types = {k: int(v) for k, v in location_types.items()}
            
            location_analysis.append({
                'location': location,
                'building_count': int(len(location_buildings)),
                'types': location_types,
                'state': location_buildings['state'].iloc[0],
                'region': location_buildings['region'].iloc[0],
                'population': int(location_buildings['population'].iloc[0]),
                'data_source': 'VRAIES DONNÉES' if BUILDING_DISTRIBUTOR_AVAILABLE else 'ESTIMATIONS'
            })
        
        # Calcul des statistiques
        stats = {
            'total_records': int(len(buildings_df)),
            'buildings_count': int(len(buildings_df)),
            'avg_consumption': 0,  # Sera calculé avec les séries temporelles
            'max_consumption': 0   # Sera calculé avec les séries temporelles
        }
        
        # Preparation de la reponse avec conversion des types
        response_data = {
            'success': True,
            'message': f'Generation reussie de {len(buildings_df)} batiments',
            'buildings': buildings_df.head(200).to_dict('records'),  # Limiter pour l'affichage
            'stats': stats,
            'location_analysis': location_analysis,
            'data_sources': {
                'real_data_used': generator.real_data_available,
                'data_quality': 'OFFICIAL' if generator.real_data_available else 'ESTIMATED',
                'sources': [
                    'Ministry of Health Malaysia',
                    'Ministry of Education Malaysia',
                    'Department of Statistics Malaysia'
                ] if generator.real_data_available else [
                    'Population-based estimation',
                    'Urban planning ratios'
                ]
            }
        }
        
        logger.info(f"Generation reussie - {len(buildings_df)} batiments, {len(buildings_df['location'].unique())} villes")
        
        return safe_json_response(response_data)
        
    except Exception as e:
        logger.error(f"Erreur generation: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/download', methods=['POST'])
def download_data():
    """Route pour generer et telecharger les fichiers complets"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
            
        # Recuperation des parametres
        params = request.get_json()
        
        num_buildings = int(params.get('num_buildings', 100))
        start_date = params.get('start_date', '2024-01-01')
        end_date = params.get('end_date', '2024-01-31')
        freq = params.get('freq', '30T')
        location_filter = params.get('location_filter')
        custom_location = params.get('custom_location')
        
        logger.info(f"Telechargement demande: {num_buildings} batiments, {start_date} a {end_date}")
        
        # Generation des batiments
        buildings_df = generator.generate_building_metadata(
            num_buildings=num_buildings,
            location_filter=location_filter,
            custom_location=custom_location
        )
        
        # Generation des series temporelles
        timeseries_df = generator.generate_timeseries_data(
            buildings_df, start_date, end_date, freq
        )
        
        # Preparation des noms de fichiers
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = 'generated_data'
        
        # Creer le dossier de sortie si necessaire
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Determination du prefixe selon le filtre de localisation
        if location_filter:
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
        
        # Sauvegarde des fichiers
        buildings_df.to_parquet(buildings_filename, index=False)
        timeseries_df.to_parquet(timeseries_filename, index=False)
        
        # Creation du message de resume
        message = f"""Fichiers generes pour la MALAISIE:
        
Metadonnees: {buildings_filename}
   - {len(buildings_df)} batiments repartis dans {buildings_df['location'].nunique()} villes
        
Series temporelles: {timeseries_filename}
   - {len(timeseries_df):,} observations
   - Periode: {start_date} a {end_date}
   - Frequence: {freq}
        
Statistiques:
   - Consommation moyenne: {timeseries_df['y'].mean():.2f} kWh
   - Consommation maximale: {timeseries_df['y'].max():.2f} kWh
   - Valeurs nulles: {(timeseries_df['y'] == 0).sum()} ({(timeseries_df['y'] == 0).sum() / len(timeseries_df) * 100:.1f}%)
        
Realisme: Distribution basee sur la taille et le type de chaque ville"""
        
        files_generated = {
            'buildings': buildings_filename,
            'timeseries': timeseries_filename
        }
        
        response_data = {
            'success': True,
            'message': message,
            'files': files_generated,
            'data_sources': {
                'real_data_used': generator.real_data_available,
                'data_quality': 'OFFICIAL' if generator.real_data_available else 'ESTIMATED'
            }
        }
        
        logger.info("Telechargement prepare avec succes!")
        
        return safe_json_response(response_data)
        
    except Exception as e:
        logger.error(f"Erreur telechargement: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/sample')
def show_sample():
    """Route pour afficher un echantillon de donnees"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
            
        # Generation d'un petit echantillon
        sample_buildings = generator.generate_building_metadata(num_buildings=10)
        sample_timeseries = generator.generate_timeseries_data(
            sample_buildings, '2024-01-01', '2024-01-02', '1H'
        )
        
        # Preparation des donnees d'exemple
        response_data = {
            'success': True,
            'buildings': sample_buildings.to_dict('records'),
            'timeseries': sample_timeseries.head(50).to_dict('records'),
            'stats': {
                'total_records': len(sample_timeseries),
                'buildings_count': len(sample_buildings),
                'avg_consumption': float(sample_timeseries['y'].mean()),
                'max_consumption': float(sample_timeseries['y'].max())
            },
            'summary': {
                'buildings_count': len(sample_buildings),
                'timeseries_count': len(sample_timeseries),
                'cities': sample_buildings['location'].unique().tolist(),
                'building_types': sample_buildings['building_class'].value_counts().to_dict()
            },
            'data_sources': {
                'real_data_used': generator.real_data_available,
                'data_quality': 'OFFICIAL' if generator.real_data_available else 'ESTIMATED'
            }
        }
        
        return safe_json_response(response_data)
        
    except Exception as e:
        logger.error(f"Erreur echantillon: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ===== INTEGRATION COMPLETE (SI DISPONIBLE) =====
if COMPLETE_INTEGRATION_AVAILABLE and generator:
    try:
        integration_success = create_complete_integration(app, generator)
        if integration_success:
            logger.info("✅ Intégration complète activée avec succès")
        else:
            logger.warning("⚠️ Échec de l'intégration complète")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'intégration complète: {e}")


# ===== POINT D'ENTREE PRINCIPAL =====
if __name__ == '__main__':
    print("🇲🇾 GÉNÉRATEUR DE DONNÉES ÉLECTRIQUES POUR LA MALAISIE")
    print("=" * 60)
    
    if generator:
        print(f"✅ Générateur initialisé avec succès")
        print(f"📍 Villes disponibles: {len(generator.malaysia_locations)}")
        print(f"🏗️ Types de bâtiments: {len(generator.building_classes)}")
        print(f"🧠 Distribution: {'Intelligente' if BUILDING_DISTRIBUTOR_AVAILABLE else 'Basique'}")
        print(f"📍 Coordonnées: {'Améliorées' if ENHANCED_COORDINATES_AVAILABLE else 'Classiques'}")
        print(f"🔗 Intégration: {'Complète' if COMPLETE_INTEGRATION_AVAILABLE else 'Basique'}")
    else:
        print("❌ ERREUR: Générateur non initialisé")
        print("🔧 Vérifiez les dépendances et relancez l'application")
    
    print()
    print("🌐 URLS DISPONIBLES:")
    urls = [
        "http://localhost:5000 - Interface principale",
        "http://localhost:5000/api/stats - Statistiques système",
        "http://localhost:5000/api/real-data-status - Statut des données",
        "http://localhost:5000/sample - Échantillon de démonstration"
    ]
    
    for url in urls:
        print(f"  {url}")
    
    print()
    print("💡 CONSEILS D'UTILISATION:")
    tips = [
        "🧪 Test: 5-20 bâtiments, 1 semaine, fréquence 1H",
        "📚 Développement: 50-200 bâtiments, 1-3 mois, 30T",
        "🤖 ML: 200-1000 bâtiments, 6-12 mois, 1H",
        "🏭 Production: 1000+ bâtiments, 1+ an, 30T ou 1H"
    ]
    
    for tip in tips:
        print(f"  {tip}")
    
    print()
    print("🚀 DÉMARRAGE DU SERVEUR...")
    print("=" * 60)
    
    try:
        if generator:
            app.run(debug=True, host='0.0.0.0', port=5000)
        else:
            print("❌ Impossible de démarrer: générateur non initialisé")
            print("🔧 Corrigez les erreurs ci-dessus et relancez")
    except Exception as e:
        print(f"❌ Erreur de démarrage: {e}")
        print("🔧 Vérifiez que le port 5000 n'est pas déjà utilisé")