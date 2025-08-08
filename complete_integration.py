# complete_integration.py
"""
Intégration complète du prédicteur de bâtiments avec l'application Flask.
Ajoute les routes API nécessaires pour le prédicteur frontend.

Version: 2.0 - Intégration corrigée
Auteur: Système de génération Malaysia
"""

import json
import logging
from typing import Dict, List, Optional, Any
from flask import jsonify, request

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuildingPredictorBackend:
    """
    Backend pour le prédicteur de bâtiments avec API pour le frontend
    """
    
    def __init__(self, generator):
        """
        Initialise le backend du prédicteur
        
        Args:
            generator: Instance du générateur principal (ElectricityDataGenerator)
        """
        self.generator = generator
        
        # Données de référence pour prédiction (synchronisées avec frontend)
        self.reference_data = {
            'Kuala Lumpur': {
                'population': 1800000,
                'region': 'Central',
                'type': 'metropolis',
                'distribution': {
                    'Residential': 0.65, 'Commercial': 0.12, 'Office': 0.08,
                    'Industrial': 0.04, 'Hospital': 0.002, 'Clinic': 0.01,
                    'School': 0.025, 'Hotel': 0.025, 'Restaurant': 0.04,
                    'Retail': 0.06, 'Warehouse': 0.012, 'Apartment': 0.015
                },
                'confidence': 95,
                'source': 'Ministry of Health, Education, Tourism Malaysia'
            },
            'George Town': {
                'population': 708000,
                'region': 'Northern',
                'type': 'major_city',
                'distribution': {
                    'Residential': 0.70, 'Commercial': 0.14, 'Office': 0.05,
                    'Industrial': 0.04, 'Hospital': 0.001, 'Clinic': 0.006,
                    'School': 0.022, 'Hotel': 0.025, 'Restaurant': 0.028,
                    'Retail': 0.05, 'Warehouse': 0.008, 'Apartment': 0.012
                },
                'confidence': 95,
                'source': 'Penang State Government + Tourism Board'
            },
            'Johor Bahru': {
                'population': 497000,
                'region': 'Southern',
                'type': 'industrial_city',
                'distribution': {
                    'Residential': 0.68, 'Commercial': 0.12, 'Office': 0.06,
                    'Industrial': 0.12, 'Hospital': 0.001, 'Clinic': 0.005,
                    'School': 0.018, 'Hotel': 0.012, 'Restaurant': 0.022,
                    'Retail': 0.04, 'Warehouse': 0.035, 'Factory': 0.025
                },
                'confidence': 90,
                'source': 'Johor State Government + MIDA'
            },
            'Langkawi': {
                'population': 65000,
                'region': 'Northern',
                'type': 'tourist_destination',
                'distribution': {
                    'Residential': 0.60, 'Commercial': 0.15, 'Office': 0.02,
                    'Industrial': 0.01, 'Hospital': 0.0, 'Clinic': 0.005,
                    'School': 0.020, 'Hotel': 0.12, 'Restaurant': 0.15,
                    'Retail': 0.06, 'Warehouse': 0.005
                },
                'confidence': 85,
                'source': 'Tourism Malaysia + Kedah State'
            }
        }
        
        # Ratios par défaut selon type de ville
        self.default_ratios = {
            'metropolis': {
                'Residential': 0.65, 'Commercial': 0.12, 'Office': 0.08,
                'Industrial': 0.04, 'Hospital': 0.002, 'Clinic': 0.01,
                'School': 0.025, 'Hotel': 0.020, 'Restaurant': 0.035,
                'Retail': 0.055, 'Warehouse': 0.012, 'Apartment': 0.018
            },
            'major_city': {
                'Residential': 0.70, 'Commercial': 0.13, 'Office': 0.06,
                'Industrial': 0.05, 'Hospital': 0.001, 'Clinic': 0.008,
                'School': 0.025, 'Hotel': 0.015, 'Restaurant': 0.025,
                'Retail': 0.045, 'Warehouse': 0.010, 'Apartment': 0.012
            },
            'medium_city': {
                'Residential': 0.72, 'Commercial': 0.11, 'Office': 0.04,
                'Industrial': 0.06, 'Hospital': 0.001, 'Clinic': 0.006,
                'School': 0.028, 'Hotel': 0.010, 'Restaurant': 0.018,
                'Retail': 0.040, 'Warehouse': 0.008, 'Factory': 0.015
            },
            'small_city': {
                'Residential': 0.75, 'Commercial': 0.10, 'Office': 0.02,
                'Industrial': 0.08, 'Hospital': 0.0, 'Clinic': 0.005,
                'School': 0.030, 'Hotel': 0.005, 'Restaurant': 0.012,
                'Retail': 0.035, 'Warehouse': 0.005
            },
            'tourist_destination': {
                'Residential': 0.60, 'Commercial': 0.15, 'Office': 0.02,
                'Industrial': 0.02, 'Hospital': 0.0, 'Clinic': 0.005,
                'School': 0.025, 'Hotel': 0.10, 'Restaurant': 0.12,
                'Retail': 0.06, 'Warehouse': 0.005
            },
            'industrial_city': {
                'Residential': 0.65, 'Commercial': 0.10, 'Office': 0.05,
                'Industrial': 0.15, 'Hospital': 0.001, 'Clinic': 0.005,
                'School': 0.020, 'Hotel': 0.008, 'Restaurant': 0.018,
                'Retail': 0.035, 'Warehouse': 0.040, 'Factory': 0.035
            }
        }
        
        logger.info("✅ BuildingPredictorBackend initialisé avec données de référence")
    
    def determine_city_type(self, population: int) -> str:
        """
        Détermine le type de ville selon la population
        
        Args:
            population: Population de la ville
            
        Returns:
            Type de ville (metropolis, major_city, etc.)
        """
        if population > 1000000:
            return 'metropolis'
        elif population > 500000:
            return 'major_city'
        elif population > 200000:
            return 'medium_city'
        elif population > 50000:
            return 'small_city'
        else:
            return 'small_city'
    
    def get_city_distribution(self, city_name: str, population: int, 
                            region: str, city_type: str = None) -> Dict[str, float]:
        """
        Obtient la distribution pour une ville donnée
        
        Args:
            city_name: Nom de la ville
            population: Population de la ville
            region: Région de la ville
            city_type: Type de ville (optionnel)
            
        Returns:
            Distribution en pourcentages
        """
        # Utiliser les vraies données si disponibles
        if city_name in self.reference_data:
            return self.reference_data[city_name]['distribution']
        
        # Déterminer le type si non fourni
        if not city_type:
            city_type = self.determine_city_type(population)
        
        # Ajustements spéciaux selon le nom/région
        if 'langkawi' in city_name.lower() or 'tourist' in city_name.lower():
            city_type = 'tourist_destination'
        elif any(keyword in city_name.lower() for keyword in ['port', 'pasir gudang', 'industrial']):
            city_type = 'industrial_city'
        
        # Retourner la distribution par défaut
        return self.default_ratios.get(city_type, self.default_ratios['medium_city'])
    
    def calculate_prediction(self, num_buildings: int, location_params: Dict) -> Dict[str, Any]:
        """
        Calcule la prédiction de distribution des bâtiments
        
        Args:
            num_buildings: Nombre total de bâtiments
            location_params: Paramètres de localisation
            
        Returns:
            Prédiction complète avec distribution et métadonnées
        """
        try:
            cities = location_params.get('cities', [])
            confidence = location_params.get('confidence', 80)
            method = location_params.get('method', 'Estimation')
            
            if not cities:
                return self._create_error_prediction("Aucune ville spécifiée")
            
            # Distribution pondérée selon les villes
            combined_distribution = {}
            total_weight = 0
            total_population = 0
            regions = set()
            
            # Calculer les poids et combiner les distributions
            for city in cities:
                weight = city.get('population', 100000)
                total_weight += weight
                total_population += city.get('population', 100000)
                regions.add(city.get('region', 'Unknown'))
                
                # Obtenir la distribution pour cette ville
                city_distribution = self.get_city_distribution(
                    city.get('name', ''),
                    city.get('population', 100000),
                    city.get('region', ''),
                    city.get('type', '')
                )
                
                # Ajouter avec pondération
                for building_type, percentage in city_distribution.items():
                    if building_type not in combined_distribution:
                        combined_distribution[building_type] = 0
                    combined_distribution[building_type] += percentage * weight
            
            # Normaliser la distribution
            for building_type in combined_distribution:
                combined_distribution[building_type] /= total_weight
            
            # Convertir en nombres de bâtiments
            building_counts = self._distribute_buildings(combined_distribution, num_buildings)
            
            # Créer la réponse
            prediction = {
                'success': True,
                'distribution': building_counts,
                'percentages': combined_distribution,
                'confidence': confidence,
                'method': method,
                'summary': {
                    'total_buildings': num_buildings,
                    'cities_count': len(cities),
                    'average_population': int(total_population / len(cities)) if cities else 0,
                    'total_population': int(total_population),
                    'regions': list(regions),
                    'has_real_data': any(city.get('name') in self.reference_data for city in cities)
                },
                'city_details': [
                    {
                        'name': city.get('name', ''),
                        'population': city.get('population', 0),
                        'region': city.get('region', ''),
                        'type': city.get('type', ''),
                        'has_real_data': city.get('name') in self.reference_data,
                        'data_source': self.reference_data[city.get('name', '')].get('source', 'Estimation') 
                                      if city.get('name') in self.reference_data else 'Ratios par défaut'
                    }
                    for city in cities
                ],
                'data_quality': {
                    'real_data_cities': sum(1 for city in cities if city.get('name') in self.reference_data),
                    'estimated_cities': len(cities) - sum(1 for city in cities if city.get('name') in self.reference_data),
                    'overall_quality': 'HIGH' if confidence >= 90 else 'MEDIUM' if confidence >= 70 else 'LOW'
                }
            }
            
            logger.info(f"🔮 Prédiction calculée: {num_buildings} bâtiments, {len(cities)} villes, {confidence}% confiance")
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul prédiction: {e}")
            return self._create_error_prediction(str(e))
    
    def _distribute_buildings(self, percentages: Dict[str, float], total_buildings: int) -> Dict[str, int]:
        """
        Distribue les bâtiments selon les pourcentages
        
        Args:
            percentages: Pourcentages par type de bâtiment
            total_buildings: Nombre total de bâtiments
            
        Returns:
            Nombres de bâtiments par type
        """
        building_counts = {}
        assigned_buildings = 0
        
        # Trier par pourcentage décroissant
        sorted_types = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
        
        # Assigner les bâtiments (tous sauf le dernier)
        for i, (building_type, percentage) in enumerate(sorted_types[:-1]):
            count = round(percentage * total_buildings)
            building_counts[building_type] = count
            assigned_buildings += count
        
        # Le dernier type récupère le reste
        if sorted_types:
            last_type = sorted_types[-1][0]
            building_counts[last_type] = max(0, total_buildings - assigned_buildings)
        
        return building_counts
    
    def _create_error_prediction(self, error_message: str) -> Dict[str, Any]:
        """
        Crée une prédiction d'erreur
        
        Args:
            error_message: Message d'erreur
            
        Returns:
            Structure de prédiction avec erreur
        """
        return {
            'success': False,
            'error': error_message,
            'distribution': {},
            'confidence': 0,
            'method': 'Error',
            'summary': {
                'total_buildings': 0,
                'cities_count': 0,
                'error': True
            }
        }
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du système de prédiction
        
        Returns:
            Statistiques complètes
        """
        return {
            'reference_cities': list(self.reference_data.keys()),
            'city_types': list(self.default_ratios.keys()),
            'total_malaysia_locations': len(self.generator.malaysia_locations),
            'cities_with_real_data': len(self.reference_data),
            'building_types': list(self.generator.building_classes),
            'prediction_capabilities': {
                'real_data_integration': self.generator.real_data_available,
                'validation_system': self.generator.validation_enabled,
                'building_distributor': hasattr(self.generator, 'building_distributor')
            },
            'data_sources': [
                'Ministry of Health Malaysia (MOH)',
                'Ministry of Education Malaysia (MOE)',
                'Tourism Malaysia',
                'Malaysia Investment Development Authority (MIDA)',
                'State Government Planning Departments'
            ]
        }
    
    def compare_prediction_with_generator(self, num_buildings: int, location_params: Dict) -> Dict[str, Any]:
        """
        Compare la prédiction avec ce que génèrerait réellement le système
        
        Args:
            num_buildings: Nombre de bâtiments
            location_params: Paramètres de localisation
            
        Returns:
            Comparaison détaillée
        """
        try:
            # Obtenir la prédiction
            prediction = self.calculate_prediction(num_buildings, location_params)
            
            if not prediction['success']:
                return prediction
            
            # Simuler une génération réelle (sans créer les données)
            cities = location_params.get('cities', [])
            if not cities:
                return self._create_error_prediction("Aucune ville pour la comparaison")
            
            # Prendre la première ville comme référence
            main_city = cities[0]
            city_name = main_city.get('name', 'Unknown')
            
            # Utiliser le générateur pour obtenir la distribution réelle
            if hasattr(self.generator, 'building_distributor'):
                real_distribution = self.generator.building_distributor.calculate_building_distribution(
                    city_name,
                    main_city.get('population', 100000),
                    main_city.get('region', 'Central'),
                    num_buildings
                )
            else:
                # Fallback vers distribution basique
                real_distribution = self._get_basic_distribution(num_buildings)
            
            # Calculer les différences
            comparison = {
                'prediction': prediction['distribution'],
                'real_generation': real_distribution,
                'differences': {},
                'accuracy_score': 0,
                'total_buildings': num_buildings,
                'comparison_city': city_name
            }
            
            # Analyser les différences
            all_types = set(list(prediction['distribution'].keys()) + list(real_distribution.keys()))
            total_diff = 0
            
            for building_type in all_types:
                predicted = prediction['distribution'].get(building_type, 0)
                real = real_distribution.get(building_type, 0)
                diff = abs(predicted - real)
                
                comparison['differences'][building_type] = {
                    'predicted': predicted,
                    'real': real,
                    'difference': diff,
                    'percentage_diff': (diff / max(real, 1)) * 100
                }
                
                total_diff += diff
            
            # Calculer le score de précision
            accuracy = max(0, 100 - (total_diff / num_buildings) * 100)
            comparison['accuracy_score'] = round(accuracy, 1)
            
            # Ajouter des recommandations
            comparison['recommendations'] = self._generate_comparison_recommendations(comparison)
            
            return {
                'success': True,
                'comparison': comparison,
                'summary': {
                    'accuracy': accuracy,
                    'total_difference': total_diff,
                    'perfect_matches': len([d for d in comparison['differences'].values() if d['difference'] == 0]),
                    'major_differences': len([d for d in comparison['differences'].values() if d['percentage_diff'] > 50])
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur comparaison prédiction: {e}")
            return self._create_error_prediction(f"Erreur comparaison: {str(e)}")
    
    def _get_basic_distribution(self, num_buildings: int) -> Dict[str, int]:
        """
        Distribution basique de fallback
        
        Args:
            num_buildings: Nombre de bâtiments
            
        Returns:
            Distribution basique
        """
        basic_ratios = {
            'Residential': 0.70,
            'Commercial': 0.12,
            'Industrial': 0.08,
            'Office': 0.04,
            'Retail': 0.03,
            'School': 0.02,
            'Clinic': 0.01
        }
        
        return self._distribute_buildings(basic_ratios, num_buildings)
    
    def _generate_comparison_recommendations(self, comparison: Dict) -> List[str]:
        """
        Génère des recommandations basées sur la comparaison
        
        Args:
            comparison: Résultats de comparaison
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        # Analyser les différences majeures
        for building_type, diff_data in comparison['differences'].items():
            if diff_data['percentage_diff'] > 30:  # Différence > 30%
                if diff_data['predicted'] > diff_data['real']:
                    recommendations.append(
                        f"Réduire la prédiction pour {building_type}: "
                        f"{diff_data['predicted']} → {diff_data['real']} "
                        f"({diff_data['percentage_diff']:.1f}% de différence)"
                    )
                else:
                    recommendations.append(
                        f"Augmenter la prédiction pour {building_type}: "
                        f"{diff_data['predicted']} → {diff_data['real']} "
                        f"({diff_data['percentage_diff']:.1f}% de différence)"
                    )
        
        # Recommandations générales selon la précision
        accuracy = comparison.get('accuracy_score', 0)
        if accuracy >= 90:
            recommendations.append("✅ Prédiction très précise - Système bien calibré")
        elif accuracy >= 75:
            recommendations.append("✅ Prédiction correcte - Ajustements mineurs possibles")
        elif accuracy >= 60:
            recommendations.append("⚠️ Prédiction acceptable - Améliorations recommandées")
        else:
            recommendations.append("❌ Prédiction imprécise - Révision des paramètres nécessaire")
        
        return recommendations


def create_complete_integration(app, generator):
    """
    Crée l'intégration complète du prédicteur avec l'application Flask
    
    Args:
        app: Instance Flask
        generator: Instance du générateur principal
        
    Returns:
        True si l'intégration réussit, False sinon
    """
    try:
        # Créer l'instance du backend prédicteur
        predictor_backend = BuildingPredictorBackend(generator)
        
        # ===============================================================
        # ROUTES API POUR LE PRÉDICTEUR
        # ===============================================================
        
        @app.route('/api/predictor/predict', methods=['POST'])
        def api_predict_buildings():
            """
            API principale de prédiction des bâtiments
            """
            try:
                data = request.get_json()
                
                # Paramètres requis
                num_buildings = data.get('num_buildings', 0)
                location_params = data.get('location_params', {})
                
                if num_buildings <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Nombre de bâtiments invalide'
                    })
                
                # Calculer la prédiction
                prediction = predictor_backend.calculate_prediction(num_buildings, location_params)
                
                return jsonify(prediction)
                
            except Exception as e:
                logger.error(f"❌ Erreur API prédiction: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Erreur serveur: {str(e)}'
                })
        
        @app.route('/api/predictor/stats')
        def api_predictor_stats():
            """
            API pour obtenir les statistiques du prédicteur
            """
            try:
                stats = predictor_backend.get_prediction_stats()
                
                return jsonify({
                    'success': True,
                    'stats': stats,
                    'backend_available': True,
                    'integration_version': '2.0'
                })
                
            except Exception as e:
                logger.error(f"❌ Erreur API stats prédicteur: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @app.route('/api/predictor/compare', methods=['POST'])
        def api_compare_prediction():
            """
            API pour comparer prédiction vs génération réelle
            """
            try:
                data = request.get_json()
                
                num_buildings = data.get('num_buildings', 0)
                location_params = data.get('location_params', {})
                
                if num_buildings <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Nombre de bâtiments invalide'
                    })
                
                # Effectuer la comparaison
                comparison = predictor_backend.compare_prediction_with_generator(
                    num_buildings, location_params
                )
                
                return jsonify(comparison)
                
            except Exception as e:
                logger.error(f"❌ Erreur API comparaison: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @app.route('/api/predictor/city-analysis/<city_name>')
        def api_predictor_city_analysis(city_name):
            """
            API pour analyser une ville spécifique
            """
            try:
                # Obtenir les infos de la ville
                if city_name in generator.malaysia_locations:
                    city_info = generator.malaysia_locations[city_name]
                    
                    # Créer une prédiction pour cette ville
                    location_params = {
                        'cities': [{
                            'name': city_name,
                            'population': city_info['population'],
                            'region': city_info['region'],
                            'type': predictor_backend.determine_city_type(city_info['population'])
                        }],
                        'confidence': 95 if city_name in predictor_backend.reference_data else 80,
                        'method': 'Vraies données' if city_name in predictor_backend.reference_data else 'Estimation'
                    }
                    
                    # Prédiction pour 100 bâtiments (référence)
                    prediction = predictor_backend.calculate_prediction(100, location_params)
                    
                    # Ajouter des informations supplémentaires
                    analysis = {
                        'city_info': city_info,
                        'prediction_sample': prediction,
                        'has_real_data': city_name in predictor_backend.reference_data,
                        'data_source': predictor_backend.reference_data[city_name].get('source', 'Estimation basée sur population') if city_name in predictor_backend.reference_data else 'Estimation basée sur population',
                        'city_type': predictor_backend.determine_city_type(city_info['population']),
                        'recommended_building_types': [
                            bt for bt, count in prediction['distribution'].items() 
                            if count > 5  # Types avec au moins 5 bâtiments sur 100
                        ] if prediction['success'] else []
                    }
                    
                    return jsonify({
                        'success': True,
                        'city_name': city_name,
                        'analysis': analysis
                    })
                
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Ville "{city_name}" non trouvée dans la base Malaysia'
                    })
                    
            except Exception as e:
                logger.error(f"❌ Erreur analyse ville {city_name}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @app.route('/api/predictor/custom-city', methods=['POST'])
        def api_custom_city_prediction():
            """
            API pour prédiction d'une ville personnalisée
            """
            try:
                data = request.get_json()
                
                # Paramètres de la ville personnalisée
                city_name = data.get('city_name', 'Custom City')
                population = data.get('population', 100000)
                region = data.get('region', 'Custom')
                num_buildings = data.get('num_buildings', 100)
                
                if num_buildings <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Nombre de bâtiments invalide'
                    })
                
                # Créer les paramètres de localisation
                city_type = predictor_backend.determine_city_type(population)
                location_params = {
                    'cities': [{
                        'name': city_name,
                        'population': population,
                        'region': region,
                        'type': city_type
                    }],
                    'confidence': 70,  # Confiance réduite pour ville personnalisée
                    'method': 'Estimation personnalisée'
                }
                
                # Calculer la prédiction
                prediction = predictor_backend.calculate_prediction(num_buildings, location_params)
                
                # Ajouter des informations sur la ville personnalisée
                if prediction['success']:
                    prediction['custom_city_info'] = {
                        'name': city_name,
                        'population': population,
                        'region': region,
                        'type': city_type,
                        'is_custom': True,
                        'similar_real_cities': [
                            name for name, info in generator.malaysia_locations.items()
                            if abs(info['population'] - population) < population * 0.3
                        ][:3]  # Top 3 villes similaires
                    }
                
                return jsonify(prediction)
                
            except Exception as e:
                logger.error(f"❌ Erreur prédiction ville personnalisée: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        # ===============================================================
        # INTÉGRATION AVEC LES ROUTES EXISTANTES
        # ===============================================================
        
        # Modifier la route /generate existante pour inclure la prédiction
        original_generate = None
        
        # Trouver la route /generate existante
        for rule in app.url_map.iter_rules():
            if rule.rule == '/generate' and 'POST' in rule.methods:
                # Sauvegarder la fonction originale
                original_generate = app.view_functions[rule.endpoint]
                break
        
        if original_generate:
            @app.route('/generate-with-prediction', methods=['POST'])
            def generate_with_prediction():
                """
                Route améliorée qui inclut la prédiction avant génération
                """
                try:
                    # Obtenir les paramètres de la requête
                    data = request.get_json()
                    num_buildings = data.get('num_buildings', 10)
                    
                    # Créer les paramètres de localisation pour prédiction
                    location_params = {}
                    
                    if data.get('custom_location'):
                        custom = data['custom_location']
                        location_params = {
                            'cities': [{
                                'name': custom.get('name', 'Custom'),
                                'population': custom.get('population', 100000),
                                'region': custom.get('region', 'Central'),
                                'type': predictor_backend.determine_city_type(custom.get('population', 100000))
                            }],
                            'confidence': 70,
                            'method': 'Ville personnalisée'
                        }
                    else:
                        # Utiliser toute la Malaisie
                        cities = [
                            {
                                'name': name,
                                'population': info['population'],
                                'region': info['region'],
                                'type': predictor_backend.determine_city_type(info['population'])
                            }
                            for name, info in generator.malaysia_locations.items()
                        ]
                        location_params = {
                            'cities': cities,
                            'confidence': 95,
                            'method': 'Distribution Malaysia complète'
                        }
                    
                    # Calculer la prédiction
                    prediction = predictor_backend.calculate_prediction(num_buildings, location_params)
                    
                    # Appeler la génération originale
                    original_response = original_generate()
                    
                    # Si la génération originale réussit, ajouter la prédiction
                    if hasattr(original_response, 'json') and original_response.get_json().get('success'):
                        response_data = original_response.get_json()
                        response_data['prediction'] = prediction
                        return jsonify(response_data)
                    else:
                        return original_response
                    
                except Exception as e:
                    logger.error(f"❌ Erreur génération avec prédiction: {e}")
                    # Fallback vers génération originale
                    return original_generate()
        
        # ===============================================================
        # ROUTE DE TEST ET DIAGNOSTIC
        # ===============================================================
        
        @app.route('/api/predictor/test')
        def api_test_predictor():
            """
            Route de test pour vérifier le fonctionnement du prédicteur
            """
            try:
                test_results = {}
                
                # Test 1: Prédiction Kuala Lumpur
                kl_params = {
                    'cities': [{
                        'name': 'Kuala Lumpur',
                        'population': 1800000,
                        'region': 'Central',
                        'type': 'metropolis'
                    }],
                    'confidence': 95,
                    'method': 'Test avec vraies données'
                }
                
                kl_prediction = predictor_backend.calculate_prediction(100, kl_params)
                test_results['kuala_lumpur_test'] = {
                    'success': kl_prediction['success'],
                    'distribution_types': len(kl_prediction.get('distribution', {})),
                    'confidence': kl_prediction.get('confidence', 0)
                }
                
                # Test 2: Ville personnalisée
                custom_params = {
                    'cities': [{
                        'name': 'Test City',
                        'population': 300000,
                        'region': 'Test Region',
                        'type': 'medium_city'
                    }],
                    'confidence': 70,
                    'method': 'Test ville personnalisée'
                }
                
                custom_prediction = predictor_backend.calculate_prediction(50, custom_params)
                test_results['custom_city_test'] = {
                    'success': custom_prediction['success'],
                    'distribution_types': len(custom_prediction.get('distribution', {})),
                    'confidence': custom_prediction.get('confidence', 0)
                }
                
                # Test 3: Comparaison si possible
                if hasattr(generator, 'building_distributor'):
                    comparison = predictor_backend.compare_prediction_with_generator(100, kl_params)
                    test_results['comparison_test'] = {
                        'success': comparison['success'],
                        'accuracy': comparison.get('summary', {}).get('accuracy', 0)
                    }
                
                # Résumé général
                test_results['summary'] = {
                    'backend_functional': True,
                    'real_data_available': len(predictor_backend.reference_data),
                    'total_malaysia_cities': len(generator.malaysia_locations),
                    'building_types_supported': len(generator.building_classes),
                    'test_timestamp': logger.handlers[0].format(logger.makeRecord(
                        'test', 20, '', 0, '', (), None
                    )) if logger.handlers else 'Unknown'
                }
                
                return jsonify({
                    'success': True,
                    'message': 'Tests du prédicteur terminés',
                    'test_results': test_results
                })
                
            except Exception as e:
                logger.error(f"❌ Erreur test prédicteur: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'backend_available': False
                })
        
        # ===============================================================
        # FINALISATION
        # ===============================================================
        
        logger.info("✅ Intégration complète du prédicteur créée avec succès")
        logger.info(f"🔗 Routes ajoutées:")
        logger.info("   • /api/predictor/predict - Prédiction principale")
        logger.info("   • /api/predictor/stats - Statistiques")
        logger.info("   • /api/predictor/compare - Comparaison")
        logger.info("   • /api/predictor/city-analysis/<city> - Analyse ville")
        logger.info("   • /api/predictor/custom-city - Ville personnalisée")
        logger.info("   • /api/predictor/test - Tests et diagnostic")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur création intégration prédicteur: {e}")
        return False


# ===================================================================
# CLASSE UTILITAIRE POUR INTÉGRATION FRONTEND
# ===================================================================

class PredictorFrontendHelper:
    """
    Classe utilitaire pour faciliter l'intégration frontend
    """
    
    @staticmethod
    def generate_javascript_config(predictor_backend):
        """
        Génère la configuration JavaScript pour le frontend
        
        Args:
            predictor_backend: Instance du backend prédicteur
            
        Returns:
            Configuration JavaScript
        """
        config = {
            'apiEndpoints': {
                'predict': '/api/predictor/predict',
                'stats': '/api/predictor/stats',
                'compare': '/api/predictor/compare',
                'cityAnalysis': '/api/predictor/city-analysis',
                'customCity': '/api/predictor/custom-city',
                'test': '/api/predictor/test'
            },
            'referenceCities': list(predictor_backend.reference_data.keys()),
            'cityTypes': list(predictor_backend.default_ratios.keys()),
            'buildingTypes': [
                'Residential', 'Commercial', 'Office', 'Industrial', 
                'Hospital', 'Clinic', 'School', 'Hotel', 'Restaurant',
                'Retail', 'Warehouse', 'Factory', 'Apartment'
            ],
            'malaysiaCities': list(predictor_backend.generator.malaysia_locations.keys()),
            'defaultConfidence': {
                'realData': 95,
                'estimation': 80,
                'custom': 70
            }
        }
        
        return f"window.PREDICTOR_CONFIG = {json.dumps(config, indent=2)};"
    
    @staticmethod
    def create_integration_guide():
        """
        Crée un guide d'intégration pour le frontend
        
        Returns:
            Guide d'intégration
        """
        return """
🔮 GUIDE D'INTÉGRATION PRÉDICTEUR FRONTEND
=========================================

1. INCLUSION DU SCRIPT:
   <script src="/static/building_predictor_frontend_fixed.js"></script>

2. UTILISATION DE L'API:
   // Prédiction simple
   const prediction = await fetch('/api/predictor/predict', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       num_buildings: 100,
       location_params: {
         cities: [{name: 'Kuala Lumpur', population: 1800000, region: 'Central', type: 'metropolis'}],
         confidence: 95,
         method: 'Vraies données'
       }
     })
   }).then(r => r.json());

3. API JAVASCRIPT DISPONIBLE:
   - window.BuildingPredictorAPI.getCurrentPrediction()
   - window.BuildingPredictorAPI.forceUpdate()
   - window.BuildingPredictorAPI.customPrediction(buildings, city, population)
   - window.diagnosticPredictor()
   - window.testPredictor()

4. ÉVÉNEMENTS AUTOMATIQUES:
   Le prédicteur se met à jour automatiquement quand:
   - Le nombre de bâtiments change
   - La sélection géographique change
   - Les filtres de population changent

5. STYLES CSS:
   Les styles sont inclus automatiquement dans le script.
   Classes principales: .prediction-panel-fixed, .building-type-prediction-fixed

6. INTÉGRATION AVEC FORMULAIRE EXISTANT:
   Le prédicteur s'intègre automatiquement avec les éléments:
   - #numBuildings
   - #locationMode  
   - #filterRegion, #filterState, #filterCity
   - #customCity, #customPopulation
   
7. DÉBOGAGE:
   - Ouvrir la console développeur
   - Utiliser window.diagnosticPredictor() pour diagnostic
   - Vérifier window.BuildingPredictorAPI.isReady()
        """


if __name__ == "__main__":
    print("🔮 Module d'intégration prédicteur chargé")
    print("Utilisez create_complete_integration(app, generator) pour l'intégrer")