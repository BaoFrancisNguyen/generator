"""
Route backend pour la génération basée sur OpenStreetMap
Fichier: osm_generation_route.py

À intégrer dans votre app.py existant
"""

import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from flask import request, jsonify
import random

# Configuration du logging
logger = logging.getLogger(__name__)

def add_osm_routes(app, generator):
    """
    Ajoute les routes OSM à l'application Flask existante
    
    Args:
        app: Instance Flask
        generator: Instance ElectricityDataGenerator existante
    """
    
    @app.route('/generate-from-osm', methods=['POST'])
    def generate_from_osm():
        """
        Route principale pour générer des données à partir d'OpenStreetMap
        """
        try:
            logger.info("🗺️ Début génération basée sur OSM")
            
            # Récupération des données de la requête
            data = request.get_json()
            
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
            
            # Générer les séries temporelles avec vos règles existantes
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
                'message': f'Données générées avec succès depuis OSM pour {zone_data.get("name", "zone sélectionnée")}',
                'stats': stats,
                'osm_quality': osm_quality,
                'sample_data': sample_data,
                'buildings_analysis': analyze_building_distribution(buildings_df),
                'consumption_patterns': analyze_consumption_patterns(timeseries_df),
                'generation_info': {
                    'zone_type': zone_data.get('type', 'unknown'),
                    'zone_name': zone_data.get('name', 'Unknown'),
                    'osm_buildings_count': len(buildings_osm),
                    'processed_buildings': len(buildings_df),
                    'time_range': f"{start_date} to {end_date}",
                    'frequency': freq,
                    'generation_timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info("✅ Génération OSM terminée avec succès")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur génération OSM: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la génération basée sur OSM'
            }), 500

    @app.route('/validate-osm-zone', methods=['POST'])
    def validate_osm_zone():
        """
        Validation et estimation pour une zone OSM
        """
        try:
            data = request.get_json()
            zone_data = data.get('zone_data', {})
            
            # Estimation du nombre de bâtiments
            estimated_buildings = estimate_buildings_in_zone(zone_data)
            
            # Estimation du temps de requête OSM
            query_time_estimate = estimate_osm_query_time(zone_data)
            
            # Validation de la zone
            zone_validation = validate_zone_parameters(zone_data)
            
            return jsonify({
                'success': True,
                'estimated_buildings': estimated_buildings,
                'query_time_estimate': query_time_estimate,
                'validation': zone_validation,
                'recommendations': generate_zone_recommendations(zone_data)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur validation zone OSM: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/preview-osm-data', methods=['POST'])
    def preview_osm_data():
        """
        Aperçu des données OSM sans génération complète
        """
        try:
            data = request.get_json()
            buildings_osm = data.get('buildings_osm', [])
            
            if not buildings_osm:
                return jsonify({
                    'success': False,
                    'error': 'Aucun bâtiment OSM fourni'
                })
            
            # Analyse rapide des bâtiments
            building_analysis = quick_analyze_osm_buildings(buildings_osm)
            
            # Échantillon de bâtiments convertis
            sample_buildings = convert_osm_sample(buildings_osm[:10])
            
            return jsonify({
                'success': True,
                'building_analysis': building_analysis,
                'sample_buildings': sample_buildings,
                'total_buildings': len(buildings_osm)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur aperçu OSM: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


def convert_osm_to_buildings_df(buildings_osm, zone_data):
    """
    Convertit les bâtiments OSM en DataFrame compatible avec votre système existant
    """
    buildings_list = []
    
    zone_name = zone_data.get('name', 'Unknown Zone')
    zone_center = zone_data.get('center', [3.1390, 101.6869])  # Défaut KL
    
    for i, building in enumerate(buildings_osm):
        if not building.get('geometry') or len(building['geometry']) < 3:
            continue
            
        try:
            # Calculer le centre du bâtiment
            coords = building['geometry']
            center_lat = sum(point['lat'] for point in coords) / len(coords)
            center_lon = sum(point['lon'] for point in coords) / len(coords)
            
            # Déterminer le type de bâtiment selon vos catégories existantes
            building_class = map_osm_to_building_class(building.get('tags', {}))
            
            # Générer un ID unique
            unique_id = f"OSM_{building.get('id', i)}_{random.randint(10000, 99999)}"
            
            # Créer l'entrée de bâtiment compatible avec votre système
            building_data = {
                'unique_id': unique_id,
                'dataset': 'malaysia_electricity_osm',
                'building_id': f"OSM_{zone_name.replace(' ', '_')}_{i:06d}",
                'location_id': f"OSM_{hash(zone_name) % 100000:05d}",
                'latitude': center_lat,
                'longitude': center_lon,
                'location': zone_name,
                'state': determine_state_from_coords(center_lat, center_lon),
                'region': determine_region_from_coords(center_lat, center_lon),
                'population': zone_data.get('population', estimate_population_from_zone(zone_data)),
                'timezone': 'Asia/Kuala_Lumpur',
                'building_class': building_class,
                'cluster_size': random.randint(1, 20),  # Basé sur la densité locale
                'freq': '30T',
                
                # Métadonnées OSM additionnelles
                'osm_id': building.get('id'),
                'osm_type': building.get('type', 'way'),
                'osm_tags': json.dumps(building.get('tags', {})),
                'osm_building_type': building.get('tags', {}).get('building', 'yes'),
                'osm_name': building.get('tags', {}).get('name'),
                'osm_height': building.get('tags', {}).get('height'),
                'osm_levels': building.get('tags', {}).get('building:levels'),
                'osm_area': calculate_building_area(coords)
            }
            
            buildings_list.append(building_data)
            
        except Exception as e:
            logger.warning(f"Erreur traitement bâtiment OSM {building.get('id', i)}: {e}")
            continue
    
    logger.info(f"✅ Conversion OSM: {len(buildings_list)} bâtiments traités")
    return pd.DataFrame(buildings_list)


def map_osm_to_building_class(tags):
    """
    Mappe les tags OSM vers vos classes de bâtiments existantes
    """
    if not tags or 'building' not in tags:
        return 'Residential'  # Défaut
    
    osm_building = tags['building'].lower()
    
    # Mapping direct vers vos classes existantes
    mapping = {
        # Résidentiel
        'residential': 'Residential',
        'house': 'Residential', 
        'detached': 'Residential',
        'apartments': 'Apartment',
        'apartment': 'Apartment',
        'terrace': 'Residential',
        'semidetached_house': 'Residential',
        'bungalow': 'Residential',
        
        # Commercial
        'commercial': 'Commercial',
        'retail': 'Retail',
        'shop': 'Retail',
        'supermarket': 'Retail',
        'mall': 'Commercial',
        'office': 'Office',
        
        # Industriel
        'industrial': 'Industrial',
        'warehouse': 'Warehouse',
        'factory': 'Factory',
        'manufacture': 'Factory',
        
        # Services publics
        'hospital': 'Hospital',
        'clinic': 'Clinic',
        'school': 'School',
        'university': 'School',
        'college': 'School',
        'kindergarten': 'School',
        
        # Hôtellerie
        'hotel': 'Hotel',
        'motel': 'Hotel',
        'guest_house': 'Hotel',
        'hostel': 'Hotel',
        
        # Restauration
        'restaurant': 'Restaurant',
        'cafe': 'Restaurant',
        'fast_food': 'Restaurant',
        
        # Autres
        'church': 'Commercial',  # Pas de catégorie religieuse spécifique
        'mosque': 'Commercial',
        'temple': 'Commercial',
        'civic': 'Office',
        'government': 'Office',
        'public': 'Office'
    }
    
    # Vérifier les tags spéciaux
    if 'amenity' in tags:
        amenity = tags['amenity'].lower()
        amenity_mapping = {
            'hospital': 'Hospital',
            'clinic': 'Clinic', 
            'school': 'School',
            'university': 'School',
            'restaurant': 'Restaurant',
            'cafe': 'Restaurant',
            'hotel': 'Hotel'
        }
        if amenity in amenity_mapping:
            return amenity_mapping[amenity]
    
    return mapping.get(osm_building, 'Residential')


def determine_state_from_coords(lat, lon):
    """
    Détermine l'état malaisien à partir des coordonnées
    """
    # Mapping approximatif des coordonnées vers les états
    if 3.0 <= lat <= 3.3 and 101.5 <= lon <= 101.8:
        return 'Federal Territory'  # Kuala Lumpur
    elif 5.2 <= lat <= 5.6 and 100.1 <= lon <= 100.5:
        return 'Penang'  # George Town
    elif 2.8 <= lat <= 3.8 and 101.0 <= lon <= 102.0:
        return 'Selangor'
    elif 1.3 <= lat <= 2.0 and 103.0 <= lon <= 104.0:
        return 'Johor'
    elif 4.0 <= lat <= 5.0 and 100.5 <= lon <= 102.0:
        return 'Perak'
    elif 5.5 <= lat <= 6.5 and 115.5 <= lon <= 117.5:
        return 'Sabah'
    elif 0.5 <= lat <= 3.0 and 109.0 <= lon <= 115.0:
        return 'Sarawak'
    else:
        return 'Unknown'


def determine_region_from_coords(lat, lon):
    """
    Détermine la région malaisienne à partir des coordonnées
    """
    state = determine_state_from_coords(lat, lon)
    
    region_mapping = {
        'Federal Territory': 'Central',
        'Selangor': 'Central',
        'Negeri Sembilan': 'Central',
        'Penang': 'Northern',
        'Kedah': 'Northern',
        'Perlis': 'Northern',
        'Perak': 'Northern',
        'Johor': 'Southern',
        'Malacca': 'Southern',
        'Pahang': 'East Coast',
        'Terengganu': 'East Coast',
        'Kelantan': 'East Coast',
        'Sabah': 'East Malaysia',
        'Sarawak': 'East Malaysia'
    }
    
    return region_mapping.get(state, 'Unknown')


def calculate_building_area(coords):
    """
    Calcule approximativement l'aire d'un bâtiment
    """
    if len(coords) < 3:
        return 0
    
    # Formule de Shoelace simplifiée
    area = 0
    n = len(coords)
    
    for i in range(n):
        j = (i + 1) % n
        area += coords[i]['lat'] * coords[j]['lon']
        area -= coords[j]['lat'] * coords[i]['lon']
    
    area = abs(area) / 2
    
    # Conversion approximative en m² (très approximative)
    # 1 degré ≈ 111 km à l'équateur
    area_m2 = area * (111000 ** 2)
    
    return round(area_m2, 2)


def estimate_population_from_zone(zone_data):
    """
    Estime la population d'une zone
    """
    zone_type = zone_data.get('type', 'city')
    
    if zone_type == 'country':
        return 32000000  # Population Malaisie
    elif zone_type == 'city':
        return zone_data.get('population', 500000)
    elif zone_type == 'custom':
        radius = zone_data.get('radius', 1000)
        # Estimation: ~1000 hab/km² en zone urbaine
        area_km2 = (radius / 1000) ** 2 * 3.14159
        return int(area_km2 * 1000)
    else:
        return 100000


def calculate_osm_stats(buildings_df, timeseries_df, zone_data):
    """
    Calcule les statistiques complètes pour les données OSM
    """
    stats = {
        'buildings_count': len(buildings_df),
        'total_records': len(timeseries_df),
        'unique_locations': buildings_df['location'].nunique(),
        'zone_info': {
            'name': zone_data.get('name', 'Unknown'),
            'type': zone_data.get('type', 'unknown'),
            'population': zone_data.get('population', 0)
        },
        'building_distribution': buildings_df['building_class'].value_counts().to_dict(),
        'consumption_stats': {
            'mean': float(timeseries_df['y'].mean()),
            'max': float(timeseries_df['y'].max()),
            'min': float(timeseries_df['y'].min()),
            'std': float(timeseries_df['y'].std())
        },
        'date_range': {
            'start': timeseries_df['ds'].min().isoformat(),
            'end': timeseries_df['ds'].max().isoformat()
        },
        'data_sources': [
            'OpenStreetMap via Overpass API',
            'Règles de consommation électrique tropicales Malaysia',
            'Patterns climatiques régionaux'
        ]
    }
    
    return stats


def analyze_osm_data_quality(buildings_osm):
    """
    Analyse la qualité des données OSM récupérées
    """
    total_buildings = len(buildings_osm)
    
    if total_buildings == 0:
        return {
            'quality_score': 0,
            'completeness': 0,
            'issues': ['Aucun bâtiment trouvé'],
            'recommendations': ['Élargir la zone de recherche']
        }
    
    # Analyse de la complétude
    buildings_with_names = sum(1 for b in buildings_osm if b.get('tags', {}).get('name'))
    buildings_with_height = sum(1 for b in buildings_osm if b.get('tags', {}).get('height'))
    buildings_with_levels = sum(1 for b in buildings_osm if b.get('tags', {}).get('building:levels'))
    buildings_with_address = sum(1 for b in buildings_osm if b.get('tags', {}).get('addr:street'))
    
    completeness_score = (
        (buildings_with_names / total_buildings * 25) +
        (buildings_with_height / total_buildings * 25) +
        (buildings_with_levels / total_buildings * 25) +
        (buildings_with_address / total_buildings * 25)
    )
    
    # Score de qualité global
    quality_score = min(100, completeness_score + 30)  # Base de 30 pour avoir des géométries
    
    # Identification des problèmes
    issues = []
    recommendations = []
    
    if buildings_with_names / total_buildings < 0.3:
        issues.append('Peu de bâtiments nommés')
        recommendations.append('Données OSM partielles - noms manquants')
    
    if buildings_with_height / total_buildings < 0.1:
        issues.append('Informations de hauteur manquantes')
        recommendations.append('Hauteurs estimées selon le type de bâtiment')
    
    return {
        'quality_score': round(quality_score, 1),
        'completeness': round(completeness_score, 1),
        'total_buildings': total_buildings,
        'metadata_stats': {
            'with_names': buildings_with_names,
            'with_height': buildings_with_height,
            'with_levels': buildings_with_levels,
            'with_address': buildings_with_address
        },
        'issues': issues,
        'recommendations': recommendations,
        'freshness': 'Données OSM en temps réel'
    }


def prepare_sample_data(buildings_df, timeseries_df):
    """
    Prépare un échantillon des données pour l'aperçu
    """
    # Échantillon de bâtiments
    sample_buildings = buildings_df.head(5).to_dict('records')
    
    # Échantillon de séries temporelles
    sample_timeseries = timeseries_df.head(10).to_dict('records')
    
    # Convertir les timestamps en strings pour JSON
    for record in sample_timeseries:
        if 'ds' in record:
            record['ds'] = record['ds'].isoformat()
    
    return {
        'buildings_sample': sample_buildings,
        'timeseries_sample': sample_timeseries,
        'sample_size': {
            'buildings': len(sample_buildings),
            'timeseries': len(sample_timeseries)
        }
    }


def analyze_building_distribution(buildings_df):
    """
    Analyse la distribution des types de bâtiments
    """
    distribution = buildings_df['building_class'].value_counts()
    total = len(buildings_df)
    
    analysis = {
        'total_buildings': total,
        'types_count': len(distribution),
        'distribution': {},
        'dominant_type': distribution.index[0] if len(distribution) > 0 else 'Unknown',
        'diversity_score': 0
    }
    
    for building_type, count in distribution.items():
        percentage = (count / total) * 100
        analysis['distribution'][building_type] = {
            'count': int(count),
            'percentage': round(percentage, 1)
        }
    
    # Score de diversité (entropy simplifiée)
    if len(distribution) > 1:
        entropy = sum(-(count/total) * np.log2(count/total) for count in distribution.values())
        max_entropy = np.log2(len(distribution))
        analysis['diversity_score'] = round((entropy / max_entropy) * 100, 1)
    
    return analysis


def analyze_consumption_patterns(timeseries_df):
    """
    Analyse les patterns de consommation générés
    """
    if len(timeseries_df) == 0:
        return {'error': 'Aucune donnée de consommation'}
    
    # Analyse par heure si possible
    timeseries_df['hour'] = pd.to_datetime(timeseries_df['ds']).dt.hour
    hourly_avg = timeseries_df.groupby('hour')['y'].mean()
    
    # Détection des pics
    peak_hours = hourly_avg.nlargest(3).index.tolist()
    low_hours = hourly_avg.nsmallest(3).index.tolist()
    
    return {
        'overall_stats': {
            'mean_consumption': round(timeseries_df['y'].mean(), 2),
            'max_consumption': round(timeseries_df['y'].max(), 2),
            'min_consumption': round(timeseries_df['y'].min(), 2),
            'std_consumption': round(timeseries_df['y'].std(), 2)
        },
        'temporal_patterns': {
            'peak_hours': peak_hours,
            'low_consumption_hours': low_hours,
            'hourly_average': hourly_avg.round(2).to_dict()
        },
        'data_quality': {
            'zero_consumption_rate': round((timeseries_df['y'] == 0).sum() / len(timeseries_df) * 100, 2),
            'outliers_rate': round((timeseries_df['y'] > timeseries_df['y'].quantile(0.99)).sum() / len(timeseries_df) * 100, 2)
        }
    }


def quick_analyze_osm_buildings(buildings_osm):
    """
    Analyse rapide des bâtiments OSM pour l'aperçu
    """
    if not buildings_osm:
        return {'error': 'Aucun bâtiment fourni'}
    
    building_types = {}
    total_area = 0
    buildings_with_metadata = 0
    
    for building in buildings_osm:
        tags = building.get('tags', {})
        building_type = tags.get('building', 'unknown')
        
        building_types[building_type] = building_types.get(building_type, 0) + 1
        
        if building.get('geometry'):
            area = calculate_building_area(building['geometry'])
            total_area += area
        
        if tags.get('name') or tags.get('height') or tags.get('building:levels'):
            buildings_with_metadata += 1
    
    return {
        'total_buildings': len(buildings_osm),
        'building_types': building_types,
        'estimated_total_area': round(total_area, 2),
        'metadata_completeness': round((buildings_with_metadata / len(buildings_osm)) * 100, 1),
        'most_common_type': max(building_types.items(), key=lambda x: x[1])[0] if building_types else 'unknown'
    }


def convert_osm_sample(buildings_osm):
    """
    Convertit un échantillon de bâtiments OSM pour l'aperçu
    """
    sample = []
    
    for i, building in enumerate(buildings_osm[:5]):  # Limiter à 5 pour l'aperçu
        tags = building.get('tags', {})
        geometry = building.get('geometry', [])
        
        # Calculer le centre si possible
        center_lat = center_lon = None
        if geometry and len(geometry) > 0:
            center_lat = sum(point['lat'] for point in geometry) / len(geometry)
            center_lon = sum(point['lon'] for point in geometry) / len(geometry)
        
        sample.append({
            'osm_id': building.get('id'),
            'building_type_osm': tags.get('building', 'unknown'),
            'building_class_mapped': map_osm_to_building_class(tags),
            'name': tags.get('name'),
            'height': tags.get('height'),
            'levels': tags.get('building:levels'),
            'center_coordinates': [center_lat, center_lon] if center_lat else None,
            'area_estimated': calculate_building_area(geometry) if geometry else 0
        })
    
    return sample


# Fonctions utilitaires additionnelles
def estimate_buildings_in_zone(zone_data):
    """
    Estime le nombre de bâtiments dans une zone
    """
    zone_type = zone_data.get('type', 'city')
    
    if zone_type == 'country':
        return 4800000  # Estimation Malaisie entière
    elif zone_type == 'city':
        population = zone_data.get('population', 500000)
        return int(population * 0.15)  # 15% ratio bâtiments/habitants
    elif zone_type == 'custom':
        radius = zone_data.get('radius', 1000)
        area_km2 = (radius / 1000) ** 2 * 3.14159
        return int(area_km2 * 100)  # ~100 bâtiments/km² en zone urbaine
    else:
        return 1000


def estimate_osm_query_time(zone_data):
    """
    Estime le temps de requête OSM
    """
    estimated_buildings = estimate_buildings_in_zone(zone_data)
    
    if estimated_buildings < 500:
        return "< 10 secondes"
    elif estimated_buildings < 2000:
        return "10-30 secondes"
    elif estimated_buildings < 10000:
        return "30-90 secondes"
    else:
        return "1-5 minutes"


def validate_zone_parameters(zone_data):
    """
    Valide les paramètres de zone
    """
    validation = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    zone_type = zone_data.get('type')
    
    if zone_type == 'custom':
        center = zone_data.get('center', [])
        radius = zone_data.get('radius', 0)
        
        if len(center) != 2:
            validation['errors'].append('Coordonnées de centre invalides')
            validation['valid'] = False
        
        if radius < 100 or radius > 20000:
            validation['warnings'].append('Rayon recommandé: 100m - 20km')
    
    elif zone_type == 'country':
        validation['warnings'].append('Zone très large - temps de traitement élevé')
    
    return validation


def generate_zone_recommendations(zone_data):
    """
    Génère des recommandations pour la zone
    """
    zone_type = zone_data.get('type', 'city')
    estimated_buildings = estimate_buildings_in_zone(zone_data)
    
    recommendations = []
    
    if estimated_buildings > 10000:
        recommendations.append('Zone large détectée - considérer une subdivision')
        recommendations.append('Temps de traitement estimé > 5 minutes')
    
    if zone_type == 'custom':
        recommendations.append('Vérifier que la zone couvre une zone urbaine')
        recommendations.append('Ajuster le rayon selon la densité locale')
    
    if zone_type == 'city':
        recommendations.append('Données de haute qualité attendues')
        recommendations.append('Bonne couverture OSM dans les villes malaysiennes')
    
    return recommendations


# Import numpy pour les calculs statistiques
try:
    import numpy as np
except ImportError:
    # Fallback si numpy n'est pas disponible
    class np:
        @staticmethod
        def log2(x):
            import math
            return math.log2(x)