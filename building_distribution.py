# building_distribution.py
"""
Module de distribution réaliste des types de bâtiments pour la Malaisie.
Basé sur les caractéristiques démographiques et économiques réelles des villes.
"""

import random
import numpy as np


class BuildingDistributor:
    """Classe pour gérer la distribution réaliste des types de bâtiments en Malaisie"""
    
    def __init__(self):
        # Définition des types de bâtiments avec leurs caractéristiques
        self.building_types = {
            'Residential': {
                'priority': 'essential',  # Présent partout
                'min_population': 0,      # Aucune limite
                'description': 'Logements résidentiels'
            },
            'Commercial': {
                'priority': 'high',
                'min_population': 10000,
                'description': 'Centres commerciaux, bureaux'
            },
            'Office': {
                'priority': 'medium',
                'min_population': 20000,
                'description': 'Bureaux administratifs'
            },
            'Retail': {
                'priority': 'high',
                'min_population': 5000,
                'description': 'Magasins, boutiques'
            },
            'School': {
                'priority': 'essential',
                'min_population': 5000,
                'description': 'Écoles primaires et secondaires'
            },
            'Restaurant': {
                'priority': 'medium',
                'min_population': 10000,
                'description': 'Restaurants et cafés'
            },
            'Hospital': {
                'priority': 'critical',   # Seulement dans certaines villes
                'min_population': 80000,  # Hôpitaux généraux
                'description': 'Hôpitaux généraux'
            },
            'Clinic': {  # Nouveau type plus réaliste
                'priority': 'high',
                'min_population': 15000,
                'description': 'Cliniques et centres de santé'
            },
            'Hotel': {
                'priority': 'tourism',   # Selon le type de ville
                'min_population': 30000,
                'description': 'Hôtels et hébergements'
            },
            'Industrial': {
                'priority': 'economic',  # Zones industrielles
                'min_population': 50000,
                'description': 'Usines légères'
            },
            'Factory': {
                'priority': 'economic',
                'min_population': 100000,
                'description': 'Grandes usines'
            },
            'Warehouse': {
                'priority': 'logistics',
                'min_population': 25000,
                'description': 'Entrepôts logistiques'
            },
            'Apartment': {
                'priority': 'urban',     # Surtout en ville
                'min_population': 50000,
                'description': 'Immeubles d\'appartements'
            }
        }
        
        # Caractéristiques spéciales des villes de Malaisie
        self.city_characteristics = {
            # Métropoles (>1M habitants)
            'Kuala Lumpur': {
                'type': 'metropolis',
                'economic_center': True,
                'tourist_destination': True,
                'industrial_hub': False,
                'port_city': False,
                'university_city': True
            },
            
            # Grandes villes (500K-1M)
            'George Town': {
                'type': 'major_city',
                'economic_center': True,
                'tourist_destination': True,
                'industrial_hub': True,
                'port_city': True,
                'university_city': True
            },
            'Ipoh': {
                'type': 'major_city',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': True,
                'port_city': False,
                'university_city': True
            },
            'Shah Alam': {
                'type': 'major_city',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': True,
                'port_city': False,
                'university_city': True
            },
            'Petaling Jaya': {
                'type': 'major_city',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': False,
                'port_city': False,
                'university_city': True
            },
            'Johor Bahru': {
                'type': 'major_city',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': True,
                'port_city': True,
                'university_city': True
            },
            
            # Villes moyennes importantes
            'Kota Kinabalu': {
                'type': 'regional_capital',
                'economic_center': True,
                'tourist_destination': True,
                'industrial_hub': False,
                'port_city': True,
                'university_city': True
            },
            'Kuching': {
                'type': 'regional_capital',
                'economic_center': True,
                'tourist_destination': True,
                'industrial_hub': False,
                'port_city': True,
                'university_city': True
            },
            'Malacca City': {
                'type': 'heritage_city',
                'economic_center': False,
                'tourist_destination': True,
                'industrial_hub': False,
                'port_city': True,
                'university_city': False
            },
            
            # Centres industriels
            'Port Klang': {
                'type': 'industrial_port',
                'economic_center': False,
                'tourist_destination': False,
                'industrial_hub': True,
                'port_city': True,
                'university_city': False
            },
            'Pasir Gudang': {
                'type': 'industrial_city',
                'economic_center': False,
                'tourist_destination': False,
                'industrial_hub': True,
                'port_city': True,
                'university_city': False
            },
            
            # Villes touristiques
            'Langkawi': {
                'type': 'tourist_destination',
                'economic_center': False,
                'tourist_destination': True,
                'industrial_hub': False,
                'port_city': False,
                'university_city': False
            },
            
            # Capitales d'état
            'Alor Setar': {
                'type': 'state_capital',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': False,
                'port_city': False,
                'university_city': True
            },
            'Kuantan': {
                'type': 'state_capital',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': True,
                'port_city': True,
                'university_city': True
            },
            'Kuala Terengganu': {
                'type': 'state_capital',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': False,
                'port_city': True,
                'university_city': True
            },
            'Kota Bharu': {
                'type': 'state_capital',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': False,
                'port_city': False,
                'university_city': True
            }
        }
    
    def get_city_characteristics(self, city_name, population):
        """Retourne les caractéristiques d'une ville selon sa taille et son type"""
        if city_name in self.city_characteristics:
            return self.city_characteristics[city_name]
        
        # Caractéristiques par défaut selon la population
        if population > 500000:
            return {
                'type': 'large_city',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': True,
                'port_city': False,
                'university_city': True
            }
        elif population > 200000:
            return {
                'type': 'medium_city',
                'economic_center': True,
                'tourist_destination': False,
                'industrial_hub': random.choice([True, False]),
                'port_city': False,
                'university_city': random.choice([True, False])
            }
        elif population > 50000:
            return {
                'type': 'small_city',
                'economic_center': False,
                'tourist_destination': False,
                'industrial_hub': False,
                'port_city': False,
                'university_city': False
            }
        else:
            return {
                'type': 'town',
                'economic_center': False,
                'tourist_destination': False,
                'industrial_hub': False,
                'port_city': False,
                'university_city': False
            }
    
    def calculate_building_distribution(self, city_name, population, region, total_buildings):
        """Calcule la distribution réaliste des types de bâtiments pour une ville"""
        characteristics = self.get_city_characteristics(city_name, population)
        distribution = {}
        
        # 1. RÉSIDENTIEL - Toujours majoritaire (50-70%)
        base_residential = 0.6
        if characteristics['type'] in ['town', 'small_city']:
            base_residential = 0.7  # Plus résidentiel dans les petites villes
        elif characteristics['type'] == 'metropolis':
            base_residential = 0.5  # Plus de diversité en métropole
        
        distribution['Residential'] = base_residential
        distribution['Apartment'] = 0.1 if population > 100000 else 0.0
        
        # 2. COMMERCE ET SERVICES - Selon l'importance économique
        if characteristics['economic_center']:
            distribution['Commercial'] = 0.12
            distribution['Office'] = 0.08
            distribution['Retail'] = 0.08
        else:
            distribution['Commercial'] = 0.06
            distribution['Office'] = 0.02
            distribution['Retail'] = 0.06
        
        # 3. SANTÉ - Très important pour le réalisme
        if population > 300000:  # Grandes villes - hôpitaux complets
            distribution['Hospital'] = 0.015
            distribution['Clinic'] = 0.025
        elif population > 100000:  # Villes moyennes - cliniques principales
            distribution['Hospital'] = 0.008
            distribution['Clinic'] = 0.03
        elif population > 30000:  # Petites villes - cliniques seulement
            distribution['Hospital'] = 0.0
            distribution['Clinic'] = 0.025
        else:  # Villages - centres de santé basiques
            distribution['Hospital'] = 0.0
            distribution['Clinic'] = 0.015
        
        # 4. ÉDUCATION - Essentiel partout
        if population > 100000:
            distribution['School'] = 0.06  # Plus d'écoles en ville
        elif population > 20000:
            distribution['School'] = 0.08  # Proportion plus élevée
        else:
            distribution['School'] = 0.10  # Très important dans les petites communautés
        
        # 5. INDUSTRIE - Selon le profil économique
        if characteristics['industrial_hub']:
            if population > 200000:
                distribution['Industrial'] = 0.08
                distribution['Factory'] = 0.04
                distribution['Warehouse'] = 0.03
            else:
                distribution['Industrial'] = 0.12
                distribution['Factory'] = 0.06
                distribution['Warehouse'] = 0.04
        else:
            distribution['Industrial'] = 0.02
            distribution['Factory'] = 0.0
            distribution['Warehouse'] = 0.01
        
        # 6. HÔTELLERIE - Selon le tourisme
        if characteristics['tourist_destination']:
            if city_name == 'Langkawi':  # Île touristique
                distribution['Hotel'] = 0.08
            elif city_name in ['George Town', 'Malacca City']:  # Patrimoine UNESCO
                distribution['Hotel'] = 0.05
            elif characteristics['type'] == 'metropolis':
                distribution['Hotel'] = 0.04  # Tourisme d'affaires
            else:
                distribution['Hotel'] = 0.03
        else:
            if population > 200000:
                distribution['Hotel'] = 0.02  # Quelques hôtels d'affaires
            else:
                distribution['Hotel'] = 0.005  # Très peu
        
        # 7. RESTAURATION - Selon l'urbanisation
        if characteristics['type'] in ['metropolis', 'major_city']:
            distribution['Restaurant'] = 0.06
        elif characteristics['type'] in ['regional_capital', 'state_capital']:
            distribution['Restaurant'] = 0.04
        elif characteristics['tourist_destination']:
            distribution['Restaurant'] = 0.05  # Plus de restaurants touristiques
        else:
            distribution['Restaurant'] = 0.02
        
        # 8. Ajustement final pour totaliser 100%
        total_percentage = sum(distribution.values())
        if total_percentage != 1.0:
            # Ajuster proportionnellement
            for building_type in distribution:
                distribution[building_type] = distribution[building_type] / total_percentage
        
        # Convertir en nombres de bâtiments
        building_counts = {}
        remaining_buildings = total_buildings
        
        # Assigner les bâtiments en commençant par les plus importants
        for building_type, percentage in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
            if remaining_buildings <= 0:
                building_counts[building_type] = 0
                continue
                
            count = max(0, int(percentage * total_buildings))
            
            # Contraintes minimales réalistes
            if building_type == 'Hospital' and count > 0 and population < 80000:
                count = 0  # Pas d'hôpital dans les petites villes
            elif building_type == 'Factory' and count > 0 and population < 100000:
                count = 0  # Pas de grandes usines dans les petites villes
            elif building_type == 'Apartment' and count > 0 and population < 50000:
                count = 0  # Pas d'immeubles dans les petites villes
            
            # Au moins 1 de chaque type essentiel si la ville est assez grande
            if building_type in ['Residential', 'Retail'] and count == 0 and total_buildings > 5:
                count = 1
            elif building_type == 'School' and count == 0 and population > 10000:
                count = 1
            elif building_type == 'Clinic' and count == 0 and population > 15000:
                count = 1
            
            building_counts[building_type] = min(count, remaining_buildings)
            remaining_buildings -= building_counts[building_type]
        
        # Distribuer les bâtiments restants au résidentiel
        if remaining_buildings > 0:
            building_counts['Residential'] = building_counts.get('Residential', 0) + remaining_buildings
        
        return building_counts
    
    def generate_building_type_for_city(self, city_info, building_index, total_buildings_in_city):
        """Génère un type de bâtiment spécifique pour une ville donnée"""
        city_name = city_info['name']
        population = city_info['population']
        region = city_info.get('region', 'Unknown')
        
        # Si c'est le premier appel pour cette ville, calculer la distribution
        if not hasattr(self, '_city_distributions'):
            self._city_distributions = {}
        
        if city_name not in self._city_distributions:
            self._city_distributions[city_name] = self.calculate_building_distribution(
                city_name, population, region, total_buildings_in_city
            )
        
        distribution = self._city_distributions[city_name]
        
        # Créer une liste pondérée des types de bâtiments
        building_types = []
        for building_type, count in distribution.items():
            building_types.extend([building_type] * count)
        
        if not building_types:
            return 'Residential'  # Fallback
        
        # Retourner un type aléatoire de la liste
        if building_index < len(building_types):
            return building_types[building_index]
        else:
            # Si on dépasse, utiliser un choix pondéré
            weights = list(distribution.values())
            types = list(distribution.keys())
            return np.random.choice(types, p=weights)
    
    def get_building_summary(self, city_name, population):
        """Retourne un résumé des types de bâtiments pour une ville"""
        characteristics = self.get_city_characteristics(city_name, population)
        distribution = self.calculate_building_distribution(city_name, population, 'Unknown', 100)
        
        summary = {
            'city_type': characteristics['type'],
            'characteristics': characteristics,
            'building_distribution': distribution,
            'description': self._get_city_description(characteristics, population)
        }
        
        return summary
    
    def _get_city_description(self, characteristics, population):
        """Génère une description de la ville basée sur ses caractéristiques"""
        descriptions = []
        
        if characteristics['type'] == 'metropolis':
            descriptions.append("Métropole moderne")
        elif characteristics['type'] == 'major_city':
            descriptions.append("Grande ville")
        elif characteristics['type'] == 'state_capital':
            descriptions.append("Capitale d'état")
        elif characteristics['type'] == 'heritage_city':
            descriptions.append("Ville historique")
        elif characteristics['type'] == 'tourist_destination':
            descriptions.append("Destination touristique")
        elif characteristics['type'] == 'industrial_city':
            descriptions.append("Centre industriel")
        
        if characteristics['economic_center']:
            descriptions.append("centre économique")
        if characteristics['tourist_destination']:
            descriptions.append("destination touristique")
        if characteristics['industrial_hub']:
            descriptions.append("pôle industriel")
        if characteristics['port_city']:
            descriptions.append("ville portuaire")
        if characteristics['university_city']:
            descriptions.append("ville universitaire")
        
        return f"{population:,} hab. - " + ", ".join(descriptions)