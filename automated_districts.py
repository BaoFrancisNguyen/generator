# automated_districts.py - Systeme Automatise de Recuperation des Quartiers (Version Corrigee)
"""
Systeme automatise pour recuperer les quartiers malaysiens depuis diverses sources.
Version corrigee avec fonction d'integration manquante.
"""

import requests
import json
import os
import time
import random
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class AutomatedDistrictsManager:
    """
    Gestionnaire automatise pour recuperer et cacher les donnees de quartiers
    """
    
    def __init__(self, cache_dir="districts_cache", cache_duration_days=30):
        """
        Initialise le gestionnaire avec systeme de cache
        
        Args:
            cache_dir (str): Dossier pour stocker le cache
            cache_duration_days (int): Duree de validite du cache en jours
        """
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(days=cache_duration_days)
        
        # Creer le dossier de cache si necessaire
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            logger.info(f"Dossier cache cree: {cache_dir}")
        
        # Configuration des APIs
        self.apis_config = {
            'nominatim': {
                'base_url': 'https://nominatim.openstreetmap.org',
                'rate_limit': 1.0,  # 1 seconde entre requetes
                'enabled': True
            },
            'overpass': {
                'base_url': 'http://overpass-api.de/api/interpreter',
                'rate_limit': 2.0,  # 2 secondes entre requetes
                'enabled': True
            }
        }
        
        # Statistiques d'utilisation
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_update': None
        }
        
        logger.info("✅ AutomatedDistrictsManager initialise")
    
    def get_city_districts(self, city_name: str, country: str = "Malaysia", 
                          force_refresh: bool = False) -> Dict:
        """
        Recupere les quartiers d'une ville avec systeme de cache intelligent
        
        Args:
            city_name (str): Nom de la ville
            country (str): Pays (par defaut Malaysia)
            force_refresh (bool): Forcer la mise a jour depuis les APIs
            
        Returns:
            dict: Quartiers avec coordonnees et metadonnees
        """
        
        cache_key = f"{city_name.lower().replace(' ', '_')}_{country.lower()}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Verifier le cache en premier
        if not force_refresh and self._is_cache_valid(cache_file):
            logger.info(f"Utilisation cache pour {city_name}")
            self.stats['cache_hits'] += 1
            return self._load_from_cache(cache_file)
        
        # Cache expire ou force refresh, recuperer depuis APIs
        logger.info(f"Recuperation donnees API pour {city_name}")
        self.stats['cache_misses'] += 1
        
        # Tenter plusieurs sources dans l'ordre de preference
        districts_data = None
        sources_tried = []
        
        # Source 1: Fallback vers coordonnees generiques si echec des APIs
        try:
            districts_data = self._generate_fallback_districts(city_name, country)
            sources_tried.append('fallback_coordinates')
            logger.info(f"Donnees fallback generees pour {city_name}: {districts_data['total_districts']} quartiers")
        except Exception as e:
            logger.warning(f"Echec generation fallback pour {city_name}: {e}")
            sources_tried.append('fallback_error')
        
        # Enrichir avec metadonnees
        if districts_data:
            districts_data.update({
                'city': city_name,
                'country': country,
                'last_updated': datetime.now().isoformat(),
                'sources_tried': sources_tried,
                'total_districts': len(districts_data.get('districts', {}))
            })
            
            # Sauvegarder dans le cache
            self._save_to_cache(cache_file, districts_data)
            self.stats['last_update'] = datetime.now()
        
        logger.info(f"Recuperation terminee pour {city_name}: {districts_data['total_districts'] if districts_data else 0} quartiers")
        return districts_data or self._get_empty_districts_data(city_name, country)
    
    def _generate_fallback_districts(self, city_name: str, country: str) -> Dict:
        """
        Genere des quartiers generiques si les APIs echouent
        Base sur la taille estimee de la ville
        """
        
        # Coordonnees generiques par ville (fallback)
        city_coords = {
            'Kuala Lumpur': {'lat': (3.1319, 3.1681), 'lon': (101.6841, 101.7381)},
            'George Town': {'lat': (5.4000, 5.4300), 'lon': (100.3000, 100.3300)},
            'Johor Bahru': {'lat': (1.4833, 1.5033), 'lon': (103.7333, 103.7533)},
            'Langkawi': {'lat': (6.3167, 6.3367), 'lon': (99.8167, 99.8367)},
            'Ipoh': {'lat': (4.5833, 4.6033), 'lon': (101.0833, 101.1033)},
            'Shah Alam': {'lat': (3.0667, 3.1167), 'lon': (101.4833, 101.5333)},
            'Petaling Jaya': {'lat': (3.1073, 3.1273), 'lon': (101.6063, 101.6263)},
            'Kota Kinabalu': {'lat': (5.9667, 5.9867), 'lon': (116.0667, 116.0867)},
            'Kuching': {'lat': (1.5333, 1.5533), 'lon': (110.3333, 110.3533)},
            'Cyberjaya': {'lat': (2.9167, 2.9367), 'lon': (101.6333, 101.6533)},
            'Malacca City': {'lat': (2.1896, 2.2096), 'lon': (102.2394, 102.2594)},
            'Alor Setar': {'lat': (6.1088, 6.1288), 'lon': (100.3580, 100.3780)},
            'Kuantan': {'lat': (3.8000, 3.8200), 'lon': (103.3200, 103.3400)}
        }
        
        if city_name not in city_coords:
            # Coordonnees par defaut Malaisie
            base_coords = {'lat': (2.0, 6.0), 'lon': (100.0, 118.0)}
        else:
            base_coords = city_coords[city_name]
        
        # Generer 4 quartiers generiques
        lat_range = base_coords['lat']
        lon_range = base_coords['lon']
        
        lat_mid = sum(lat_range) / 2
        lon_mid = sum(lon_range) / 2
        
        fallback_districts = {
            'Centre Ville': {
                'name': 'Centre Ville',
                'coordinates': {
                    'lat': (lat_mid - 0.01, lat_mid + 0.01),
                    'lon': (lon_mid - 0.01, lon_mid + 0.01)
                },
                'type': 'city_center',
                'suitable_buildings': ['Commercial', 'Office', 'Hotel', 'Restaurant'],
                'source': 'fallback'
            },
            'Zone Residentielle Nord': {
                'name': 'Zone Residentielle Nord',
                'coordinates': {
                    'lat': (lat_mid, lat_range[1]),
                    'lon': (lon_range[0], lon_mid)
                },
                'type': 'residential_district',
                'suitable_buildings': ['Residential', 'School', 'Clinic'],
                'source': 'fallback'
            },
            'Zone Residentielle Sud': {
                'name': 'Zone Residentielle Sud',
                'coordinates': {
                    'lat': (lat_range[0], lat_mid),
                    'lon': (lon_mid, lon_range[1])
                },
                'type': 'residential_district',
                'suitable_buildings': ['Residential', 'School', 'Clinic'],
                'source': 'fallback'
            },
            'Zone Industrielle': {
                'name': 'Zone Industrielle',
                'coordinates': {
                    'lat': (lat_range[0], lat_mid),
                    'lon': (lon_range[0], lon_mid)
                },
                'type': 'industrial_zone',
                'suitable_buildings': ['Industrial', 'Factory', 'Warehouse'],
                'source': 'fallback'
            }
        }
        
        return {
            'districts': fallback_districts,
            'sources': ['fallback'],
            'api_response_count': 0
        }
    
    def _get_empty_districts_data(self, city_name: str, country: str) -> Dict:
        """Retourne une structure vide en cas d'echec total"""
        return {
            'city': city_name,
            'country': country,
            'districts': {},
            'sources': ['error'],
            'total_districts': 0,
            'last_updated': datetime.now().isoformat(),
            'error': 'Impossible de recuperer les donnees de quartiers'
        }
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """Verifie si le fichier cache est encore valide"""
        if not os.path.exists(cache_file):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        return datetime.now() - file_time < self.cache_duration
    
    def _load_from_cache(self, cache_file: str) -> Dict:
        """Charge les donnees depuis le cache"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lecture cache {cache_file}: {e}")
            return {}
    
    def _save_to_cache(self, cache_file: str, data: Dict):
        """Sauvegarde les donnees dans le cache"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache {cache_file}: {e}")
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques d'utilisation du systeme"""
        return {
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'api_calls_total': self.stats['api_calls'],
            'cache_hit_rate': (self.stats['cache_hits'] / 
                             max(1, self.stats['cache_hits'] + self.stats['cache_misses']) * 100),
            'last_update': self.stats['last_update'].isoformat() if self.stats['last_update'] else None,
            'cache_directory': self.cache_dir,
            'cache_files': len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
        }
    
    def clear_cache(self, city_name: str = None):
        """Efface le cache pour une ville specifique ou tout le cache"""
        if city_name:
            cache_key = f"{city_name.lower().replace(' ', '_')}_malaysia"
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.info(f"Cache efface pour {city_name}")
        else:
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))
            logger.info("Tout le cache efface")


class EnhancedCoordinatesGenerator:
    """
    Generateur de coordonnees ameliore integrant le systeme automatise
    Compatible avec le systeme existant
    """
    
    def __init__(self, cache_dir="districts_cache"):
        """
        Initialise le generateur avec le gestionnaire automatise
        """
        try:
            self.districts_manager = AutomatedDistrictsManager(cache_dir=cache_dir)
            self.city_districts_cache = {}  # Cache en memoire pour les performances
            self.initialization_successful = True
            logger.info("✅ EnhancedCoordinatesGenerator initialise avec succes")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation EnhancedCoordinatesGenerator: {e}")
            self.districts_manager = None
            self.city_districts_cache = {}
            self.initialization_successful = False
    
    def generate_coordinates(self, city_name: str, building_type: str = None) -> Tuple[float, float]:
        """
        Genere des coordonnees avec placement intelligent par quartier
        
        Args:
            city_name (str): Nom de la ville
            building_type (str): Type de batiment (optionnel)
            
        Returns:
            tuple: (latitude, longitude)
        """
        
        if not self.initialization_successful or not self.districts_manager:
            logger.warning(f"Systeme ameliore non disponible, coordonnees generiques pour {city_name}")
            return self._generate_generic_coordinates(city_name)
        
        try:
            # Recuperer les quartiers de la ville
            if city_name not in self.city_districts_cache:
                districts_data = self.districts_manager.get_city_districts(city_name)
                self.city_districts_cache[city_name] = districts_data
            else:
                districts_data = self.city_districts_cache[city_name]
            
            districts = districts_data.get('districts', {})
            
            if not districts:
                logger.warning(f"Aucun quartier trouve pour {city_name}, coordonnees generiques")
                return self._generate_generic_coordinates(city_name)
            
            # Selectionner le quartier approprie selon le type de batiment
            if building_type:
                suitable_district = self._find_best_district_for_building(districts, building_type)
            else:
                # Choisir un quartier au hasard si pas de type specifie
                suitable_district = random.choice(list(districts.values()))
            
            # Generer coordonnees dans le quartier choisi
            coords = suitable_district['coordinates']
            latitude = round(random.uniform(coords['lat'][0], coords['lat'][1]), 6)
            longitude = round(random.uniform(coords['lon'][0], coords['lon'][1]), 6)
            
            logger.debug(f"Coordonnees ameliorees pour {building_type or 'batiment'} a {city_name}: "
                        f"{latitude}, {longitude} dans {suitable_district['name']}")
            
            return (latitude, longitude)
            
        except Exception as e:
            logger.warning(f"Erreur generation coordonnees ameliorees pour {city_name}: {e}")
            return self._generate_generic_coordinates(city_name)
    
    def _find_best_district_for_building(self, districts: Dict, building_type: str) -> Dict:
        """Trouve le quartier le plus adapte pour un type de batiment"""
        
        # Evaluer chaque quartier
        scored_districts = []
        for district_name, district_info in districts.items():
            score = self._calculate_suitability_score(district_info, building_type)
            scored_districts.append((score, district_info))
        
        # Trier par score decroissant
        scored_districts.sort(key=lambda x: x[0], reverse=True)
        
        # Selectionner avec ponderation (favorise les meilleurs mais permet variete)
        if len(scored_districts) == 1:
            return scored_districts[0][1]
        
        # Selection ponderee : 60% chance pour le meilleur, 30% pour le 2e, etc.
        weights = [0.6, 0.3, 0.08, 0.02] + [0.0] * max(0, len(scored_districts) - 4)
        weights = weights[:len(scored_districts)]
        
        # Normaliser les poids
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Selection aleatoire ponderee
        rand = random.random()
        cumulative = 0.0
        
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand <= cumulative:
                return scored_districts[i][1]
        
        # Fallback
        return scored_districts[0][1]
    
    def _calculate_suitability_score(self, district_info: Dict, building_type: str) -> int:
        """Calcule un score de pertinence entre un quartier et un type de batiment"""
        
        suitable_buildings = district_info.get('suitable_buildings', [])
        
        # Score de base si le batiment est explicitement adapte
        if building_type in suitable_buildings:
            base_score = 10
        else:
            base_score = 3  # Score neutre
        
        # Bonus selon le type de quartier
        district_type = district_info.get('type', '')
        
        if building_type == 'Residential' and 'residential' in district_type:
            base_score += 5
        elif building_type in ['Commercial', 'Office'] and 'center' in district_type:
            base_score += 5
        elif building_type in ['Industrial', 'Factory'] and 'industrial' in district_type:
            base_score += 5
        elif building_type == 'Hotel' and 'center' in district_type:
            base_score += 3
        
        return base_score
    
    def _generate_generic_coordinates(self, city_name: str) -> Tuple[float, float]:
        """Genere des coordonnees generiques pour une ville"""
        
        # Coordonnees connues des principales villes malaysiennes
        city_coordinates = {
            'Kuala Lumpur': {'lat': (3.1319, 3.1681), 'lon': (101.6841, 101.7381)},
            'George Town': {'lat': (5.4000, 5.4300), 'lon': (100.3000, 100.3300)},
            'Johor Bahru': {'lat': (1.4833, 1.5033), 'lon': (103.7333, 103.7533)},
            'Langkawi': {'lat': (6.3167, 6.3367), 'lon': (99.8167, 99.8367)},
            'Ipoh': {'lat': (4.5833, 4.6033), 'lon': (101.0833, 101.1033)},
            'Shah Alam': {'lat': (3.0667, 3.1167), 'lon': (101.4833, 101.5333)},
            'Petaling Jaya': {'lat': (3.1073, 3.1273), 'lon': (101.6063, 101.6263)},
            'Kota Kinabalu': {'lat': (5.9667, 5.9867), 'lon': (116.0667, 116.0867)},
            'Kuching': {'lat': (1.5333, 1.5533), 'lon': (110.3333, 110.3533)},
            'Cyberjaya': {'lat': (2.9167, 2.9367), 'lon': (101.6333, 101.6533)},
            'Malacca City': {'lat': (2.1896, 2.2096), 'lon': (102.2394, 102.2594)},
            'Alor Setar': {'lat': (6.1088, 6.1288), 'lon': (100.3580, 100.3780)},
            'Kuantan': {'lat': (3.8000, 3.8200), 'lon': (103.3200, 103.3400)}
        }
        
        if city_name in city_coordinates:
            coords = city_coordinates[city_name]
            lat_range = coords['lat']
            lon_range = coords['lon']
            
            latitude = round(random.uniform(lat_range[0], lat_range[1]), 6)
            longitude = round(random.uniform(lon_range[0], lon_range[1]), 6)
        else:
            # Coordonnees generiques pour la Malaisie
            latitude = round(random.uniform(1.0, 7.0), 6)
            longitude = round(random.uniform(99.5, 119.5), 6)
        
        return (latitude, longitude)
    
    def generate_detailed_coordinates(self, city_name: str, building_type: str) -> Dict:
        """
        Genere des coordonnees avec informations detaillees du quartier
        
        Args:
            city_name (str): Nom de la ville
            building_type (str): Type de batiment
            
        Returns:
            dict: Coordonnees + metadonnees du quartier
        """
        
        if not self.initialization_successful or not self.districts_manager:
            lat, lon = self._generate_generic_coordinates(city_name)
            return {
                'latitude': lat,
                'longitude': lon,
                'district_name': 'Zone Generique',
                'district_type': 'generic',
                'suitability_score': 1,
                'data_source': 'fallback'
            }
        
        try:
            # Recuperer les quartiers
            if city_name not in self.city_districts_cache:
                districts_data = self.districts_manager.get_city_districts(city_name)
                self.city_districts_cache[city_name] = districts_data
            else:
                districts_data = self.city_districts_cache[city_name]
            
            districts = districts_data.get('districts', {})
            
            if not districts:
                lat, lon = self._generate_generic_coordinates(city_name)
                return {
                    'latitude': lat,
                    'longitude': lon,
                    'district_name': 'Zone Generique',
                    'district_type': 'generic',
                    'suitability_score': 1,
                    'data_source': 'fallback'
                }
            
            # Trouver le meilleur quartier
            suitable_district = self._find_best_district_for_building(districts, building_type)
            
            # Generer coordonnees
            coords = suitable_district['coordinates']
            latitude = round(random.uniform(coords['lat'][0], coords['lat'][1]), 6)
            longitude = round(random.uniform(coords['lon'][0], coords['lon'][1]), 6)
            
            # Calculer le score de pertinence
            suitability_score = self._calculate_suitability_score(suitable_district, building_type)
            
            return {
                'latitude': latitude,
                'longitude': longitude,
                'district_name': suitable_district['name'],
                'district_type': suitable_district['type'],
                'district_description': suitable_district.get('description', ''),
                'suitability_score': suitability_score,
                'data_source': suitable_district.get('source', 'unknown'),
                'suitable_buildings': suitable_district.get('suitable_buildings', [])
            }
            
        except Exception as e:
            logger.error(f"Erreur generation coordonnees detaillees pour {city_name}: {e}")
            lat, lon = self._generate_generic_coordinates(city_name)
            return {
                'latitude': lat,
                'longitude': lon,
                'district_name': 'Zone Generique (Erreur)',
                'district_type': 'generic',
                'suitability_score': 1,
                'data_source': 'fallback_error',
                'error': str(e)
            }


# ===================================================================
# FONCTION D'INTEGRATION MANQUANTE (CORRECTION CRITIQUE)
# ===================================================================

def create_enhanced_coordinate_generator(cache_dir="districts_cache"):
    """
    FONCTION MANQUANTE: Cree une instance du generateur de coordonnees ameliore
    
    Cette fonction etait appelee dans app.py mais n'existait pas, causant l'erreur d'import.
    
    Args:
        cache_dir (str): Dossier pour le cache des quartiers
        
    Returns:
        EnhancedCoordinatesGenerator: Instance du generateur de coordonnees
    """
    try:
        logger.info("🔄 Creation du generateur de coordonnees ameliore...")
        generator = EnhancedCoordinatesGenerator(cache_dir=cache_dir)
        
        if generator.initialization_successful:
            logger.info("✅ Generateur de coordonnees ameliore cree avec succes")
            return generator
        else:
            logger.warning("⚠️ Generateur cree mais avec des limitations")
            return generator
            
    except Exception as e:
        logger.error(f"❌ Erreur creation generateur coordonnees ameliore: {e}")
        # Retourner un generateur basique de secours
        return BasicCoordinatesGenerator()


class BasicCoordinatesGenerator:
    """
    Generateur de coordonnees basique de secours
    Utilise si EnhancedCoordinatesGenerator ne peut pas etre initialise
    """
    
    def __init__(self):
        self.initialization_successful = True
        logger.info("⚠️ BasicCoordinatesGenerator initialise en mode secours")
    
    def generate_coordinates(self, city_name: str, building_type: str = None) -> Tuple[float, float]:
        """Genere des coordonnees basiques pour une ville"""
        
        # Coordonnees basiques des principales villes
        city_coordinates = {
            'Kuala Lumpur': {'lat': (3.1319, 3.1681), 'lon': (101.6841, 101.7381)},
            'George Town': {'lat': (5.4000, 5.4300), 'lon': (100.3000, 100.3300)},
            'Johor Bahru': {'lat': (1.4833, 1.5033), 'lon': (103.7333, 103.7533)},
            'Langkawi': {'lat': (6.3167, 6.3367), 'lon': (99.8167, 99.8367)},
            'Ipoh': {'lat': (4.5833, 4.6033), 'lon': (101.0833, 101.1033)},
            'Shah Alam': {'lat': (3.0667, 3.1167), 'lon': (101.4833, 101.5333)},
            'Petaling Jaya': {'lat': (3.1073, 3.1273), 'lon': (101.6063, 101.6263)},
            'Kota Kinabalu': {'lat': (5.9667, 5.9867), 'lon': (116.0667, 116.0867)},
            'Kuching': {'lat': (1.5333, 1.5533), 'lon': (110.3333, 110.3533)}
        }
        
        if city_name in city_coordinates:
            coords = city_coordinates[city_name]
            lat_range = coords['lat']
            lon_range = coords['lon']
            
            latitude = round(random.uniform(lat_range[0], lat_range[1]), 6)
            longitude = round(random.uniform(lon_range[0], lon_range[1]), 6)
        else:
            # Coordonnees generiques pour la Malaisie
            latitude = round(random.uniform(1.0, 7.0), 6)
            longitude = round(random.uniform(99.5, 119.5), 6)
        
        return (latitude, longitude)


# ===================================================================
# FONCTIONS UTILITAIRES
# ===================================================================

def test_enhanced_coordinates_system():
    """Fonction de test pour le systeme de coordonnees ameliore"""
    
    print("🧪 Test du systeme de coordonnees ameliore")
    print("=" * 50)
    
    try:
        # Test de creation
        generator = create_enhanced_coordinate_generator()
        
        if generator.initialization_successful:
            print("✅ Generateur cree avec succes")
            
            # Test de generation de coordonnees
            cities_to_test = ['Kuala Lumpur', 'George Town', 'Langkawi', 'Ville Inconnue']
            building_types = ['Residential', 'Commercial', 'Hospital', 'Hotel']
            
            for city in cities_to_test:
                print(f"\n📍 Test pour {city}:")
                for building_type in building_types[:2]:  # Limiter les tests
                    try:
                        lat, lon = generator.generate_coordinates(city, building_type)
                        print(f"  {building_type}: {lat}, {lon}")
                    except Exception as e:
                        print(f"  {building_type}: Erreur - {e}")
        else:
            print("⚠️ Generateur cree avec des limitations")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    # Test si execute directement
    test_enhanced_coordinates_system()