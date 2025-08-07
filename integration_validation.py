# integration_validation.py
"""
Module d'intégration pour connecter la validation automatique 
avec le générateur principal de données électriques.

Ce module permet de :
1. Valider automatiquement chaque génération
2. Ajuster les paramètres en temps réel
3. Suggérer des améliorations
4. Maintenir un historique de qualité
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Import des modules créés précédemment
try:
    from quick_validation import QuickValidator
    from building_evaluation import BuildingEvaluator
    from building_distribution import BuildingDistributor
except ImportError as e:
    print(f"⚠️ Import manquant: {e}")
    print("Assurez-vous que tous les fichiers sont dans le même dossier")

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IntegratedValidator:
    """Système de validation intégré au générateur principal"""
    
    def __init__(self):
        self.quick_validator = QuickValidator()
        self.building_evaluator = BuildingEvaluator()
        self.building_distributor = BuildingDistributor()
        
        # Configuration des seuils de qualité
        self.quality_thresholds = {
            'excellent': 85,
            'good': 70,
            'acceptable': 55,
            'poor': 40
        }
        
        # Historique des validations
        self.validation_history_file = 'validation_history.json'
        self.validation_history = self._load_validation_history()
        
        # Compteurs pour l'auto-amélioration
        self.adjustment_counters = {}
        
    def _load_validation_history(self) -> List[Dict]:
        """Charge l'historique des validations"""
        if os.path.exists(self.validation_history_file):
            try:
                with open(self.validation_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de l'historique: {e}")
        return []
    
    def _save_validation_history(self):
        """Sauvegarde l'historique des validations"""
        try:
            with open(self.validation_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.validation_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'historique: {e}")
    
    def validate_generation(self, buildings_df: pd.DataFrame, 
                          timeseries_df: pd.DataFrame = None,
                          auto_adjust: bool = False) -> Dict:
        """
        Valide une génération complète de données
        
        Args:
            buildings_df: DataFrame des bâtiments générés
            timeseries_df: DataFrame des séries temporelles (optionnel)
            auto_adjust: Si True, applique automatiquement les ajustements
            
        Returns:
            Dict avec résultats de validation et recommandations
        """
        
        validation_session = {
            'timestamp': datetime.now().isoformat(),
            'total_buildings': len(buildings_df),
            'cities_analyzed': [],
            'overall_quality': {},
            'recommendations': [],
            'adjustments_applied': [],
            'data_quality_issues': []
        }
        
        logger.info(f"🔍 Démarrage validation - {len(buildings_df)} bâtiments")
        
        # 1. Validation par ville
        city_validations = self._validate_by_city(buildings_df)
        validation_session['cities_analyzed'] = city_validations
        
        # 2. Validation des patterns de consommation (si disponible)
        if timeseries_df is not None:
            consumption_validation = self._validate_consumption_patterns(
                buildings_df, timeseries_df
            )
            validation_session['consumption_validation'] = consumption_validation
        
        # 3. Calcul de la qualité globale
        overall_quality = self._calculate_overall_quality(city_validations)
        validation_session['overall_quality'] = overall_quality
        
        # 4. Génération des recommandations
        recommendations = self._generate_recommendations(city_validations, overall_quality)
        validation_session['recommendations'] = recommendations
        
        # 5. Auto-ajustement si demandé
        if auto_adjust and overall_quality['score'] < self.quality_thresholds['good']:
            adjustments = self._apply_auto_adjustments(recommendations)
            validation_session['adjustments_applied'] = adjustments
        
        # 6. Sauvegarde dans l'historique
        self.validation_history.append(validation_session)
        self._save_validation_history()
        
        # 7. Génération du rapport
        report = self._generate_integration_report(validation_session)
        validation_session['report'] = report
        
        logger.info(f"✅ Validation terminée - Score: {overall_quality['score']}%")
        
        return validation_session
    
    def _validate_by_city(self, buildings_df: pd.DataFrame) -> List[Dict]:
        """Valide la distribution pour chaque ville"""
        
        city_validations = []
        
        # Grouper par ville
        for city in buildings_df['location'].unique():
            city_buildings = buildings_df[buildings_df['location'] == city]
            
            # Créer la distribution pour cette ville
            city_distribution = city_buildings['building_class'].value_counts().to_dict()
            
            # Valider avec le quick validator
            validation_result = self.quick_validator.validate_city_distribution(
                city, city_distribution
            )
            
            # Ajouter des métadonnées
            validation_result['buildings_count'] = len(city_buildings)
            validation_result['population'] = city_buildings.iloc[0]['population'] if len(city_buildings) > 0 else 0
            
            city_validations.append(validation_result)
            
            logger.info(f"📍 {city}: {validation_result['overall_score']}% - {validation_result['status']}")
        
        return city_validations
    
    def _validate_consumption_patterns(self, buildings_df: pd.DataFrame, 
                                     timeseries_df: pd.DataFrame) -> Dict:
        """Valide les patterns de consommation électrique"""
        
        consumption_validation = {
            'total_observations': len(timeseries_df),
            'zero_consumption_rate': (timeseries_df['y'] == 0).sum() / len(timeseries_df),
            'consumption_ranges': {},
            'anomalies': [],
            'quality_score': 0
        }
        
        # Analyser par type de bâtiment
        for building_type in buildings_df['building_class'].unique():
            building_ids = buildings_df[buildings_df['building_class'] == building_type]['unique_id']
            type_consumption = timeseries_df[timeseries_df['unique_id'].isin(building_ids)]['y']
            
            if len(type_consumption) > 0:
                consumption_validation['consumption_ranges'][building_type] = {
                    'min': float(type_consumption.min()),
                    'max': float(type_consumption.max()),
                    'mean': float(type_consumption.mean()),
                    'std': float(type_consumption.std())
                }
                
                # Détecter les anomalies
                if type_consumption.max() > type_consumption.mean() + 5 * type_consumption.std():
                    consumption_validation['anomalies'].append({
                        'type': building_type,
                        'issue': 'extreme_peak_consumption',
                        'max_value': float(type_consumption.max()),
                        'expected_max': float(type_consumption.mean() + 3 * type_consumption.std())
                    })
        
        # Score de qualité basé sur le réalisme
        quality_factors = []
        
        # Facteur 1: Taux de consommation nulle (doit être < 5%)
        zero_rate = consumption_validation['zero_consumption_rate']
        if zero_rate < 0.005:
            quality_factors.append(100)
        elif zero_rate < 0.02:
            quality_factors.append(80)
        elif zero_rate < 0.05:
            quality_factors.append(60)
        else:
            quality_factors.append(30)
        
        # Facteur 2: Absence d'anomalies extrêmes
        anomaly_penalty = min(50, len(consumption_validation['anomalies']) * 10)
        quality_factors.append(100 - anomaly_penalty)
        
        consumption_validation['quality_score'] = sum(quality_factors) / len(quality_factors)
        
        return consumption_validation
    
    def _calculate_overall_quality(self, city_validations: List[Dict]) -> Dict:
        """Calcule la qualité globale de la génération"""
        
        scores = [cv['overall_score'] for cv in city_validations if cv['overall_score'] > 0]
        
        if not scores:
            return {'score': 0, 'grade': 'UNVALIDATED', 'cities_validated': 0}
        
        overall_score = sum(scores) / len(scores)
        
        # Déterminer le grade
        if overall_score >= self.quality_thresholds['excellent']:
            grade = 'EXCELLENT'
        elif overall_score >= self.quality_thresholds['good']:
            grade = 'GOOD'
        elif overall_score >= self.quality_thresholds['acceptable']:
            grade = 'ACCEPTABLE'
        else:
            grade = 'NEEDS_IMPROVEMENT'
        
        return {
            'score': round(overall_score, 1),
            'grade': grade,
            'cities_validated': len(scores),
            'best_city_score': max(scores),
            'worst_city_score': min(scores),
            'cities_above_threshold': len([s for s in scores if s >= self.quality_thresholds['good']])
        }
    
    def _generate_recommendations(self, city_validations: List[Dict], 
                                overall_quality: Dict) -> List[Dict]:
        """Génère des recommandations d'amélioration"""
        
        recommendations = []
        
        # Analyser les patterns d'erreurs
        common_issues = {}
        
        for city_validation in city_validations:
            for rec in city_validation.get('recommendations', []):
                issue_type = self._extract_issue_type(rec)
                if issue_type not in common_issues:
                    common_issues[issue_type] = {'count': 0, 'cities': [], 'examples': []}
                common_issues[issue_type]['count'] += 1
                common_issues[issue_type]['cities'].append(city_validation['city'])
                common_issues[issue_type]['examples'].append(rec)
        
        # Créer des recommandations prioritaires
        for issue_type, issue_data in common_issues.items():
            if issue_data['count'] >= 2:  # Issue dans au moins 2 villes
                priority = 'HIGH' if issue_data['count'] >= len(city_validations) * 0.5 else 'MEDIUM'
                
                recommendations.append({
                    'type': 'SYSTEMATIC_ADJUSTMENT',
                    'priority': priority,
                    'issue': issue_type,
                    'affected_cities': issue_data['cities'],
                    'frequency': issue_data['count'],
                    'action': self._get_adjustment_action(issue_type),
                    'parameter_to_adjust': self._get_parameter_name(issue_type)
                })
        
        # Recommandations basées sur la qualité globale
        if overall_quality['score'] < self.quality_thresholds['acceptable']:
            recommendations.append({
                'type': 'GENERAL_RECALIBRATION',
                'priority': 'HIGH',
                'action': 'Recalibrer complètement le système avec plus de données réelles',
                'steps': [
                    'Collecter données officielles récentes',
                    'Ajuster tous les ratios de distribution',
                    'Tester sur échantillon réduit',
                    'Valider avant déploiement complet'
                ]
            })
        
        return recommendations
    
    def _extract_issue_type(self, recommendation: str) -> str:
        """Extrait le type d'issue d'une recommandation"""
        if 'hôpital' in recommendation.lower() or 'hospital' in recommendation.lower():
            return 'hospital_distribution'
        elif 'école' in recommendation.lower() or 'school' in recommendation.lower():
            return 'school_distribution'
        elif 'hôtel' in recommendation.lower() or 'hotel' in recommendation.lower():
            return 'hotel_distribution'
        elif 'clinique' in recommendation.lower() or 'clinic' in recommendation.lower():
            return 'clinic_distribution'
        elif 'commercial' in recommendation.lower():
            return 'commercial_distribution'
        elif 'industriel' in recommendation.lower() or 'industrial' in recommendation.lower():
            return 'industrial_distribution'
        else:
            return 'other_distribution'
    
    def _get_adjustment_action(self, issue_type: str) -> str:
        """Retourne l'action d'ajustement pour un type d'issue"""
        actions = {
            'hospital_distribution': 'Ajuster le seuil de population minimale pour les hôpitaux',
            'school_distribution': 'Revoir le ratio écoles/population selon les normes malaisiennes',
            'hotel_distribution': 'Différencier les ratios selon le type de ville (touristique/business)',
            'clinic_distribution': 'Ajuster la distribution des cliniques selon la densité urbaine',
            'commercial_distribution': 'Revoir la répartition commerciale selon l\'importance économique',
            'industrial_distribution': 'Mieux cibler les zones industrielles réelles'
        }
        return actions.get(issue_type, 'Analyser et ajuster les paramètres de distribution')
    
    def _get_parameter_name(self, issue_type: str) -> str:
        """Retourne le nom du paramètre à ajuster"""
        parameters = {
            'hospital_distribution': 'min_population_hospital',
            'school_distribution': 'schools_per_10k_ratio', 
            'hotel_distribution': 'hotel_ratio_by_city_type',
            'clinic_distribution': 'clinic_density_factor',
            'commercial_distribution': 'commercial_economic_factor',
            'industrial_distribution': 'industrial_hub_multiplier'
        }
        return parameters.get(issue_type, 'distribution_ratio')
    
    def _apply_auto_adjustments(self, recommendations: List[Dict]) -> List[Dict]:
        """Applique automatiquement les ajustements possibles"""
        
        adjustments_applied = []
        
        for rec in recommendations:
            if rec['type'] == 'SYSTEMATIC_ADJUSTMENT' and rec['priority'] == 'HIGH':
                adjustment = self._calculate_adjustment(rec)
                if adjustment:
                    adjustments_applied.append(adjustment)
                    logger.info(f"🔧 Ajustement appliqué: {adjustment['description']}")
        
        return adjustments_applied
    
    def _calculate_adjustment(self, recommendation: Dict) -> Optional[Dict]:
        """Calcule l'ajustement numérique à appliquer"""
        
        issue_type = recommendation['issue']
        
        # Exemple d'ajustements automatiques
        if issue_type == 'hospital_distribution':
            return {
                'parameter': 'min_population_hospital',
                'old_value': 80000,
                'new_value': 100000,
                'description': 'Augmentation seuil population pour hôpitaux',
                'justification': f"Erreur dans {recommendation['frequency']} villes"
            }
        elif issue_type == 'hotel_distribution':
            return {
                'parameter': 'hotel_ratio_tourist_areas',
                'old_value': 0.08,
                'new_value': 0.12,
                'description': 'Augmentation ratio hôtels zones touristiques',
                'justification': 'Sous-représentation dans destinations touristiques'
            }
        
        return None
    
    def _generate_integration_report(self, validation_session: Dict) -> str:
        """Génère un rapport d'intégration complet"""
        
        report = f"""
🔗 RAPPORT D'INTÉGRATION - VALIDATION AUTOMATIQUE
{'='*65}

📊 RÉSUMÉ DE LA GÉNÉRATION
{'-'*30}
Timestamp: {validation_session['timestamp']}
Bâtiments générés: {validation_session['total_buildings']:,}
Villes analysées: {len(validation_session['cities_analyzed'])}

🎯 QUALITÉ GLOBALE
{'-'*30}
Score: {validation_session['overall_quality']['score']}%
Grade: {validation_session['overall_quality']['grade']}
Villes validées: {validation_session['overall_quality']['cities_validated']}
Villes >70%: {validation_session['overall_quality']['cities_above_threshold']}

📍 DÉTAIL PAR VILLE
{'-'*30}
"""
        
        for city in validation_session['cities_analyzed']:
            status_emoji = "✅" if city['overall_score'] >= 70 else "⚠️" if city['overall_score'] >= 50 else "❌"
            report += f"{status_emoji} {city['city']}: {city['overall_score']}% ({city.get('buildings_count', 0)} bâtiments)\n"
        
        if validation_session['recommendations']:
            report += f"\n💡 RECOMMANDATIONS PRIORITAIRES\n{'-'*30}\n"
            for i, rec in enumerate(validation_session['recommendations'][:3], 1):
                report += f"{i}. [{rec['priority']}] {rec.get('action', 'Action non définie')}\n"
        
        if validation_session.get('adjustments_applied'):
            report += f"\n🔧 AJUSTEMENTS APPLIQUÉS\n{'-'*30}\n"
            for adj in validation_session['adjustments_applied']:
                report += f"• {adj['description']}\n"
        
        # Tendance historique
        if len(self.validation_history) > 1:
            previous_score = self.validation_history[-2]['overall_quality']['score']
            current_score = validation_session['overall_quality']['score']
            trend = "📈" if current_score > previous_score else "📉" if current_score < previous_score else "➡️"
            
            report += f"\n📈 TENDANCE QUALITÉ\n{'-'*30}\n"
            report += f"Évolution: {previous_score}% → {current_score}% {trend}\n"
        
        report += f"\n🎯 PROCHAINES ACTIONS RECOMMANDÉES\n{'-'*30}\n"
        
        if validation_session['overall_quality']['score'] >= 80:
            report += "✅ Qualité excellente - Continuer le monitoring\n"
            report += "📊 Considérer l'ajout de nouvelles villes de référence\n"
        elif validation_session['overall_quality']['score'] >= 70:
            report += "🔧 Ajustements mineurs recommandés\n"
            report += "📋 Valider sur davantage de villes\n"
        else:
            report += "❗ Recalibration nécessaire\n"
            report += "📚 Collecter plus de données de référence\n"
            report += "🔄 Tester ajustements sur échantillon réduit\n"
        
        return report
    
    def get_quality_trend(self, days: int = 30) -> Dict:
        """Analyse la tendance qualité sur les derniers jours"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_validations = [
            v for v in self.validation_history 
            if datetime.fromisoformat(v['timestamp']) >= cutoff_date
        ]
        
        if len(recent_validations) < 2:
            return {'status': 'insufficient_data', 'validations_count': len(recent_validations)}
        
        scores = [v['overall_quality']['score'] for v in recent_validations]
        
        return {
            'period_days': days,
            'validations_count': len(recent_validations),
            'average_score': sum(scores) / len(scores),
            'best_score': max(scores),
            'worst_score': min(scores),
            'trend': 'improving' if scores[-1] > scores[0] else 'declining' if scores[-1] < scores[0] else 'stable',
            'score_variance': max(scores) - min(scores)
        }
    
    def export_validation_metrics(self, filepath: str = 'validation_metrics.csv'):
        """Exporte les métriques de validation vers CSV pour analyse"""
        
        if not self.validation_history:
            logger.warning("Aucun historique de validation à exporter")
            return
        
        metrics_data = []
        
        for validation in self.validation_history:
            base_metrics = {
                'timestamp': validation['timestamp'],
                'total_buildings': validation['total_buildings'],
                'overall_score': validation['overall_quality']['score'],
                'overall_grade': validation['overall_quality']['grade'],
                'cities_count': len(validation['cities_analyzed']),
                'recommendations_count': len(validation['recommendations'])
            }
            
            # Ajouter métriques par ville
            for city in validation['cities_analyzed']:
                city_metrics = base_metrics.copy()
                city_metrics.update({
                    'city_name': city['city'],
                    'city_score': city['overall_score'],
                    'city_status': city['status'],
                    'city_population': city.get('population', 0),
                    'city_buildings': city.get('buildings_count', 0)
                })
                metrics_data.append(city_metrics)
        
        df = pd.DataFrame(metrics_data)
        df.to_csv(filepath, index=False)
        
        logger.info(f"📊 Métriques exportées vers {filepath}")
        
        return df


# Fonction d'intégration avec le générateur principal
def integrate_with_main_generator():
    """
    Exemple d'intégration avec le générateur principal app.py
    À ajouter dans les routes Flask
    """
    
    integration_code = '''
# À ajouter dans app.py

from integration_validation import IntegratedValidator

# Instance globale du validateur
integrated_validator = IntegratedValidator()

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # ... code existant de génération ...
        buildings_df = generator.generate_building_metadata(...)
        timeseries_df = generator.generate_timeseries_data(...)
        
        # NOUVELLE FONCTIONNALITÉ: Validation automatique
        validation_results = integrated_validator.validate_generation(
            buildings_df, 
            timeseries_df, 
            auto_adjust=True  # Ajustements automatiques
        )
        
        # Ajouter les résultats de validation à la réponse
        return jsonify({
            'success': True,
            'buildings': buildings_df.to_dict('records'),
            'timeseries': timeseries_df.head(500).to_dict('records'),
            'stats': stats,
            'validation': {
                'quality_score': validation_results['overall_quality']['score'],
                'grade': validation_results['overall_quality']['grade'],
                'recommendations': validation_results['recommendations'][:3],
                'report': validation_results['report']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validation-history')
def get_validation_history():
    """Nouvelle API pour consulter l'historique de validation"""
    trend = integrated_validator.get_quality_trend(days=30)
    return jsonify({
        'success': True,
        'trend': trend,
        'recent_validations': integrated_validator.validation_history[-10:]
    })
    '''
    
    return integration_code


if __name__ == "__main__":
    # Test du système d'intégration
    print("🔗 Test du système de validation intégré")
    
    # Créer des données de test
    test_buildings = pd.DataFrame([
        {'unique_id': 'test1', 'location': 'Kuala Lumpur', 'building_class': 'Residential', 'population': 1800000},
        {'unique_id': 'test2', 'location': 'Kuala Lumpur', 'building_class': 'Hospital', 'population': 1800000},
        {'unique_id': 'test3', 'location': 'Langkawi', 'building_class': 'Hotel', 'population': 65000},
    ])
    
    test_timeseries = pd.DataFrame([
        {'unique_id': 'test1', 'timestamp': '2024-01-01 12:00', 'y': 5.5},
        {'unique_id': 'test2', 'timestamp': '2024-01-01 12:00', 'y': 45.2},
        {'unique_id': 'test3', 'timestamp': '2024-01-01 12:00', 'y': 12.8},
    ])
    
    # Tester la validation intégrée
    validator = IntegratedValidator()
    results = validator.validate_generation(test_buildings, test_timeseries, auto_adjust=True)
    
    print("✅ Test terminé!")
    print(f"Score de qualité: {results['overall_quality']['score']}%")
    print("\n" + results['report'])