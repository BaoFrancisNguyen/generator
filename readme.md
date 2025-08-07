#Générateur de Données Électriques pour la Malaisie

## Description

Application Flask qui génère des données synthétiques réalistes de consommation électrique spécialement adaptées à la **Malaisie**. Basée sur l'analyse de vrais datasets de demande électrique, elle produit des séries temporelles avec des patterns climatiques tropicaux, des spécificités culturelles malaisiennes, et des coordonnées géographiques précises.

### Objectif
Créer des datasets de test/entraînement pour l'analyse de consommation électrique en Malaisie avec des caractéristiques ultra-réalistes.

---

## Installation

### Prérequis
- Python 3.8+
- pip (gestionnaire de paquets Python)

### Étapes d'installation

```bash
# 1. Cloner ou télécharger le projet
git clone https://github.com/BaoFrancisNguyen/generator

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv

# 3. Activer l'environnement virtuel
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer l'application
python run.py
```

### Structure des fichiers
```
projet/
├── app.py              # Application Flask principale
├── run.py              # Script de démarrage
├── requirements.txt    # Dépendances Python
├── generated_data/     # Dossier de sortie (créé automatiquement)
└── README.md          # Cette documentation
```

---

## Interface Utilisateur

### Accès
Une fois l'application lancée, ouvrir dans le navigateur :

- **Interface principale** : http://localhost:5000
- **API statistiques** : http://localhost:5000/api/stats

### Interface Web

L'application propose une interfaceavec 3 se ctions principales :

#### 1. **Formulaire de Configuration**

| Champ | Type | Description | Valeurs | Défaut |
|-------|------|-------------|---------|--------|
| **Nombre de Bâtiments** | Nombre | Quantité de bâtiments à générer | 1 - 1000 | 50 |
| **Fréquence d'Échantillonnage** | Liste | Intervalle entre les mesures | 30T, 1H, 15T | 30T |
| **Date de Début** | Date | Début de la période de génération | Format YYYY-MM-DD | 2024-01-01 |
| **Date de Fin** | Date | Fin de la période de génération | Format YYYY-MM-DD | 2024-01-31 |

**Notes sur les paramètres :**
- **30T** = 30 minutes (format identique à votre dataset original)
- **1H** = 1 heure 
- **15T** = 15 minutes
- Plus la période est longue, plus les patterns saisonniers sont visibles

#### 2. **Boutons d'Action**

| Bouton | Fonction | Résultat |
|--------|----------|----------|
| ** Générer et Visualiser** | Crée les données et les affiche dans l'interface | Aperçu immédiat + statistiques |
| ** Générer et Télécharger** | Crée les données et les sauvegarde en fichiers | 2 fichiers .parquet |
| ** Voir un Échantillon** | Génère un petit exemple (5 bâtiments, 2 jours) | Démonstration rapide |

#### 3. **Zone de Résultats**

Après génération, affichage de :
- **Statistiques** : Nombre d'observations, moyenne, maximum, etc.
- **Aperçu des métadonnées** : Tableau des bâtiments avec villes, types, coordonnées
- **Aperçu des séries temporelles** : Échantillon des données de consommation

---

## Inputs (Entrées)

### Paramètres de Configuration

| Paramètre | Type | Range | Impact |
|-----------|------|-------|--------|
| `num_buildings` | Integer | 1-1000 | **Performance** : 100 bâtiments × 1 mois ≈ 4.3M observations |
| `start_date` | String | "YYYY-MM-DD" | **Patterns saisonniers** : Plus long = plus réaliste |
| `end_date` | String | "YYYY-MM-DD" | **Taille du dataset** : 1 jour = 48 observations/bâtiment |
| `freq` | String | "30T", "1H", "15T" | **Granularité temporelle** |

### Recommandations d'usage

| Cas d'usage | Bâtiments | Période | Fréquence | Observations approx. |
|-------------|-----------|---------|-----------|---------------------|
| **Test rapide** | 5 | 1 semaine | 30T | ~1,680 |
| **Développement** | 50 | 1 mois | 30T | ~72,000 |
| **Production légère** | 200 | 3 mois | 1H | ~432,000 |
| **Dataset complet** | 500 | 1 an | 30T | ~8,760,000 |

---

## Outputs (Sorties)

### 1. **Fichiers Générés**

Lors du téléchargement, 2 fichiers .parquet sont créés dans le dossier `generated_data/` :

#### **Fichier 1 : Métadonnées des Bâtiments** (`malaysia_buildings_YYYYMMDD_HHMMSS.parquet`)

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| `unique_id` | String | Identifiant unique 16 caractères | `a4077c2f0ac5f939` |
| `dataset` | String | Nom du dataset | `malaysia_electricity_v1` |
| `building_id` | String | ID du bâtiment avec code état | `MY_SEL_000001` |
| `location_id` | String | ID de localisation | `MY_12345` |
| `latitude` | Float | Coordonnée GPS précise | `3.1581` |
| `longitude` | Float | Coordonnée GPS précise | `101.7123` |
| `location` | String | Nom de la ville | `Kuala Lumpur` |
| `state` | String | État de Malaisie | `Federal Territory` |
| `region` | String | Région géographique | `Central` |
| `population` | Integer | Population de la ville | `1800000` |
| `timezone` | String | Fuseau horaire | `Asia/Kuala_Lumpur` |
| `building_class` | String | Type de bâtiment | `Commercial` |
| `cluster_size` | Integer | Taille du cluster (1-250) | `42` |
| `freq` | String | Fréquence d'échantillonnage | `30T` |

#### **Fichier 2 : Séries Temporelles** (`malaysia_demand_YYYYMMDD_HHMMSS.parquet`)

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| `unique_id` | String | Identifiant du bâtiment | `a4077c2f0ac5f939` |
| `timestamp` | Datetime | Horodatage précis | `2024-01-01 00:30:00` |
| `y` | Float | Consommation électrique (kWh) | `45.672` |

### 2. **Visualisation Web**

#### **Statistiques Affichées**
- **Total des observations** : Nombre de lignes générées
- **Nombre de bâtiments** : Quantité unique de bâtiments
- **Consommation moyenne** : Moyenne de toutes les valeurs (kWh)
- **Pic maximum** : Valeur de consommation la plus élevée (kWh)

#### **Tableaux d'Aperçu**
- **Métadonnées** : 10 premiers bâtiments avec villes, types, coordonnées
- **Consommation** : 15 premières observations avec timestamps

### 3. **API REST**

#### **Endpoint : `/api/stats`** (GET)
Retourne les informations sur le générateur :

```json
{
  "success": true,
  "building_classes": ["Residential", "Commercial", ...],
  "malaysia_locations": {
    "Kuala Lumpur": {
      "population": 1800000,
      "state": "Federal Territory",
      "region": "Central"
    }
  },
  "consumption_patterns": {
    "Residential": {
      "description": "Consommation de base: 0.5 kWh, Pic: 12.0 kWh",
      "base": 0.5,
      "peak": 12.0
    }
  },
  "malaysia_specific_features": [...]
}
```

---

## 🇲🇾 Spécificités Malaisie

### **Villes Réelles** (60+ localisations)

Le générateur utilise de vraies villes malaisiennes avec leurs données démographiques :

| Catégorie | Exemples | Population | Caractéristiques |
|-----------|----------|------------|------------------|
| **Métropoles** | Kuala Lumpur, George Town, Johor Bahru | 400K - 1.8M | Plus de bureaux, commerces |
| **Villes moyennes** | Ipoh, Kuantan, Kota Kinabalu | 200K - 400K | Équilibre résidentiel/commercial |
| **Petites villes** | Langkawi, Mersing, Beaufort | 35K - 200K | Majoritairement résidentiel |

### **Patterns Climatiques Tropicaux**

#### **Facteurs Horaires**
- **6h-8h** : Pic matinal (avant la chaleur)
- **11h-16h** : **Maximum de climatisation** (heures les plus chaudes)
- **17h-21h** : Activité élevée (après-midi/soirée)
- **22h-5h** : Consommation nocturne réduite

#### **Facteurs Saisonniers**
| Mois | Saison | Facteur Clim | Description |
|------|--------|--------------|-------------|
| **Nov-Fév** | Mousson NE | 0.9-1.1× | Moins de climatisation |
| **Mar-Avr** | Transition | 1.2-1.5× | Période chaude + Ramadan |
| **Mai-Août** | Saison sèche | 1.3-1.7× | **Maximum de climatisation** |
| **Sep-Oct** | Variable | 1.0-1.3× | Climat changeant |

### **Spécificités Culturelles**

#### **Patterns Hebdomadaires**
- **Vendredi après-midi** : Réduction d'activité (prière du vendredi)
- **Weekend** : Plus de consommation résidentielle
- **Jours ouvrables** : Pics dans les bureaux/commerces

#### **Période de Ramadan** (Mar-Avr approximatif)
- **4h-17h** : Consommation résidentielle réduite de 40% (jeûne)
- **18h-23h** : Consommation résidentielle augmentée de 40% (Iftar, activités nocturnes)

### **Types de Bâtiments**

| Type | Consommation Base | Consommation Pic | Facteur Nuit | Usage Principal |
|------|------------------|------------------|--------------|----------------|
| **Residential** | 0.5 kWh | 12.0 kWh | 0.3 | Logements familiaux |
| **Commercial** | 5.0 kWh | 80.0 kWh | 0.2 | Centres commerciaux |
| **Industrial** | 20.0 kWh | 200.0 kWh | 0.7 | Usines, manufactures |
| **Office** | 3.0 kWh | 45.0 kWh | 0.1 | Bureaux, administrations |
| **Hospital** | 25.0 kWh | 70.0 kWh | 0.8 | Activité 24h/24 |
| **School** | 1.0 kWh | 25.0 kWh | 0.05 | Actif 7h-15h uniquement |
| **Hotel** | 8.0 kWh | 40.0 kWh | 0.6 | Tourisme, hébergement |
| **Restaurant** | 3.0 kWh | 60.0 kWh | 0.2 | Pics aux heures de repas |

---

## 🔧 Personnalisation

### Ajouter de Nouvelles Villes

Dans `app.py`, section `self.malaysia_locations` :

```python
'Nouvelle Ville': {
    'population': 150000, 
    'state': 'Nom État', 
    'region': 'Région'
}
```

Puis ajouter les coordonnées dans `generate_coordinates()`.

### Modifier les Patterns de Consommation

Dans `self.consumption_patterns` :

```python
'Nouveau Type': {
    'base': 2.0,      # Consommation minimale (kWh)
    'peak': 25.0,     # Consommation maximale (kWh) 
    'variance': 5.0,  # Variabilité du bruit
    'night_factor': 0.4  # Facteur nocturne (0-1)
}
```

### Ajuster les Facteurs Climatiques

Dans `calculate_realistic_consumption()`, modifier :

```python
# Heures de pic de climatisation
if 10 <= hour <= 17:  # Étendre les heures chaudes
    climate_factor = 1.5 + 0.4 * random.random()
```

---

## 🚨 Dépannage

### Erreurs Communes

| Erreur | Cause | Solution |
|--------|-------|----------|
| `ModuleNotFoundError` | Dépendances manquantes | `pip install -r requirements.txt` |
| `The number of weights does not match` | Décalage classes/poids | Vérifier les listes de poids (12 éléments) |
| `Permission denied` | Dossier protégé | Changer de répertoire ou permissions |
| `Port already in use` | Port 5000 occupé | Changer le port dans `app.run(port=5001)` |

### Problèmes de Performance

| Symptôme | Cause | Solution |
|----------|-------|----------|
| Génération lente | Trop de données | Réduire période ou nombre de bâtiments |
| Mémoire insuffisante | Dataset trop volumineux | Traitement par chunks |
| Interface qui plante | Trop d'affichage | Limiter l'aperçu à 500 lignes |

### Logs et Debug

Pour activer les logs détaillés :
```python
# Dans app.py, modifier :
app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## Exemples d'Usage

### 1. **Dataset de Test Rapide**
```
Bâtiments: 10
Période: 2024-01-01 à 2024-01-07  
Fréquence: 1H
→ Résultat: ~1,680 observations, génération <30s
```

### 2. **Dataset d'Entraînement ML**
```
Bâtiments: 200
Période: 2024-01-01 à 2024-03-31
Fréquence: 30T  
→ Résultat: ~864,000 observations, génération ~3-5 minutes
```

### 3. **Dataset de Production**
```
Bâtiments: 1000
Période: 2024-01-01 à 2024-12-31
Fréquence: 30T
→ Résultat: ~17,520,000 observations, génération ~15-30 minutes
```

---

## Intégration

### Avec Pandas
```python
import pandas as pd

# Charger les données générées
buildings = pd.read_parquet('malaysia_buildings_20241201_143022.parquet')
timeseries = pd.read_parquet('malaysia_demand_20241201_143022.parquet')

# Fusionner pour l'analyse
full_data = timeseries.merge(buildings, on='unique_id')

# Analyser par ville
city_consumption = full_data.groupby('location')['y'].agg(['mean', 'max', 'count'])
```

### Avec Machine Learning
```python
from sklearn.model_selection import train_test_split

# Préparer les features temporelles
full_data['hour'] = full_data['timestamp'].dt.hour
full_data['month'] = full_data['timestamp'].dt.month
full_data['is_weekend'] = full_data['timestamp'].dt.dayofweek >= 5

# Features pour l'entraînement
features = ['hour', 'month', 'is_weekend', 'population', 'building_class_encoded']
X = full_data[features]
y = full_data['y']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
```

---

## Checklist de Validation

Avant d'utiliser les données générées, vérifiez :

- [ ] **Cohérence temporelle** : Pas de trous dans les timestamps
- [ ] **Patterns réalistes** : Pics aux bonnes heures (11h-16h pour clim)
- [ ] **Distribution géographique** : Villes malaisiennes uniquement
- [ ] **Valeurs aberrantes** : Pas de consommation négative
- [ ] **Saisonnalité** : Variations selon les mois
- [ ] **Types de bâtiments** : Distribution logique par taille de ville
- [ ] **Format de sortie** : Compatible avec votre dataset original

---

## Contribution

Pour améliorer le générateur :

1. **Nouvelles villes** : Ajouter des localisations manquantes
2. **Patterns améliorés** : Affiner les algorithmes climatiques  
3. **Types de bâtiments** : Ajouter de nouvelles catégories
4. **Interface** : Améliorer l'UX/UI
5. **Performance** : Optimiser la génération de gros volumes

---

## Licence

Projet open-source pour usage éducatif et recherche.

---

## Support

En cas de problème :
1. Vérifier cette documentation
2. Consulter les logs d'erreur
3. Tester avec des paramètres plus petits
4. Vérifier les permissions de fichiers

---
