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

# Import sécurisé du distributeur de bâtiments avec vraies données
try:
    from real_data_integrator import RealDataIntegrator
    REAL_DATA_AVAILABLE = True
    logger.info("✅ RealDataIntegrator chargé - Vraies données disponibles")
except ImportError as e:
    logger.warning(f"⚠️ RealDataIntegrator non disponible: {e}")
    REAL_DATA_AVAILABLE = False

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
    """Générateur de données électriques réalistes pour la Malaisie avec VRAIES DONNÉES"""
    
    def __init__(self):
        # Instance du distributeur de bâtiments avec vraies données
        self.real_data_available = REAL_DATA_AVAILABLE
        
        if self.real_data_available:
            self.real_data_integrator = RealDataIntegrator()
            logger.info("🎯 Intégrateur de vraies données activé")
        else:
            self.real_data_integrator = None
            logger.warning("⚠️ Vraies données non disponibles - utilisation estimations")
        
        if BUILDING_DISTRIBUTOR_AVAILABLE:
            self.building_distributor = BuildingDistributor()
            logger.info("🏗️ BuildingDistributor chargé")
        else:
            self.building_distributor = MockBuildingDistributor()
            logger.warning("🏗️ MockBuildingDistributor utilisé (distribution basique)")
        
        # Instance du validateur (si disponible)
        self.validation_enabled = VALIDATION_ENABLED
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
        
        # Types de bâtiments supportés (étendus avec vraies données)
        self.building_classes = [
            'Residential', 'Commercial', 'Industrial', 'Office', 
            'Retail', 'Hospital', 'Clinic', 'School', 'Hotel', 'Restaurant',
            'Warehouse', 'Factory', 'Apartment'
        ]
        
        # ... (rest of existing code remains the same)

# [Le reste de votre code existant pour la classe ElectricityDataGenerator]
# [Méthodes generate_coordinates, calculate_realistic_consumption, etc.]

# Instance globale du générateur
try:
    generator = ElectricityDataGenerator()
    logger.info("✅ Générateur initialisé avec succès")
except Exception as e:
    logger.error(f"❌ Erreur initialisation générateur: {e}")
    raise


# Routes Flask mises à jour
@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Génère et affiche les données avec VRAIES DONNÉES si disponibles"""
    
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
        
        # NOUVEAU: Utiliser la méthode avec vraies données
        if hasattr(generator, 'generate_building_metadata_with_real_data'):
            buildings_df = generator.generate_building_metadata_with_real_data(
                num_buildings, location_filter, custom_location
            )
        else:
            # Fallback à l'ancienne méthode
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
        
        # Préparer la réponse avec indicateur de vraies données
        response_data = {
            'success': True,
            'buildings': buildings_df.to_dict('records'),
            'timeseries': timeseries_df.head(500).to_dict('records'),
            'stats': stats,
            'building_type_distribution': building_type_stats,
            'location_analysis': location_analysis,
            'real_data_used': generator.real_data_available,  # NOUVEAU
            'data_source': 'Official Malaysia Data' if generator.real_data_available else 'Estimated Data'  # NOUVEAU
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
        
        # NOUVEAU: Ajouter rapport de comparaison si vraies données disponibles
        if generator.real_data_available and len(location_analysis) > 0:
            main_city = location_analysis[0]['location']
            try:
                comparison_report = generator.real_data_integrator.generate_comparison_report(
                    building_type_stats, main_city
                )
                response_data['real_data_comparison'] = comparison_report
            except Exception as e:
                logger.warning(f"Erreur génération rapport comparaison: {e}")
        
        logger.info(f"🎉 Génération réussie - {len(buildings_df)} bâtiments, {len(timeseries_df)} observations")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur génération: {e}")
        return jsonify({'success': False, 'error': str(e)})

# [Autres routes existantes: /download, /sample, etc.]

@app.route('/api/real-data-status')
def get_real_data_status():
    """API pour vérifier le statut des vraies données"""
    
    status = {
        'real_data_available': generator.real_data_available,
        'cities_with_official_data': [],
        'total_official_buildings': 0,
        'data_sources': []
    }
    
    if generator.real_data_available:
        try:
            real_data = generator.real_data_integrator.real_building_data
            cities = real_data.get('cities', {})
            
            for city_name, city_data in cities.items():
                status['cities_with_official_data'].append({
                    'name': city_name,
                    'total_buildings': city_data.get('total_buildings', 0),
                    'source': city_data.get('source', 'Unknown'),
                    'last_updated': city_data.get('last_updated', 'Unknown')
                })
                status['total_official_buildings'] += city_data.get('total_buildings', 0)
            
            # Extraire les sources uniques
            sources = set()
            for city_data in cities.values():
                if 'source' in city_data:
                    sources.add(city_data['source'])
            status['data_sources'] = list(sources)
            
        except Exception as e:
            logger.error(f"Erreur récupération statut vraies données: {e}")
    
    return jsonify({
        'success': True,
        'status': status
    })

@app.route('/api/city-comparison/<city_name>')
def get_city_comparison(city_name):
    """API pour obtenir une comparaison détaillée d'une ville"""
    
    if not generator.real_data_available:
        return jsonify({
            'success': False,
            'error': 'Vraies données non disponibles'
        })
    
    try:
        # Générer une distribution exemple
        example_distribution = {
            'Residential': 100,
            'Commercial': 20,
            'Industrial': 10,
            'Hospital': 2,
            'School': 8
        }
        
        comparison_report = generator.real_data_integrator.generate_comparison_report(
            example_distribution, city_name
        )
        
        return jsonify({
            'success': True,
            'city': city_name,
            'comparison_report': comparison_report
        })
        
    except Exception as e:
        logger.error(f"Erreur comparaison ville: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update-real-data', methods=['POST'])
def update_real_data():
    """API pour mettre à jour les vraies données"""
    
    try:
        if generator.real_data_available:
            # Recharger les données
            generator.real_data_integrator = RealDataIntegrator()
            
            return jsonify({
                'success': True,
                'message': 'Vraies données rechargées avec succès',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'RealDataIntegrator non disponible'
            })
            
    except Exception as e:
        logger.error(f"Erreur mise à jour vraies données: {e}")
        return jsonify({'success': False, 'error': str(e)})

# [Routes API existantes: /api/stats, /api/validation-history, etc.]


if __name__ == '__main__':
    print("🇲🇾 Démarrage du générateur de données électriques pour la MALAISIE...")
    print(f"🏙️ {len(generator.malaysia_locations)} villes disponibles")
    print("📊 Distribution réaliste des bâtiments selon les caractéristiques urbaines")
    print("🌴 Patterns climatiques tropicaux intégrés")
    
    if generator.real_data_available:
        print("🎯 VRAIES DONNÉES OFFICIELLES ACTIVÉES!")
        print("   - Nombres exacts basés sur sources gouvernementales")
        print("   - Hôpitaux selon Ministry of Health Malaysia")
        print("   - Écoles selon Ministry of Education Malaysia")
        print("   - Validation contre données officielles")
        print("   - APIs: /api/real-data-status, /api/city-comparison")
    else:
        print("📊 Mode estimation (pour activer vraies données: installer real_data_integrator.py)")
    
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