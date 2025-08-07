# building_evaluation.py
"""
Module pour évaluer et valider la distribution des bâtiments avec des données réelles.
Utilise diverses sources de données ouvertes et APIs pour la validation.
"""

import requests
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Tuple
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuildingEvaluator:
    """Classe pour évaluer la distribution des bâtiments avec des données réelles"""
    
    def __init__(self):
        self.real_data_sources = {
            'openstreetmap': 'https://overpass-api.de/api/interpreter',
            'malaysia_stats': 'https://www.dosm.gov.my/v1/index.php',
            'worldbank': 'https://api.worldbank.org/v2/country/MYS/indicator/',
            'google_places': 'https://maps.googleapis.com/maps/api/place/'
        }
        
        # Ratios typiques bâtiments/population selon des études urbaines
        self.typical_ratios = {
            'total_buildings_per_1000_pop': {
                'developed_countries': 180,  # Pays développés
                'malaysia_estimate': 150,    # Estimation pour la Malaisie
                'urban_areas': 200,          # Zones urbaines
                'rural_areas': 120           # Zones rurales
            },
            'building_types_ratio': {
                'residential_per_1000': 120,     # 80% des bâtiments
                'commercial_per_1000': 15,       # ~10%
                'schools_per_10000': 8,          # 8 écoles pour 10K habitants
                'hospitals_per_100000': 2,       # 2 hôpitaux pour 100K
                'clinics_per_50000': 5,          # 5 cliniques pour 50K
                'hotels_per_10000': 3,           # Moyenne générale
                'hotels_tourist_per_10000': 12,  # Zones touristiques
                'factories_per_100000': 15,      # Zones industrielles
                'offices_per_10000': 25          # Zones d'affaires
            }
        }
        
        # Données réelles approximatives pour certaines villes malaisiennes
        self.known_real_data = {
            'Kuala Lumpur': {
                'total_buildings_estimate': 280000,  # Estimation basée sur études urbaines
                'schools': 450,                       # Données ministère éducation
                'hospitals': 28,                      # Hôpitaux publics + privés
                'clinics': 180,                       # Estimation cliniques privées
                'hotels': 650,                        # Données tourisme
                'shopping_centers': 85,               # Grands centres commerciaux
                'source': 'Various gov sources + estimates'
            },
            'George Town': {
                'total_buildings_estimate': 95000,
                'schools': 180,
                'hospitals': 8,
                'clinics': 45,
                'hotels': 180,                        # Ville touristique UNESCO
                'shopping_centers': 25,
                'source': 'Penang state data + tourism board'
            },
            'Johor Bahru': {
                'total_buildings_estimate': 75000,
                'schools': 150,
                'hospitals': 6,
                'clinics': 35,
                'hotels': 85,
                'shopping_centers': 35,
                'industrial_buildings': 450,          # Hub industriel
                'source': 'Johor state industrial data'
            }
        }
    
    def get_osm_building_count(self, city_name: str, bbox: Tuple[float, float, float, float]) -> Dict:
        """
        Récupère le nombre de bâtiments via OpenStreetMap Overpass API
        bbox: (south, west, north, east)
        """
        query = f"""
        [out:json][timeout:60];
        (
            way["building"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            relation["building"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out count;
        """
        
        try:
            response = requests.post(
                self.real_data_sources['openstreetmap'],
                data={'data': query},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                total_count = sum([elem.get('tags', {}).get('total', 0) for elem in data.get('elements', [])])
                
                logger.info(f"OSM: {city_name} a environ {total_count} bâtiments mappés")
                return {
                    'city': city_name,
                    'total_buildings_osm': total_count,
                    'source': 'OpenStreetMap',
                    'note': 'Données incomplètes - dépend de la cartographie communautaire'
                }
            else:
                logger.warning(f"Erreur OSM pour {city_name}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération OSM pour {city_name}: {e}")
            return None
    
    def estimate_buildings_from_population(self, city_name: str, population: int, 
                                         city_type: str = 'urban') -> Dict:
        """Estime le nombre de bâtiments basé sur la population et le type de ville"""
        
        # Ratio de base selon le type de ville
        if city_type == 'metropolis':
            ratio = self.typical_ratios['total_buildings_per_1000_pop']['urban_areas'] * 1.1
        elif city_type == 'rural':
            ratio = self.typical_ratios['total_buildings_per_1000_pop']['rural_areas']
        else:
            ratio = self.typical_ratios['total_buildings_per_1000_pop']['malaysia_estimate']
        
        # Ajustement selon la densité urbaine malaisienne
        if population > 1000000:  # Métropoles
            ratio *= 1.15
        elif population > 500000:  # Grandes villes
            ratio *= 1.05
        elif population < 50000:   # Petites villes
            ratio *= 0.85
        
        total_buildings = int((population / 1000) * ratio)
        
        # Estimation par type de bâtiment
        building_breakdown = {
            'residential': int(total_buildings * 0.75),
            'commercial': int(total_buildings * 0.12),
            'industrial': int(total_buildings * 0.06),
            'institutional': int(total_buildings * 0.04),
            'other': int(total_buildings * 0.03)
        }
        
        # Estimations spécifiques
        specific_estimates = {
            'schools': max(1, int((population / 10000) * self.typical_ratios['building_types_ratio']['schools_per_10000'])),
            'hospitals': max(0, int((population / 100000) * self.typical_ratios['building_types_ratio']['hospitals_per_100000'])),
            'clinics': max(1, int((population / 50000) * self.typical_ratios['building_types_ratio']['clinics_per_50000'])),
            'hotels': max(1, int((population / 10000) * self.typical_ratios['building_types_ratio']['hotels_per_10000'])),
            'offices': max(1, int((population / 10000) * self.typical_ratios['building_types_ratio']['offices_per_10000']))
        }
        
        return {
            'city': city_name,
            'population': population,
            'estimated_total_buildings': total_buildings,
            'buildings_per_1000_pop': round(ratio, 1),
            'breakdown_by_category': building_breakdown,
            'specific_building_types': specific_estimates,
            'source': 'Population-based estimation',
            'methodology': f'Ratio {ratio:.1f} buildings per 1000 inhabitants'
        }
    
    def get_google_places_count(self, city_name: str, api_key: str, 
                               building_types: List[str] = None) -> Dict:
        """
        Récupère des données via Google Places API (nécessite clé API)
        ATTENTION: API payante après quotas
        """
        if not building_types:
            building_types = ['hospital', 'school', 'lodging', 'shopping_mall', 'restaurant']
        
        results = {}
        base_url = f"{self.real_data_sources['google_places']}textsearch/json"
        
        for building_type in building_types:
            try:
                params = {
                    'query': f'{building_type} in {city_name} Malaysia',
                    'key': api_key
                }
                
                response = requests.get(base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get('results', []))
                    results[building_type] = count
                    
                    logger.info(f"Google Places: {count} {building_type}s trouvés à {city_name}")
                    time.sleep(1)  # Respecter les limites de rate
                    
                else:
                    logger.warning(f"Erreur Google Places pour {building_type}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Erreur Google Places pour {building_type}: {e}")
        
        return {
            'city': city_name,
            'google_places_counts': results,
            'source': 'Google Places API',
            'note': 'Données limitées par quotas API et visibilité en ligne'
        }
    
    def compare_with_real_data(self, city_name: str, generated_distribution: Dict) -> Dict:
        """Compare la distribution générée avec les données réelles connues"""
        
        if city_name not in self.known_real_data:
            return {
                'status': 'no_real_data',
                'message': f'Pas de données réelles disponibles pour {city_name}'
            }
        
        real_data = self.known_real_data[city_name]
        comparison = {
            'city': city_name,
            'comparison_results': {},
            'accuracy_scores': {},
            'recommendations': []
        }
        
        # Comparer les types de bâtiments disponibles
        for building_type, real_count in real_data.items():
            if building_type in ['source', 'total_buildings_estimate']:
                continue
                
            generated_count = generated_distribution.get(building_type, 0)
            
            if real_count > 0:
                accuracy = min(100, (1 - abs(generated_count - real_count) / real_count) * 100)
                
                comparison['comparison_results'][building_type] = {
                    'real_count': real_count,
                    'generated_count': generated_count,
                    'difference': generated_count - real_count,
                    'accuracy_percentage': round(accuracy, 1)
                }
                
                comparison['accuracy_scores'][building_type] = accuracy
                
                # Recommandations d'ajustement
                if accuracy < 70:
                    if generated_count > real_count:
                        comparison['recommendations'].append(
                            f"Réduire {building_type}: généré {generated_count}, réel ~{real_count}"
                        )
                    else:
                        comparison['recommendations'].append(
                            f"Augmenter {building_type}: généré {generated_count}, réel ~{real_count}"
                        )
        
        # Score global
        if comparison['accuracy_scores']:
            comparison['overall_accuracy'] = round(
                sum(comparison['accuracy_scores'].values()) / len(comparison['accuracy_scores']), 1
            )
        
        return comparison
    
    def validate_distribution_logic(self, city_data: Dict) -> Dict:
        """Valide la logique de distribution selon des règles urbanistiques"""
        
        city_name = city_data.get('name', 'Unknown')
        population = city_data.get('population', 0)
        building_distribution = city_data.get('building_distribution', {})
        
        validation_results = {
            'city': city_name,
            'population': population,
            'validation_checks': {},
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        total_buildings = sum(building_distribution.values())
        
        # 1. Vérifier le ratio bâtiments/population
        buildings_per_1000 = (total_buildings / population) * 1000 if population > 0 else 0
        expected_min = 100
        expected_max = 250
        
        if buildings_per_1000 < expected_min:
            validation_results['warnings'].append(
                f"Ratio faible: {buildings_per_1000:.1f} bâtiments/1000 hab. (attendu: {expected_min}-{expected_max})"
            )
        elif buildings_per_1000 > expected_max:
            validation_results['warnings'].append(
                f"Ratio élevé: {buildings_per_1000:.1f} bâtiments/1000 hab. (attendu: {expected_min}-{expected_max})"
            )
        
        validation_results['validation_checks']['buildings_per_1000_pop'] = {
            'value': round(buildings_per_1000, 1),
            'expected_range': f"{expected_min}-{expected_max}",
            'status': 'OK' if expected_min <= buildings_per_1000 <= expected_max else 'WARNING'
        }
        
        # 2. Vérifier la cohérence des hôpitaux
        hospitals = building_distribution.get('Hospital', 0)
        if population < 80000 and hospitals > 0:
            validation_results['errors'].append(
                f"Hôpital dans une ville de {population:,} hab. (seuil recommandé: 80K)"
            )
        elif population > 300000 and hospitals == 0:
            validation_results['warnings'].append(
                f"Aucun hôpital pour {population:,} hab. (attendu: au moins 1)"
            )
        
        # 3. Vérifier les écoles (ratio critique)
        schools = building_distribution.get('School', 0)
        expected_schools = max(1, (population / 10000) * 8)  # 8 écoles pour 10K hab.
        
        if schools < expected_schools * 0.5:
            validation_results['errors'].append(
                f"Trop peu d'écoles: {schools} (attendu: ~{expected_schools:.0f})"
            )
        elif schools > expected_schools * 2:
            validation_results['warnings'].append(
                f"Beaucoup d'écoles: {schools} (attendu: ~{expected_schools:.0f})"
            )
        
        # 4. Vérifier la dominance résidentielle
        residential = building_distribution.get('Residential', 0)
        residential_percentage = (residential / total_buildings) * 100 if total_buildings > 0 else 0
        
        if residential_percentage < 50:
            validation_results['errors'].append(
                f"Résidentiel trop faible: {residential_percentage:.1f}% (attendu: 50-75%)"
            )
        elif residential_percentage > 85:
            validation_results['warnings'].append(
                f"Résidentiel très élevé: {residential_percentage:.1f}% (diversification nécessaire)"
            )
        
        # 5. Suggestions d'amélioration
        if validation_results['errors'] or validation_results['warnings']:
            validation_results['suggestions'].extend([
                "Consulter les données du Department of Statistics Malaysia (DOSM)",
                "Vérifier les plans d'urbanisme locaux",
                "Ajuster selon le profil économique de la ville",
                "Considérer les projets de développement en cours"
            ])
        
        return validation_results
    
    def generate_evaluation_report(self, city_name: str, population: int, 
                                 generated_distribution: Dict) -> str:
        """Génère un rapport complet d'évaluation"""
        
        # Collecte des données
        population_estimate = self.estimate_buildings_from_population(city_name, population)
        real_data_comparison = self.compare_with_real_data(city_name, generated_distribution)
        
        validation = self.validate_distribution_logic({
            'name': city_name,
            'population': population,
            'building_distribution': generated_distribution
        })
        
        # Génération du rapport
        report = f"""
🏙️ RAPPORT D'ÉVALUATION - {city_name.upper()}
{'='*60}

📊 DONNÉES DE BASE
Population: {population:,} habitants
Bâtiments générés: {sum(generated_distribution.values())}
Ratio: {(sum(generated_distribution.values())/population)*1000:.1f} bâtiments/1000 hab.

📈 ESTIMATION BASÉE SUR LA POPULATION
{'-'*40}
Estimation théorique: {population_estimate['estimated_total_buildings']:,} bâtiments
Ratio recommandé: {population_estimate['buildings_per_1000_pop']} bâtiments/1000 hab.

Répartition recommandée:
"""
        
        for category, count in population_estimate['breakdown_by_category'].items():
            generated_count = sum([v for k, v in generated_distribution.items() 
                                 if k.lower() in category.lower()])
            report += f"  • {category.title()}: {count} (généré: {generated_count})\n"
        
        # Comparaison avec données réelles
        if real_data_comparison.get('status') != 'no_real_data':
            report += f"\n🎯 COMPARAISON AVEC DONNÉES RÉELLES\n{'-'*40}\n"
            report += f"Score global: {real_data_comparison.get('overall_accuracy', 'N/A')}%\n\n"
            
            for building_type, comparison in real_data_comparison.get('comparison_results', {}).items():
                report += f"  • {building_type}: {comparison['generated_count']} vs {comparison['real_count']} réel "
                report += f"({comparison['accuracy_percentage']}% précision)\n"
        
        # Validation
        report += f"\n✅ VALIDATION DE LA DISTRIBUTION\n{'-'*40}\n"
        
        if validation['errors']:
            report += "ERREURS CRITIQUES:\n"
            for error in validation['errors']:
                report += f"  ❌ {error}\n"
        
        if validation['warnings']:
            report += "\nAVERTISSEMENTS:\n"
            for warning in validation['warnings']:
                report += f"  ⚠️ {warning}\n"
        
        if validation['suggestions']:
            report += "\n💡 SUGGESTIONS D'AMÉLIORATION:\n"
            for suggestion in validation['suggestions']:
                report += f"  • {suggestion}\n"
        
        report += f"\n📋 SOURCES RECOMMANDÉES POUR VALIDATION\n{'-'*40}\n"
        report += """  • Department of Statistics Malaysia (DOSM)
  • Local Authority Planning Departments
  • Malaysia Digital Economy Corporation (MDEC)
  • Tourism Malaysia
  • Ministry of Health Malaysia
  • Ministry of Education Malaysia
  • OpenStreetMap Malaysia Community
        """
        
        return report


def example_usage():
    """Exemple d'utilisation du système d'évaluation"""
    
    evaluator = BuildingEvaluator()
    
    # Exemple pour Kuala Lumpur
    city_name = "Kuala Lumpur"
    population = 1800000
    
    # Distribution générée par votre système (exemple)
    generated_distribution = {
        'Residential': 150,
        'Commercial': 30,
        'Office': 20,
        'Hospital': 3,
        'Clinic': 8,
        'School': 15,
        'Hotel': 10,
        'Restaurant': 12,
        'Industrial': 8,
        'Warehouse': 5,
        'Factory': 2,
        'Retail': 18,
        'Apartment': 25
    }
    
    # Générer le rapport
    report = evaluator.generate_evaluation_report(
        city_name, population, generated_distribution
    )
    
    print(report)
    
    # Optionnel: Récupérer des données OSM (exemple de bbox pour KL)
    # bbox = (3.0, 101.5, 3.3, 101.8)  # (south, west, north, east)
    # osm_data = evaluator.get_osm_building_count(city_name, bbox)
    # print(f"\nDonnées OSM: {osm_data}")


if __name__ == "__main__":
    example_usage()