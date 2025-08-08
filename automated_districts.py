# automated_districts.py - Systeme Automatise de Recuperation des Quartiers (Complet)
"""
Systeme automatise pour recuperer les quartiers malaysiens depuis diverses sources :
- APIs geographiques (OpenStreetMap, Google, Nominatim)
- Fichiers geographiques (GeoJSON, Shapefile)
- Cache local pour optimiser les performances
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
    Utilise plusieurs sources pour maximiser la couverture geographique
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
        
        logger.info("AutomatedDistrictsManager initialise")
    
    
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
        
        # Source 1: Nominatim (rapide et fiable)
        if self.apis_config['nominatim']['enabled']:
            try:
                districts_data = self._get_from_nominatim(city_name, country)
                if districts_data and districts_data['districts']:
                    sources_tried.append('nominatim_success')
                    logger.info(f"Donnees recuperees via Nominatim: {len(districts_data['districts'])} quartiers")
                else:
                    sources_tried.append('nominatim_empty')
            except Exception as e:
                logger.warning(f"Echec Nominatim pour {city_name}: {e}")
                sources_tried.append('nominatim_error')
        
        # Source 2: Overpass (plus detaille si Nominatim insuffisant)
        if not districts_data or len(districts_data.get('districts', {})) < 3:
            if self.apis_config['overpass']['enabled']:
                try:
                    overpass_data = self._get_from_overpass(city_name, country)
                    if overpass_data and overpass_data['districts']:
                        # Fusionner avec donnees Nominatim si elles existent
                        if districts_data:
                            districts_data['districts'].update(overpass_data['districts'])
                            districts_data['sources'].extend(overpass_data['sources'])
                        else:
                            districts_data = overpass_data
                        sources_tried.append('overpass_success')
                        logger.info(f"Donnees Overpass ajoutees: {len(overpass_data['districts'])} quartiers")
                    else:
                        sources_tried.append('overpass_empty')
                except Exception as e:
                    logger.warning(f"Echec Overpass pour {city_name}: {e}")
                    sources_tried.append('overpass_error')
        
        # Source 3: Fallback vers coordonnees generiques si echec total
        if not districts_data or not districts_data['districts']:
            logger.warning(f"Aucune donnee API trouvee pour {city_name}, utilisation fallback")
            districts_data = self._generate_fallback_districts(city_name, country)
            sources_tried.append('fallback')
        
        # Enrichir avec metadonnees
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
        
        logger.info(f"Recuperation terminee pour {city_name}: {districts_data['total_districts']} quartiers")
        return districts_data
    
    
    def _get_from_nominatim(self, city_name: str, country: str) -> Dict:
        """
        Recupere les quartiers via l'API Nominatim (OpenStreetMap)
        API gratuite et fiable pour les grandes zones urbaines
        """
        
        base_url = self.apis_config['nominatim']['base_url']
        search_url = f"{base_url}/search"
        
        # Recherche des quartiers/districts dans la ville
        params = {
            'q': f"{city_name}, {country}",
            'format': 'json',
            'addressdetails': 1,
            'limit': 50,
            'extratags': 1,
            'namedetails': 1
        }
        
        # Respect du rate limiting
        time.sleep(self.apis_config['nominatim']['rate_limit'])
        self.stats['api_calls'] += 1
        
        response = requests.get(search_url, params=params, 
                              headers={'User-Agent': 'MalaysiaElectricityDataGenerator/1.0'})
        response.raise_for_status()
        
        data = response.json()
        
        # Extraire les quartiers
        districts = {}
        for item in data:
            district_info = self._extract_district_from_nominatim_item(item)
            if district_info:
                district_name = district_info['name']
                districts[district_name] = district_info
        
        return {
            'districts': districts,
            'sources': ['nominatim'],
            'api_response_count': len(data)
        }
    
    
    def _extract_district_from_nominatim_item(self, item: Dict) -> Optional[Dict]:
        """
        Extrait les informations de quartier depuis un element Nominatim
        """
        
        if 'address' not in item or 'boundingbox' not in item:
            return None
        
        address = item['address']
        
        # Identifier le nom du quartier selon differents niveaux
        district_name = None
        district_type = 'unknown'
        
        # Ordre de preference pour identifier les quartiers
        address_levels = [
            ('suburb', 'residential_district'),
            ('neighbourhood', 'local_area'),
            ('district', 'administrative_district'),
            ('subdistrict', 'sub_administrative'),
            ('quarter', 'city_quarter'),
            ('city_district', 'city_district')
        ]
        
        for addr_key, type_name in address_levels:
            if addr_key in address:
                district_name = address[addr_key]
                district_type = type_name
                break
        
        if not district_name:
            return None
        
        # Extraction des coordonnees de delimitation
        bbox = item['boundingbox']  # [south, north, west, east]
        
        # Classification automatique du type de quartier
        place_type = item.get('type', 'unknown')
        osm_class = item.get('class', 'unknown')
        
        # Determination des types de batiments adaptes
        suitable_buildings = self._determine_suitable_buildings(district_type, place_type, osm_class)
        
        return {
            'name': district_name,
            'coordinates': {
                'lat': (float(bbox[0]), float(bbox[1])),  # south, north
                'lon': (float(bbox[2]), float(bbox[3]))   # west, east
            },
            'type': district_type,
            'osm_type': place_type,
            'osm_class': osm_class,
            'suitable_buildings': suitable_buildings,
            'source': 'nominatim',
            'osm_id': item.get('osm_id', ''),
            'importance': item.get('importance', 0.5)
        }
    
    
    def _get_from_overpass(self, city_name: str, country: str) -> Dict:
        """
        Recupere des donnees detaillees via l'API Overpass (OpenStreetMap)
        Plus lent mais plus detaille que Nominatim
        """
        
        overpass_url = self.apis_config['overpass']['base_url']
        
        # Requete Overpass pour recuperer les relations administratives
        query = f"""
        [out:json][timeout:30];
        (
          area[name="{city_name}"][place~"city|town"];
          rel(area)[admin_level~"^(8|9|10)$"][name];
          rel(area)[place~"suburb|neighbourhood|quarter"];
        );
        out geom;
        """
        
        # Respect du rate limiting
        time.sleep(self.apis_config['overpass']['rate_limit'])
        self.stats['api_calls'] += 1
        
        response = requests.post(overpass_url, data=query, timeout=35)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraire les quartiers depuis les donnees Overpass
        districts = {}
        for element in data.get('elements', []):
            district_info = self._extract_district_from_overpass_element(element)
            if district_info:
                district_name = district_info['name']
                districts[district_name] = district_info
        
        return {
            'districts': districts,
            'sources': ['overpass'],
            'api_response_count': len(data.get('elements', []))
        }
    
    
    def _extract_district_from_overpass_element(self, element: Dict) -> Optional[Dict]:
        """
        Extrait les informations de quartier depuis un element Overpass
        """
        
        if 'tags' not in element or 'name' not in element['tags']:
            return None
        
        tags = element['tags']
        district_name = tags['name']
        
        # Determination du type de quartier
        district_type = 'administrative_area'
        if 'admin_level' in tags:
            level = tags['admin_level']
            if level == '8':
                district_type = 'city_district'
            elif level == '9':
                district_type = 'sub_district'
            elif level == '10':
                district_type = 'neighbourhood'
        
        if 'place' in tags:
            place = tags['place']
            if place == 'suburb':
                district_type = 'residential_district'
            elif place == 'neighbourhood':
                district_type = 'local_area'
            elif place == 'quarter':
                district_type = 'city_quarter'
        
        # Extraction des limites geographiques
        bounds = self._calculate_bounds_from_overpass_geometry(element)
        if not bounds:
            return None
        
        # Determination des types de batiments adaptes
        suitable_buildings = self._determine_suitable_buildings(district_type, 
                                                              tags.get('place', ''),
                                                              tags.get('landuse', ''))
        
        return {
            'name': district_name,
            'coordinates': bounds,
            'type': district_type,
            'suitable_buildings': suitable_buildings,
            'source': 'overpass',
            'admin_level': tags.get('admin_level', ''),
            'place_type': tags.get('place', ''),
            'landuse': tags.get('landuse', ''),
            'osm_id': element.get('id', '')
        }
    
    
    def _calculate_bounds_from_overpass_geometry(self, element: Dict) -> Optional[Dict]:
        """
        Calcule les limites geographiques depuis la geometrie Overpass
        """
        
        if 'bounds' in element:
            # Cas simple : limites directement fournies
            bounds = element['bounds']
            return {
                'lat': (bounds['minlat'], bounds['maxlat']),
                'lon': (bounds['minlon'], bounds['maxlon'])
            }
        
        # Cas complexe : calculer depuis les coordonnees des membres
        if 'members' in element:
            lats, lons = [], []
            
            for member in element['members']:
                if 'geometry' in member:
                    for coord in member['geometry']:
                        lats.append(coord['lat'])
                        lons.append(coord['lon'])
            
            if lats and lons:
                return {
                    'lat': (min(lats), max(lats)),
                    'lon': (min(lons), max(lons))
                }
        
        return None
    
    
    def _determine_suitable_buildings(self, district_type: str, place_type: str, 
                                    landuse: str) -> List[str]:
        """
        Determine les types de batiments adaptes selon le type de quartier
        Base sur des regles urbaines logiques
        """
        
        # Matrice de compatibilite quartier -> batiments
        compatibility_rules = {
            'residential_district': ['Residential', 'School', 'Clinic', 'Retail'],
            'city_district': ['Commercial', 'Office', 'Hotel', 'Restaurant'],
            'administrative_district': ['Office', 'Hospital', 'School'],
            'local_area': ['Residential', 'Retail', 'Restaurant'],
            'neighbourhood': ['Residential', 'School', 'Clinic'],
            'city_quarter': ['Commercial', 'Restaurant', 'Retail'],
            'business_district': ['Office', 'Commercial', 'Hotel'],
            'industrial_zone': ['Factory', 'Industrial', 'Warehouse']
        }
        
        # Regles basees sur l'utilisation des terres (landuse)
        landuse_rules = {
            'residential': ['Residential', 'School', 'Clinic'],
            'commercial': ['Commercial', 'Office', 'Retail', 'Restaurant'],
            'industrial': ['Factory', 'Industrial', 'Warehouse'],
            'retail': ['Retail', 'Commercial', 'Restaurant']
        }
        
        # Combiner les regles
        suitable_buildings = set()
        
        # Appliquer les regles de type de district
        if district_type in compatibility_rules:
            suitable_buildings.update(compatibility_rules[district_type])
        
        # Appliquer les regles d'utilisation des terres
        if landuse in landuse_rules:
            suitable_buildings.update(landuse_rules[landuse])
        
        # Regles par defaut si rien trouve
        if not suitable_buildings:
            suitable_buildings = ['Residential', 'Commercial', 'Retail']
        
        return sorted(list(suitable_buildings))
    
    
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
            'Langkawi': {'lat': (6.3167, 6.3367), 'lon': (99.8167, 99.8367)}
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
    
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """
        Verifie si le fichier cache est encore valide
        """
        if not os.path.exists(cache_file):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        return datetime.now() - file_time < self.cache_duration
    
    
    def _load_from_cache(self, cache_file: str) -> Dict:
        """
        Charge les donnees depuis le cache
        """
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    
    def _save_to_cache(self, cache_file: str, data: Dict):
        """
        Sauvegarde les donnees dans le cache
        """
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    
    def get_statistics(self) -> Dict:
        """
        Retourne les statistiques d'utilisation du systeme
        """
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
        """
        Efface le cache pour une ville specifique ou tout le cache
        """
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
    
    
    def update_all_cached_cities(self, cities: List[str]):
        """
        Met a jour le cache pour une liste de villes
        Utile pour un refresh programme
        """
        logger.info(f"Mise a jour du cache pour {len(cities)} villes")
        
        for city in cities:
            try:
                logger.info(f"Mise a jour cache pour {city}...")
                self.get_city_districts(city, force_refresh=True)
                logger.info(f"Cache mis a jour pour {city}")
                
                # Pause entre les villes pour respecter les rate limits
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Echec mise a jour cache pour {city}: {e}")
        
        logger.info("Mise a jour du cache terminee")


# Classe d'integration avec le systeme existant
class EnhancedCoordinatesGenerator:
    """
    Generateur de coordonnees ameliore integrant le systeme automatise
    Compatible avec le systeme existant
    """
    
    def __init__(self, cache_dir="districts_cache"):
        """
        Initialise le generateur avec le gestionnaire automatise
        """
        self.districts_manager = AutomatedDistrictsManager(cache_dir=cache_dir)
        self.city_districts_cache = {}  # Cache en memoire pour les performances
        
        logger.info("EnhancedCoordinatesGenerator initialise")
    
    
    def generate_coordinates(self, city_name: str, building_type: str = None) -> Tuple[float, float]:
        """
        Genere des coordonnees avec placement intelligent par quartier
        
        Args:
            city_name (str): Nom de la ville
            building_type (str): Type de batiment (optionnel)
            
        Returns:
            tuple: (latitude, longitude)
        """
        
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
        
        logger.debug(f"Coordonnees generees pour {building_type or 'batiment'} a {city_name}: "
                    f"{latitude}, {longitude} dans {suitable_district['name']}")
        
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
    
    
    def _find_best_district_for_building(self, districts: Dict, building_type: str) -> Dict:
        """
        Trouve le quartier le plus adapte pour un type de batiment
        """
        
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
        """
        Calcule un score de pertinence entre un quartier et un type de batiment
        """
        
        suitable_buildings = district_info.get('suitable_buildings', [])
        
        # Score de base si le batiment est explicitement adapte
        if building_type in suitable_buildings:
            base_score = 10
        else:
            base_score = 3  # Score neutre