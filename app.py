# app.py - Application Flask pour Génération de Données Électriques Malaysia
"""
Système de génération de données électriques réalistes pour la Malaisie
Version corrigée avec toutes les routes nécessaires
Intègre le système OSM et les prédicteurs de bâtiments
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
from typing import Dict, List, Optional

# Configuration du logging pour tracer les opérations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des modules avec gestion d'erreur
try:
    from building_distribution import BuildingDistributor
    BUILDING_DISTRIBUTOR_AVAILABLE = True
    logger.info("✅ BuildingDistributor importé avec succès")
except ImportError as e:
    logger.warning(f"⚠️ BuildingDistributor non disponible: {e}")
    BUILDING_DISTRIBUTOR_AVAILABLE = False

try:
    from automated_districts import EnhancedCoordinatesGenerator
    ENHANCED_COORDINATES_AVAILABLE = True
    logger.info("✅ Système de coordonnées amélioré disponible")
except ImportError as e:
    logger.warning(f"⚠️ Système de coordonnées amélioré non disponible: {e}")
    ENHANCED_COORDINATES_AVAILABLE = False

try:
    from complete_integration import create_complete_integration
    COMPLETE_INTEGRATION_AVAILABLE = True
    logger.info("✅ Intégration complète disponible")
except ImportError as e:
    logger.warning(f"⚠️ Intégration complète non disponible: {e}")
    COMPLETE_INTEGRATION_AVAILABLE = False

# Initialisation de l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'malaysia-electricity-generator-2025'


class SimpleDistributor:
    """
    Distributeur simple basé uniquement sur la population de la ville
    Solution de secours si BuildingDistributor n'est pas disponible
    """
    
    def __init__(self):
        logger.info("✅ SimpleDistributor initialisé en mode distribution basique")
    
    def calculate_building_distribution(self, city_name, population, region, total_buildings):
        """
        Calcule la distribution des types de bâtiments selon la population
        
        Args:
            city_name (str): Nom de la ville
            population (int): Nombre d'habitants
            region (str): Région géographique
            total_buildings (int): Nombre total de bâtiments à distribuer
            
        Returns:
            dict: Dictionnaire avec le nombre de bâtiments par type
        """
        # Distribution basique selon la taille de la ville
        if population > 1000000:  # Métropole
            ratios = {
                'Residential': 0.60, 'Commercial': 0.15, 'Office': 0.10,
                'Industrial': 0.05, 'Hospital': 0.002, 'Clinic': 0.008,
                'School': 0.03, 'Hotel': 0.02, 'Restaurant': 0.05,
                'Retail': 0.08, 'Warehouse': 0.015, 'Apartment': 0.012
            }
        elif population > 500000:  # Grande ville
            ratios = {
                'Residential': 0.70, 'Commercial': 0.12, 'Office': 0.06,
                'Industrial': 0.04, 'Hospital': 0.001, 'Clinic': 0.006,
                'School': 0.025, 'Hotel': 0.015, 'Restaurant': 0.04,
                'Retail': 0.06, 'Warehouse': 0.01, 'Apartment': 0.008
            }
        else:  # Ville moyenne/petite
            ratios = {
                'Residential': 0.80, 'Commercial': 0.08, 'Office': 0.03,
                'Industrial': 0.03, 'Hospital': 0.0005, 'Clinic': 0.004,
                'School': 0.02, 'Hotel': 0.01, 'Restaurant': 0.025,
                'Retail': 0.04, 'Warehouse': 0.005, 'Apartment': 0.003
            }
        
        # Calcul des bâtiments par type
        distribution = {}
        remaining = total_buildings
        
        for building_type, ratio in ratios.items():
            if building_type == list(ratios.keys())[-1]:  # Dernier type
                distribution[building_type] = remaining
            else:
                count = max(1, int(total_buildings * ratio))
                distribution[building_type] = count
                remaining -= count
        
        logger.info(f"Distribution calculée pour {city_name}: {sum(distribution.values())} bâtiments")
        return distribution


class ElectricityDataGenerator:
    """
    Générateur principal de données électriques pour la Malaisie
    """
    
    def __init__(self):
        """Initialise le générateur avec toutes les données de base"""
        logger.info("🔧 Initialisation du générateur de données électriques...")
        
        # Initialisation du distributeur de bâtiments
        if BUILDING_DISTRIBUTOR_AVAILABLE:
            try:
                self.distributor = BuildingDistributor()
                logger.info("✅ BuildingDistributor activé")
            except Exception as e:
                logger.error(f"Erreur BuildingDistributor: {e}, utilisation du mode simple")
                self.distributor = SimpleDistributor()
        else:
            self.distributor = SimpleDistributor()
        
        # Initialisation du système de coordonnées
        if ENHANCED_COORDINATES_AVAILABLE:
            try:
                self.coordinates_generator = EnhancedCoordinatesGenerator()
                logger.info("✅ Système de coordonnées amélioré activé")
            except Exception as e:
                logger.error(f"Erreur coordonnées améliorées: {e}")
                self.coordinates_generator = None
        else:
            self.coordinates_generator = None
        
        # Données géographiques de la Malaisie
        self.malaysia_locations = self._init_malaysia_locations()
        
        # Types et classes de bâtiments
        self.building_classes = self._init_building_classes()
        
        # Patterns de consommation
        self.consumption_patterns = self._init_consumption_patterns()
        
        logger.info(f"✅ Générateur initialisé: {len(self.malaysia_locations)} villes, {len(self.building_classes)} types de bâtiments")
    
    def _init_malaysia_locations(self):
        """Initialise les données des villes malaisiennes"""
        return {
            'Kuala Lumpur': {
                'coordinates': [3.139, 101.6869],
                'population': 1800000,
                'region': 'Central',
                'state': 'Federal Territory'
            },
            'George Town': {
                'coordinates': [5.4164, 100.3327],
                'population': 708000,
                'region': 'Northern',
                'state': 'Penang'
            },
            'Ipoh': {
                'coordinates': [4.5975, 101.0901],
                'population': 657000,
                'region': 'Northern',
                'state': 'Perak'
            },
            'Shah Alam': {
                'coordinates': [3.0733, 101.5185],
                'population': 617000,
                'region': 'Central',
                'state': 'Selangor'
            },
            'Petaling Jaya': {
                'coordinates': [3.1073, 101.6067],
                'population': 613977,
                'region': 'Central',
                'state': 'Selangor'
            },
            'Johor Bahru': {
                'coordinates': [1.4927, 103.7414],
                'population': 497067,
                'region': 'Southern',
                'state': 'Johor'
            },
            'Subang Jaya': {
                'coordinates': [3.0436, 101.5817],
                'population': 472930,
                'region': 'Central',
                'state': 'Selangor'
            },
            'Kota Kinabalu': {
                'coordinates': [5.9749, 116.0724],
                'population': 452058,
                'region': 'Eastern',
                'state': 'Sabah'
            },
            'Klang': {
                'coordinates': [3.0449, 101.4446],
                'population': 240016,
                'region': 'Central',
                'state': 'Selangor'
            },
            'Malacca City': {
                'coordinates': [2.2055, 102.2502],
                'population': 484885,
                'region': 'Southern',
                'state': 'Melaka'
            },
            'Alor Setar': {
                'coordinates': [6.1248, 100.3678],
                'population': 405523,
                'region': 'Northern',
                'state': 'Kedah'
            },
            'Kuching': {
                'coordinates': [1.5533, 110.3592],
                'population': 325132,
                'region': 'Eastern',
                'state': 'Sarawak'
            },
            'Tawau': {
                'coordinates': [4.2515, 117.8872],
                'population': 113809,
                'region': 'Eastern',
                'state': 'Sabah'
            },
            'Kuantan': {
                'coordinates': [3.8077, 103.3260],
                'population': 366229,
                'region': 'Eastern',
                'state': 'Pahang'
            }
        }
    
    def _init_building_classes(self):
        """Initialise les types de bâtiments avec leurs caractéristiques"""
        return {
            'Residential': {
                'base_consumption': 15.0,
                'variation': 0.4,
                'peak_hours': [19, 20, 21],
                'low_hours': [3, 4, 5],
                'seasonal_factor': 1.2,
                'description': 'Maisons et résidences individuelles'
            },
            'Apartment': {
                'base_consumption': 8.5,
                'variation': 0.3,
                'peak_hours': [20, 21, 22],
                'low_hours': [3, 4, 5],
                'seasonal_factor': 1.15,
                'description': 'Appartements et condominiums'
            },
            'Commercial': {
                'base_consumption': 45.0,
                'variation': 0.6,
                'peak_hours': [10, 11, 14, 15],
                'low_hours': [1, 2, 3, 4, 5, 6],
                'seasonal_factor': 1.3,
                'description': 'Centres commerciaux et magasins'
            },
            'Office': {
                'base_consumption': 35.0,
                'variation': 0.5,
                'peak_hours': [9, 10, 11, 14, 15, 16],
                'low_hours': [22, 23, 0, 1, 2, 3, 4, 5, 6, 7],
                'seasonal_factor': 1.4,
                'description': 'Bureaux et espaces de travail'
            },
            'Industrial': {
                'base_consumption': 120.0,
                'variation': 0.3,
                'peak_hours': [8, 9, 10, 13, 14, 15],
                'low_hours': [22, 23, 0, 1, 2, 3, 4, 5],
                'seasonal_factor': 1.1,
                'description': 'Usines et installations industrielles'
            },
            'Hospital': {
                'base_consumption': 200.0,
                'variation': 0.2,
                'peak_hours': list(range(24)),  # 24h/24
                'low_hours': [],
                'seasonal_factor': 1.05,
                'description': 'Hôpitaux et centres médicaux'
            },
            'Clinic': {
                'base_consumption': 25.0,
                'variation': 0.4,
                'peak_hours': [9, 10, 11, 14, 15, 16],
                'low_hours': [22, 23, 0, 1, 2, 3, 4, 5, 6, 7],
                'seasonal_factor': 1.1,
                'description': 'Cliniques et cabinets médicaux'
            },
            'School': {
                'base_consumption': 40.0,
                'variation': 0.8,
                'peak_hours': [8, 9, 10, 11, 13, 14, 15],
                'low_hours': [17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6],
                'seasonal_factor': 1.6,
                'description': 'Écoles et universités'
            },
            'Hotel': {
                'base_consumption': 60.0,
                'variation': 0.4,
                'peak_hours': [19, 20, 21, 22, 7, 8],
                'low_hours': [2, 3, 4, 5],
                'seasonal_factor': 1.3,
                'description': 'Hôtels et hébergements'
            },
            'Restaurant': {
                'base_consumption': 35.0,
                'variation': 0.7,
                'peak_hours': [12, 13, 19, 20, 21],
                'low_hours': [2, 3, 4, 5, 6, 7, 8, 9],
                'seasonal_factor': 1.2,
                'description': 'Restaurants et cafés'
            },
            'Retail': {
                'base_consumption': 30.0,
                'variation': 0.5,
                'peak_hours': [11, 12, 15, 16, 17, 20, 21],
                'low_hours': [1, 2, 3, 4, 5, 6, 7, 8],
                'seasonal_factor': 1.25,
                'description': 'Commerces de détail'
            },
            'Warehouse': {
                'base_consumption': 15.0,
                'variation': 0.3,
                'peak_hours': [8, 9, 10, 13, 14, 15, 16],
                'low_hours': [20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7],
                'seasonal_factor': 1.05,
                'description': 'Entrepôts et stockage'
            }
        }
    
    def _init_consumption_patterns(self):
        """Initialise les patterns de consommation selon les régions"""
        return {
            'Central': {'multiplier': 1.2, 'peak_shift': 0, 'climate_factor': 1.3},
            'Northern': {'multiplier': 1.0, 'peak_shift': 0, 'climate_factor': 1.2},
            'Southern': {'multiplier': 1.1, 'peak_shift': 0, 'climate_factor': 1.25},
            'Eastern': {'multiplier': 0.9, 'peak_shift': 1, 'climate_factor': 1.35}
        }
    
    def generate_buildings_dataframe(self, city_name: str, num_buildings: int) -> pd.DataFrame:
        """
        Génère un DataFrame des bâtiments pour une ville donnée
        
        Args:
            city_name (str): Nom de la ville
            num_buildings (int): Nombre total de bâtiments à générer
            
        Returns:
            pd.DataFrame: DataFrame avec tous les bâtiments générés
        """
        logger.info(f"🏢 Génération de {num_buildings} bâtiments pour {city_name}")
        
        # Récupération des informations de la ville
        city_info = self.malaysia_locations.get(city_name)
        if not city_info:
            logger.error(f"❌ Ville inconnue: {city_name}")
            raise ValueError(f"Ville non trouvée: {city_name}")
        
        # Calcul de la distribution des types de bâtiments
        try:
            distribution = self.distributor.calculate_building_distribution(
                city_name, 
                city_info['population'], 
                city_info['region'], 
                num_buildings
            )
        except Exception as e:
            logger.error(f"Erreur distribution: {e}")
            # Distribution de secours
            distribution = {'Residential': num_buildings}
        
        # Génération des bâtiments
        buildings_data = []
        building_counter = 1
        
        for building_type, count in distribution.items():
            if count > 0:
                for i in range(count):
                    # Génération des coordonnées
                    if self.coordinates_generator:
                        try:
                            coords = self.coordinates_generator.generate_building_coordinates(
                                city_name, building_type
                            )
                        except Exception as e:
                            logger.warning(f"Erreur coordonnées améliorées: {e}")
                            coords = self._generate_basic_coordinates(city_info['coordinates'])
                    else:
                        coords = self._generate_basic_coordinates(city_info['coordinates'])
                    
                    # Création du bâtiment
                    building = {
                        'building_id': f"{city_name}_{building_type}_{building_counter:04d}",
                        'city': city_name,
                        'building_type': building_type,
                        'latitude': coords[0],
                        'longitude': coords[1],
                        'region': city_info['region'],
                        'state': city_info['state'],
                        'base_consumption': self.building_classes[building_type]['base_consumption'],
                        'variation': self.building_classes[building_type]['variation']
                    }
                    buildings_data.append(building)
                    building_counter += 1
        
        buildings_df = pd.DataFrame(buildings_data)
        logger.info(f"✅ {len(buildings_df)} bâtiments générés avec succès")
        return buildings_df
    
    def _generate_basic_coordinates(self, city_coords: List[float]) -> List[float]:
        """
        Génère des coordonnées de base autour du centre ville
        
        Args:
            city_coords (List[float]): Coordonnées [lat, lng] du centre ville
            
        Returns:
            List[float]: Nouvelles coordonnées [lat, lng]
        """
        # Variation aléatoire autour du centre (rayon ~10km)
        lat_offset = random.uniform(-0.09, 0.09)  # ~10km en latitude
        lng_offset = random.uniform(-0.09, 0.09)  # ~10km en longitude
        
        return [
            city_coords[0] + lat_offset,
            city_coords[1] + lng_offset
        ]
    
    def generate_timeseries_data(self, buildings_df: pd.DataFrame, start_date: str, 
                                end_date: str, freq: str = '30T') -> pd.DataFrame:
        """
        Génère les données de séries temporelles de consommation électrique
        
        Args:
            buildings_df (pd.DataFrame): DataFrame des bâtiments
            start_date (str): Date de début (YYYY-MM-DD)
            end_date (str): Date de fin (YYYY-MM-DD)
            freq (str): Fréquence des mesures (30T = 30 minutes)
            
        Returns:
            pd.DataFrame: DataFrame avec les données de consommation
        """
        logger.info(f"📊 Génération des séries temporelles du {start_date} au {end_date} (freq: {freq})")
        
        # Génération de l'index temporel
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        logger.info(f"📈 {len(date_range)} points temporels à générer")
        
        # Stockage des données
        consumption_data = []
        
        for _, building in buildings_df.iterrows():
            building_type = building['building_type']
            region = building['region']
            
            # Récupération des patterns de consommation
            building_class = self.building_classes[building_type]
            region_pattern = self.consumption_patterns.get(region, self.consumption_patterns['Central'])
            
            for timestamp in date_range:
                # Calcul de la consommation pour ce timestamp
                consumption = self._calculate_consumption(
                    building_class, region_pattern, timestamp
                )
                
                # Ajout des données
                consumption_data.append({
                    'timestamp': timestamp,
                    'building_id': building['building_id'],
                    'consumption_kwh': round(consumption, 2),
                    'city': building['city'],
                    'building_type': building_type,
                    'region': region
                })
        
        consumption_df = pd.DataFrame(consumption_data)
        logger.info(f"✅ {len(consumption_df)} enregistrements de consommation générés")
        return consumption_df
    
    def _calculate_consumption(self, building_class: dict, region_pattern: dict, 
                             timestamp: datetime) -> float:
        """
        Calcule la consommation électrique pour un bâtiment à un moment donné
        
        Args:
            building_class (dict): Classe du bâtiment avec ses caractéristiques
            region_pattern (dict): Pattern régional de consommation
            timestamp (datetime): Moment de la mesure
            
        Returns:
            float: Consommation en kWh
        """
        # Consommation de base
        base = building_class['base_consumption']
        
        # Facteur temporel (heure de la journée)
        hour = timestamp.hour
        time_factor = 1.0
        
        if hour in building_class['peak_hours']:
            time_factor = 1.4  # Pic de consommation
        elif hour in building_class['low_hours']:
            time_factor = 0.6  # Consommation faible
        else:
            time_factor = 1.0  # Consommation normale
        
        # Facteur saisonnier (chaleur en Malaisie)
        seasonal_factor = building_class['seasonal_factor']
        if timestamp.month in [6, 7, 8]:  # Saison sèche (plus chaud)
            seasonal_factor *= 1.1
        
        # Facteur régional
        regional_factor = region_pattern['multiplier']
        climate_factor = region_pattern['climate_factor']
        
        # Variation aléatoire
        random_variation = random.uniform(1 - building_class['variation'], 
                                        1 + building_class['variation'])
        
        # Calcul final
        consumption = (base * time_factor * seasonal_factor * 
                      regional_factor * climate_factor * random_variation)
        
        # Événements spéciaux (pannes, pics de consommation)
        consumption = self._apply_special_events(consumption)
        
        return max(0.1, consumption)  # Minimum 0.1 kWh
    
    def _apply_special_events(self, base_consumption: float) -> float:
        """
        Applique des événements spéciaux qui peuvent affecter la consommation
        
        Args:
            base_consumption (float): Consommation de base
            
        Returns:
            float: Consommation ajustée
        """
        # Pic de chaleur extrême (1% de chance)
        if random.random() < 0.01:
            return base_consumption * (1.5 + random.random())
        
        # Orages tropicaux avec coupures partielles (0.5% de chance)
        if random.random() < 0.005:
            if random.random() < 0.7:
                return base_consumption * 0.2  # Coupure partielle
            else:
                return base_consumption * 1.4  # Systèmes de secours
        
        return base_consumption


def convert_numpy_types(obj):
    """Convertit les types numpy en types Python natifs pour la sérialisation JSON"""
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
    """Crée une réponse JSON en convertissant les types numpy"""
    try:
        clean_data = convert_numpy_types(data)
        return jsonify(clean_data)
    except Exception as e:
        logger.error(f"Erreur sérialisation JSON: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur de sérialisation des données',
            'details': str(e)
        })


# ===== FONCTIONS OSM =====

def convert_osm_to_buildings_df(buildings_osm: List[dict], zone_data: dict) -> pd.DataFrame:
    """
    Convertit les bâtiments OSM en DataFrame compatible avec le générateur
    
    Args:
        buildings_osm (List[dict]): Liste des bâtiments OSM
        zone_data (dict): Informations de la zone
        
    Returns:
        pd.DataFrame: DataFrame des bâtiments convertis
    """
    buildings_data = []
    
    for i, osm_building in enumerate(buildings_osm):
        # Mapping des tags OSM vers nos types de bâtiments
        building_type = map_osm_to_building_type(osm_building.get('tags', {}))
        
        # Coordonnées (centre du bâtiment)
        coords = osm_building.get('center', [0.0, 0.0])
        
        building = {
            'building_id': f"OSM_{zone_data.get('name', 'Zone')}_{i+1:04d}",
            'city': zone_data.get('name', 'Unknown'),
            'building_type': building_type,
            'latitude': coords[0] if len(coords) > 0 else 0.0,
            'longitude': coords[1] if len(coords) > 1 else 0.0,
            'region': zone_data.get('region', 'Unknown'),
            'state': zone_data.get('state', 'Unknown'),
            'base_consumption': generator.building_classes[building_type]['base_consumption'],
            'variation': generator.building_classes[building_type]['variation'],
            'osm_tags': osm_building.get('tags', {}),
            'osm_id': osm_building.get('id', f'unknown_{i}')
        }
        buildings_data.append(building)
    
    return pd.DataFrame(buildings_data)


def map_osm_to_building_type(osm_tags: dict) -> str:
    """
    Mappe les tags OSM vers nos types de bâtiments
    
    Args:
        osm_tags (dict): Tags OSM du bâtiment
        
    Returns:
        str: Type de bâtiment correspondant
    """
    building_tag = osm_tags.get('building', '').lower()
    amenity_tag = osm_tags.get('amenity', '').lower()
    shop_tag = osm_tags.get('shop', '').lower()
    landuse_tag = osm_tags.get('landuse', '').lower()
    
    # Mapping détaillé
    if building_tag in ['hospital'] or amenity_tag in ['hospital']:
        return 'Hospital'
    elif building_tag in ['clinic'] or amenity_tag in ['clinic', 'doctors']:
        return 'Clinic'
    elif building_tag in ['school', 'university'] or amenity_tag in ['school', 'university', 'college']:
        return 'School'
    elif building_tag in ['hotel'] or amenity_tag in ['hotel']:
        return 'Hotel'
    elif building_tag in ['restaurant'] or amenity_tag in ['restaurant', 'cafe', 'fast_food']:
        return 'Restaurant'
    elif building_tag in ['retail', 'commercial'] or shop_tag or amenity_tag in ['marketplace']:
        return 'Retail'
    elif building_tag in ['office'] or amenity_tag in ['office']:
        return 'Office'
    elif building_tag in ['warehouse', 'industrial'] or landuse_tag in ['industrial']:
        return 'Warehouse'
    elif building_tag in ['apartments', 'residential'] and 'apartment' in building_tag:
        return 'Apartment'
    elif building_tag in ['yes', 'house', 'residential'] or building_tag.startswith('residential'):
        return 'Residential'
    else:
        # Par défaut, considérer comme résidentiel
        return 'Residential'


def calculate_osm_stats(buildings_df: pd.DataFrame, timeseries_df: pd.DataFrame, zone_data: dict) -> dict:
    """
    Calcule les statistiques pour les données OSM
    
    Args:
        buildings_df (pd.DataFrame): DataFrame des bâtiments
        timeseries_df (pd.DataFrame): DataFrame des séries temporelles
        zone_data (dict): Informations de la zone
        
    Returns:
        dict: Statistiques calculées
    """
    try:
        # Statistiques des bâtiments
        building_counts = buildings_df['building_type'].value_counts().to_dict()
        total_buildings = len(buildings_df)
        
        # Statistiques de consommation
        if not timeseries_df.empty:
            total_consumption = timeseries_df['consumption_kwh'].sum()
            avg_consumption = timeseries_df['consumption_kwh'].mean()
            max_consumption = timeseries_df['consumption_kwh'].max()
            min_consumption = timeseries_df['consumption_kwh'].min()
            
            # Consommation par type de bâtiment
            consumption_by_type = timeseries_df.groupby('building_type')['consumption_kwh'].sum().to_dict()
        else:
            total_consumption = avg_consumption = max_consumption = min_consumption = 0
            consumption_by_type = {}
        
        # Analyse géographique
        lat_range = [buildings_df['latitude'].min(), buildings_df['latitude'].max()]
        lng_range = [buildings_df['longitude'].min(), buildings_df['longitude'].max()]
        
        return {
            'zone_info': {
                'name': zone_data.get('name', 'Unknown'),
                'region': zone_data.get('region', 'Unknown'),
                'total_buildings': total_buildings,
                'geographic_bounds': {
                    'latitude': lat_range,
                    'longitude': lng_range
                }
            },
            'building_distribution': building_counts,
            'consumption_stats': {
                'total_kwh': round(total_consumption, 2),
                'average_kwh': round(avg_consumption, 2),
                'max_kwh': round(max_consumption, 2),
                'min_kwh': round(min_consumption, 2),
                'by_building_type': {k: round(v, 2) for k, v in consumption_by_type.items()}
            },
            'data_quality': {
                'buildings_with_coords': len(buildings_df[(buildings_df['latitude'] != 0) & (buildings_df['longitude'] != 0)]),
                'buildings_without_coords': len(buildings_df[(buildings_df['latitude'] == 0) | (buildings_df['longitude'] == 0)]),
                'unique_building_types': len(building_counts),
                'generation_timestamp': datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Erreur calcul statistiques OSM: {e}")
        return {
            'error': str(e),
            'zone_info': zone_data,
            'building_distribution': {},
            'consumption_stats': {},
            'data_quality': {}
        }


def analyze_osm_data_quality(buildings_osm: List[dict]) -> dict:
    """
    Analyse la qualité des données OSM reçues
    
    Args:
        buildings_osm (List[dict]): Liste des bâtiments OSM
        
    Returns:
        dict: Analyse de qualité
    """
    if not buildings_osm:
        return {
            'total_buildings': 0,
            'buildings_with_tags': 0,
            'buildings_with_coords': 0,
            'tag_coverage': {},
            'quality_score': 0
        }
    
    buildings_with_tags = 0
    buildings_with_coords = 0
    tag_frequency = {}
    
    for building in buildings_osm:
        # Vérification des tags
        tags = building.get('tags', {})
        if tags:
            buildings_with_tags += 1
            for tag_key in tags.keys():
                tag_frequency[tag_key] = tag_frequency.get(tag_key, 0) + 1
        
        # Vérification des coordonnées
        coords = building.get('center', [])
        if len(coords) >= 2 and coords[0] != 0 and coords[1] != 0:
            buildings_with_coords += 1
    
    # Score de qualité (0-100)
    coord_score = (buildings_with_coords / len(buildings_osm)) * 50
    tag_score = (buildings_with_tags / len(buildings_osm)) * 50
    quality_score = coord_score + tag_score
    
    return {
        'total_buildings': len(buildings_osm),
        'buildings_with_tags': buildings_with_tags,
        'buildings_with_coords': buildings_with_coords,
        'tag_coverage': tag_frequency,
        'quality_score': round(quality_score, 1),
        'recommendations': generate_quality_recommendations(buildings_osm, quality_score)
    }


def generate_quality_recommendations(buildings_osm: List[dict], quality_score: float) -> List[str]:
    """
    Génère des recommandations basées sur la qualité des données OSM
    
    Args:
        buildings_osm (List[dict]): Liste des bâtiments OSM
        quality_score (float): Score de qualité calculé
        
    Returns:
        List[str]: Liste des recommandations
    """
    recommendations = []
    
    if quality_score >= 80:
        recommendations.append("✅ Excellente qualité des données OSM")
    elif quality_score >= 60:
        recommendations.append("✅ Bonne qualité des données OSM")
        recommendations.append("💡 Vérifiez les bâtiments sans coordonnées")
    elif quality_score >= 40:
        recommendations.append("⚠️ Qualité moyenne des données OSM")
        recommendations.append("💡 Ajoutez plus de tags descriptifs")
        recommendations.append("💡 Vérifiez la précision des coordonnées")
    else:
        recommendations.append("❌ Qualité faible des données OSM")
        recommendations.append("🔧 Enrichissez les données avec plus de tags")
        recommendations.append("🔧 Vérifiez et corrigez les coordonnées manquantes")
        recommendations.append("🔧 Considérez une validation manuelle")
    
    return recommendations


def prepare_sample_data(buildings_df: pd.DataFrame, timeseries_df: pd.DataFrame, sample_size: int = 10) -> dict:
    """
    Prépare un échantillon de données pour l'aperçu
    
    Args:
        buildings_df (pd.DataFrame): DataFrame des bâtiments
        timeseries_df (pd.DataFrame): DataFrame des séries temporelles
        sample_size (int): Taille de l'échantillon
        
    Returns:
        dict: Échantillon de données
    """
    try:
        # Échantillon de bâtiments
        sample_buildings = buildings_df.head(sample_size).to_dict('records')
        
        # Échantillon de données temporelles (derniers points)
        if not timeseries_df.empty:
            sample_timeseries = timeseries_df.tail(sample_size * 5).to_dict('records')
        else:
            sample_timeseries = []
        
        return {
            'buildings_sample': sample_buildings,
            'timeseries_sample': sample_timeseries,
            'sample_info': {
                'buildings_shown': len(sample_buildings),
                'timeseries_shown': len(sample_timeseries),
                'total_buildings': len(buildings_df),
                'total_timeseries': len(timeseries_df)
            }
        }
    except Exception as e:
        logger.error(f"Erreur préparation échantillon: {e}")
        return {
            'buildings_sample': [],
            'timeseries_sample': [],
            'sample_info': {'error': str(e)}
        }


# ===== INITIALISATION DU GÉNÉRATEUR =====
# CORRECTION CRITIQUE: Initialiser le générateur AVANT les routes
try:
    generator = ElectricityDataGenerator()
    logger.info("✅ Générateur principal initialisé avec succès")
except Exception as e:
    logger.error(f"❌ Erreur critique lors de l'initialisation du générateur: {e}")
    generator = None


# ===== ROUTES FLASK =====

@app.route('/')
def index():
    """Page d'accueil de l'application"""
    return render_template('index.html')


@app.route('/api/stats')
def api_stats():
    """API pour obtenir les statistiques du système"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
        
        # Statistiques générales
        stats = {
            'total_cities': len(generator.malaysia_locations),
            'building_types': len(generator.building_classes),
            'distribution_method': 'Distribution intelligente' if BUILDING_DISTRIBUTOR_AVAILABLE else 'Distribution basique',
            'system_capabilities': {
                'building_distributor': BUILDING_DISTRIBUTOR_AVAILABLE,
                'enhanced_coordinates': ENHANCED_COORDINATES_AVAILABLE,
                'validation_system': False,
                'climate_patterns': True,
                'osm_integration': True
            },
            'available_cities': list(generator.malaysia_locations.keys()),
            'available_building_types': list(generator.building_classes.keys()),
            'regions': list(set(city['region'] for city in generator.malaysia_locations.values())),
            'system_status': 'Opérationnel'
        }
        
        return safe_json_response(stats)
        
    except Exception as e:
        logger.error(f"Erreur API stats: {e}")
        return jsonify({
            'error': str(e),
            'system_status': 'Erreur'
        }), 500


@app.route('/api/real-data-status')
def real_data_status():
    """API pour le statut des données réelles"""
    try:
        # Simulation du statut - à remplacer par vraies données si disponibles
        status = {
            'real_data_available': False,
            'simulated_data_only': True,
            'data_sources': [
                'Distribution intelligente de bâtiments',
                'Patterns de consommation régionaux',
                'Facteurs climatiques Malaysia',
                'Événements spéciaux simulés'
            ],
            'quality_indicators': {
                'distribution_accuracy': 85,
                'temporal_patterns': 90,
                'regional_variation': 80,
                'climate_integration': 95
            },
            'last_update': datetime.now().isoformat(),
            'recommendations': [
                'Données simulées basées sur patterns réalistes',
                'Validation avec données réelles recommandée',
                'Calibrage possible avec mesures terrain'
            ]
        }
        
        return safe_json_response(status)
        
    except Exception as e:
        logger.error(f"Erreur API real-data-status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/sample')
def sample_generation():
    """Génère un échantillon de démonstration"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
        
        logger.info("🧪 Génération d'un échantillon de démonstration")
        
        # Paramètres de l'échantillon
        city_name = 'Kuala Lumpur'
        num_buildings = 10
        start_date = '2024-01-01'
        end_date = '2024-01-02'
        freq = '1H'
        
        # Génération des bâtiments
        buildings_df = generator.generate_buildings_dataframe(city_name, num_buildings)
        
        # Génération des séries temporelles
        timeseries_df = generator.generate_timeseries_data(buildings_df, start_date, end_date, freq)
        
        # Préparation de la réponse
        response_data = {
            'success': True,
            'sample_info': {
                'city': city_name,
                'num_buildings': len(buildings_df),
                'time_points': len(timeseries_df),
                'period': f"{start_date} à {end_date}",
                'frequency': freq
            },
            'buildings': buildings_df.head().to_dict('records'),
            'timeseries': timeseries_df.head(20).to_dict('records'),
            'statistics': {
                'building_distribution': buildings_df['building_type'].value_counts().to_dict(),
                'total_consumption': round(timeseries_df['consumption_kwh'].sum(), 2),
                'average_consumption': round(timeseries_df['consumption_kwh'].mean(), 2)
            }
        }
        
        return safe_json_response(response_data)
        
    except Exception as e:
        logger.error(f"Erreur génération échantillon: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== ROUTE OSM PRINCIPALE =====

@app.route('/generate-from-osm', methods=['POST'])
def generate_from_osm():
    """
    Route principale pour générer des données à partir d'OpenStreetMap
    """
    try:
        logger.info("🗺️ Début génération basée sur OSM")
        
        if not generator:
            raise Exception("Générateur non initialisé")
        
        # Récupération des données de la requête
        data = request.get_json()
        if not data:
            raise ValueError("Données JSON requises")
        
        zone_data = data.get('zone_data', {})
        buildings_osm = data.get('buildings_osm', [])
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', '2024-01-31')
        freq = data.get('freq', '30T')
        
        logger.info(f"Zone: {zone_data.get('name', 'Unknown')}")
        logger.info(f"Bâtiments OSM: {len(buildings_osm)}")
        logger.info(f"Période: {start_date} à {end_date}")
        logger.info(f"Fréquence: {freq}")
        
        # Validation des données
        if not buildings_osm:
            raise ValueError("Aucun bâtiment OSM fourni")
        
        # Convertir les bâtiments OSM en DataFrame compatible
        buildings_df = convert_osm_to_buildings_df(buildings_osm, zone_data)
        logger.info(f"✅ {len(buildings_df)} bâtiments convertis")
        
        # Générer les séries temporelles
        timeseries_df = generator.generate_timeseries_data(
            buildings_df, start_date, end_date, freq
        )
        logger.info(f"✅ {len(timeseries_df)} enregistrements de consommation générés")
        
        # Statistiques et validation
        stats = calculate_osm_stats(buildings_df, timeseries_df, zone_data)
        
        # Analyse de la qualité OSM
        osm_quality = analyze_osm_data_quality(buildings_osm)
        
        # Échantillon pour l'aperçu
        sample_data = prepare_sample_data(buildings_df, timeseries_df)
        
        # Réponse complète
        response_data = {
            'success': True,
            'generation_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'zone_info': stats['zone_info'],
            'data_summary': {
                'total_buildings': len(buildings_df),
                'total_consumption_records': len(timeseries_df),
                'time_range': f"{start_date} to {end_date}",
                'frequency': freq,
                'building_types': list(buildings_df['building_type'].unique())
            },
            'building_distribution': stats['building_distribution'],
            'consumption_statistics': stats['consumption_stats'],
            'osm_quality_analysis': osm_quality,
            'sample_data': sample_data,
            'export_options': {
                'csv_available': True,
                'json_available': True,
                'excel_available': True
            },
            'recommendations': osm_quality.get('recommendations', [])
        }
        
        # Stockage temporaire des données pour export (optionnel)
        # Ici vous pourriez sauvegarder les DataFrames pour un export ultérieur
        
        logger.info("✅ Génération OSM terminée avec succès")
        return safe_json_response(response_data)
        
    except ValueError as ve:
        logger.error(f"Erreur de validation: {ve}")
        return jsonify({
            'success': False,
            'error': 'Données invalides',
            'details': str(ve)
        }), 400
        
    except Exception as e:
        logger.error(f"Erreur génération OSM: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur',
            'details': str(e)
        }), 500


# ===== ROUTES ADDITIONNELLES =====

@app.route('/api/cities')
def api_cities():
    """API pour obtenir la liste des villes disponibles"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
        
        cities_data = []
        for city_name, city_info in generator.malaysia_locations.items():
            cities_data.append({
                'name': city_name,
                'population': city_info['population'],
                'region': city_info['region'],
                'state': city_info['state'],
                'coordinates': city_info['coordinates']
            })
        
        # Tri par population décroissante
        cities_data.sort(key=lambda x: x['population'], reverse=True)
        
        return safe_json_response({
            'success': True,
            'cities': cities_data,
            'total_cities': len(cities_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur API cities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/building-types')
def api_building_types():
    """API pour obtenir les types de bâtiments disponibles"""
    try:
        if not generator:
            raise Exception("Générateur non initialisé")
        
        building_types_data = []
        for type_name, type_info in generator.building_classes.items():
            building_types_data.append({
                'name': type_name,
                'description': type_info['description'],
                'base_consumption': type_info['base_consumption'],
                'variation': type_info['variation'],
                'peak_hours': type_info['peak_hours'],
                'seasonal_factor': type_info['seasonal_factor']
            })
        
        return safe_json_response({
            'success': True,
            'building_types': building_types_data,
            'total_types': len(building_types_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur API building-types: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== INTÉGRATION DES MODULES ADDITIONNELS =====

# Intégration de l'API de prédiction si disponible
if COMPLETE_INTEGRATION_AVAILABLE:
    try:
        create_complete_integration(app, generator)
        logger.info("✅ Intégration complète activée")
    except Exception as e:
        logger.error(f"Erreur intégration complète: {e}")

# Gestion d'erreur globale
@app.errorhandler(404)
def not_found_error(error):
    """Gestionnaire pour les erreurs 404"""
    return jsonify({
        'success': False,
        'error': 'Route non trouvée',
        'available_routes': [
            '/ - Page d\'accueil',
            '/api/stats - Statistiques système',
            '/api/cities - Liste des villes',
            '/api/building-types - Types de bâtiments',
            '/api/real-data-status - Statut des données',
            '/generate-from-osm - Génération OSM (POST)',
            '/sample - Échantillon de démonstration'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire pour les erreurs 500"""
    return jsonify({
        'success': False,
        'error': 'Erreur interne du serveur',
        'details': 'Consultez les logs pour plus d\'informations'
    }), 500


# ===== POINT D'ENTRÉE PRINCIPAL =====

if __name__ == '__main__':
    print("=" * 60)
    print("🏢 GÉNÉRATEUR DE DONNÉES ÉLECTRIQUES MALAYSIA")
    print("=" * 60)
    print()
    
    # Vérification de l'état du système
    print("🔍 ÉTAT DU SYSTÈME:")
    print(f"🏗️ Distributeur: {'Intelligent' if BUILDING_DISTRIBUTOR_AVAILABLE else 'Basique'}")
    print(f"📍 Coordonnées: {'Améliorées' if ENHANCED_COORDINATES_AVAILABLE else 'Classiques'}")
    print(f"🔗 Intégration: {'Complète' if COMPLETE_INTEGRATION_AVAILABLE else 'Basique'}")
    
    if generator:
        print(f"🌆 Villes: {len(generator.malaysia_locations)}")
        print(f"🏢 Types de bâtiments: {len(generator.building_classes)}")
        print("✅ Générateur: Initialisé")
    else:
        print("❌ ERREUR: Générateur non initialisé")
        print("🔧 Vérifiez les dépendances et relancez l'application")
    
    print()
    print("🌐 URLS DISPONIBLES:")
    urls = [
        "http://localhost:5000 - Interface principale",
        "http://localhost:5000/api/stats - Statistiques système",
        "http://localhost:5000/api/cities - Liste des villes",
        "http://localhost:5000/api/building-types - Types de bâtiments",
        "http://localhost:5000/api/real-data-status - Statut des données",
        "http://localhost:5000/generate-from-osm - Génération OSM (POST)",
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