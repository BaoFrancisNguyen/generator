# complete_integration.py
"""
Intégration complète du système de prédiction des bâtiments.
Combine frontend JavaScript et backend Python pour une expérience utilisateur fluide.
"""

from flask import Flask, jsonify, request, render_template_string
import logging
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Template HTML complet avec le prédicteur intégré
ENHANCED_INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🇲🇾⚡ Générateur de Données Électriques - Malaisie avec Prédicteur</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <style>
        /* Styles spécifiques au prédicteur */
        .predictor-container {
            background: linear-gradient(135deg, #e8f5e8 0%, #f0fff0 100%);
            border: 2px solid #4caf50;
            border-radius: 15px;
            padding: 25px;
            margin: 25px 0;
            box-shadow: 0 8px 25px rgba(76, 175, 80, 0.2);
        }
        
        .predictor-header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .predictor-header h3 {
            color: #2e7d32;
            font-size: 1.4em;
            margin-bottom: 10px;
        }
        
        .predictor-status {
            display: inline-block;
            padding: 8px 16px;
            background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
            color: white;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .predictor-status.estimated {
            background: linear-gradient(135deg, #ff9800 0%, #ffc107 100%);
        }
        
        .predictor-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .predictor-info {
            background: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #c8e6c9;
        }
        
        .predictor-distribution {
            grid-column: 1 / -1;
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #c8e6c9;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .building-prediction-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            margin: 5px 0;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #4caf50;
            transition: all 0.3s ease;
        }
        
        .building-prediction-item:hover {
            background: #f0f0f0;
            transform: translateX(3px);
        }
        
        .building-prediction-item.major {
            border-left-color: #2e7d32;
            font-weight: bold;
            background: #e8f5e8;
        }
        
        .prediction-count {
            background: #4caf50;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
            min-width: 40px;
            text-align: center;
        }
        
        .prediction-percentage {
            color: #666;
            font-size: 0.9em;
            margin-left: 10px;
        }
        
        .confidence-indicator {
            text-align: center;
            margin-top: 15px;
        }
        
        .confidence-bar {
            width: 100%;
            height: 10px;
            background: #eeeeee;
            border-radius: 5px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #4caf50 0%, #2e7d32 100%);
            transition: width 0.5s ease;
        }
        
        .prediction-loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .prediction-error {
            text-align: center;
            padding: 20px;
            color: #f44336;
            background: #ffebee;
            border-radius: 8px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .predictor-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇲🇾⚡ Générateur de Données Électriques</h1>
            <p style="font-size: 1.2em; opacity: 0.9;">Malaisie - Données ultra-réalistes avec prédicteur intelligent</p>
        </div>

        <!-- Prédicteur de bâtiments intégré -->
        <div class="predictor-container" id="predictorContainer">
            <div class="predictor-header">
                <h3>🔮 Prédicteur de Distribution des Bâtiments</h3>
                <span class="predictor-status" id="predictorStatus">🎯 VRAIES DONNÉES MALAYSIA</span>
            </div>
            
            <div class="predictor-grid">
                <div class="predictor-info">
                    <h4>📍 Localisation</h4>
                    <div id="predictorLocation">Toute la Malaisie</div>
                    <small id="predictorPopulation">Population mixte</small>
                </div>
                
                <div class="predictor-info">
                    <h4>🏗️ Prédiction</h4>
                    <div id="predictorBuildings">0 bâtiments</div>
                    <small id="predictorMethod">Sélectionnez les paramètres</small>
                </div>
                
                <div class="predictor-distribution">
                    <h4>📊 Distribution Prédite</h4>
                    <div id="predictorDistributionContent">
                        <div class="prediction-loading">
                            🏗️ Spécifiez le nombre de bâtiments pour voir la prédiction
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="confidence-indicator">
                <div class="confidence-bar">
                    <div class="confidence-fill" id="predictorConfidence" style="width: 0%"></div>
                </div>
                <small>Confiance: <span id="predictorConfidenceText">0%</span> - Basé sur données officielles Malaysia</small>
            </div>
        </div>

        <!-- Formulaire principal -->
        <div class="card">
            <h2>📊 Configuration de la Génération</h2>
            
            <!-- Section de filtrage géographique -->
            <div class="card" style="background: #f8f9fa; margin-bottom: 25px;">
                <h3 style="color: #495057; margin-bottom: 20px;">🗺️ Filtrage Géographique</h3>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="locationMode">Mode de Localisation</label>
                        <select id="locationMode" onchange="toggleLocationMode()">
                            <option value="all">🇲🇾 Toute la Malaisie</option>
                            <option value="filter">🎯 Filtrer par zone</option>
                            <option value="custom">➕ Localisation personnalisée</option>
                        </select>
                    </div>
                </div>
                
                <!-- Filtres par zone -->
                <div id="filterSection" style="display: none;">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="filterRegion">🌏 Région</label>
                            <select id="filterRegion" onchange="updateStateOptions()">
                                <option value="all">Toutes les régions</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="filterState">🏛️ État</label>
                            <select id="filterState" onchange="updateCityOptions()">
                                <option value="all">Tous les états</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="filterCity">🏙️ Ville</label>
                            <select id="filterCity">
                                <option value="all">Toutes les villes</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="populationRange">👥 Population</label>
                            <select id="populationRange" onchange="updatePopulationInputs()">
                                <option value="all">Toutes tailles</option>
                                <option value="large">Grandes villes (>500K)</option>
                                <option value="medium">Villes moyennes (200K-500K)</option>
                                <option value="small">Petites villes (<200K)</option>
                                <option value="custom">Plage personnalisée</option>
                            </select>
                        </div>
                    </div>
                    
                    <div id="customPopulationRange" style="display: none;">
                        <div class="form-grid">
                            <div class="form-group">
                                <label for="popMin">Population Min</label>
                                <input type="number" id="popMin" placeholder="Ex: 50000">
                            </div>
                            <div class="form-group">
                                <label for="popMax">Population Max</label>
                                <input type="number" id="popMax" placeholder="Ex: 1000000">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Localisation personnalisée -->
                <div id="customSection" style="display: none;">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="customCity">🏙️ Nom de la Ville</label>
                            <input type="text" id="customCity" placeholder="Ex: Nouvelle Ville">
                        </div>
                        
                        <div class="form-group">
                            <label for="customState">🏛️ État/Province</label>
                            <input type="text" id="customState" placeholder="Ex: Nouvel État">
                        </div>
                        
                        <div class="form-group">
                            <label for="customRegion">🌏 Région</label>
                            <select id="customRegion">
                                <option value="Central">Central</option>
                                <option value="Northern">Northern</option>
                                <option value="Southern">Southern</option>
                                <option value="East Coast">East Coast</option>
                                <option value="East Malaysia">East Malaysia</option>
                                <option value="Custom">Région personnalisée</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="customPopulation">👥 Population</label>
                            <input type="number" id="customPopulation" placeholder="Ex: 250000">
                        </div>
                    </div>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="customLat">📍 Latitude</label>
                            <input type="number" step="0.000001" id="customLat" placeholder="Ex: 3.1390">
                        </div>
                        
                        <div class="form-group">
                            <label for="customLon">📍 Longitude</label>
                            <input type="number" step="0.000001" id="customLon" placeholder="Ex: 101.6869">
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="numBuildings">🏢 Nombre de Bâtiments</label>
                    <input type="number" id="numBuildings" value="50" min="1" max="10000" onchange="updateEstimation()" oninput="updateEstimation()">
                    <small id="buildingGuidance" style="color: #666; font-size: 0.9em; margin-top: 5px; display: block;"></small>
                </div>
                
                <div class="form-group">
                    <label for="freq">⏰ Fréquence d'Échantillonnage</label>
                    <select id="freq" onchange="updateEstimation()">
                        <option value="5T">5 minutes (très détaillé)</option>
                        <option value="15T">15 minutes (détaillé)</option>
                        <option value="30T" selected>30 minutes</option>
                        <option value="1H">1 heure (standard)</option>
                        <option value="2H">2 heures</option>
                        <option value="6H">6 heures</option>
                        <option value="12H">12 heures (2x/jour)</option>
                        <option value="1D">1 jour (quotidien)</option>
                        <option value="1W">1 semaine (hebdomadaire)</option>
                        <option value="1M">1 mois (mensuel)</option>
                    </select>
                    <small id="freqInfo" style="color: #666; font-size: 0.9em;"></small>
                </div>
                
                <div class="form-group">
                    <label for="startDate">📅 Date de Début</label>
                    <input type="date" id="startDate" value="2024-01-01" onchange="updateEstimation()">
                </div>
                
                <div class="form-group">
                    <label for="endDate">📅 Date de Fin</label>
                    <input type="date" id="endDate" value="2024-01-31" onchange="updateEstimation()">
                </div>
            </div>
            
            <!-- Section d'estimation -->
            <div class="estimation-card" id="estimationCard">
                <h3>📊 Estimation du Dataset</h3>
                <div class="estimation-grid">
                    <div class="estimation-item">
                        <span class="estimation-label">📈 Observations totales:</span>
                        <span class="estimation-value" id="totalObservations">-</span>
                    </div>
                    <div class="estimation-item">
                        <span class="estimation-label">💾 Taille fichier (~):</span>
                        <span class="estimation-value" id="fileSize">-</span>
                    </div>
                    <div class="estimation-item">
                        <span class="estimation-label">⏱️ Temps génération (~):</span>
                        <span class="estimation-value" id="generationTime">-</span>
                    </div>
                    <div class="estimation-item">
                        <span class="estimation-label">🎯 Cas d'usage:</span>
                        <span class="estimation-value" id="useCase">-</span>
                    </div>
                </div>
            </div>
            
            <!-- Section de recommandations -->
            <div class="guidance-section">
                <h4>💡 Guide de Configuration</h4>
                <div class="guidance-recommendations">
                    <div class="recommendation-item">
                        <strong>🧪 Test Rapide</strong><br>
                        5-20 bâtiments, 1 semaine, 1H<br>
                        <em>~3K observations, <10s</em>
                    </div>
                    <div class="recommendation-item">
                        <strong>📚 Développement</strong><br>
                        50-200 bâtiments, 1-3 mois, 30T<br>
                        <em>~200K observations, 1-3min</em>
                    </div>
                    <div class="recommendation-item">
                        <strong>🤖 Machine Learning</strong><br>
                        200-1000 bâtiments, 6-12 mois, 1H<br>
                        <em>~1M observations, 5-10min</em>
                    </div>
                    <div class="recommendation-item">
                        <strong>🏭 Production</strong><br>
                        1000-5000 bâtiments, 1-3 ans, 30T<br>
                        <em>~20M observations, 20+ min</em>
                    </div>
                    <div class="recommendation-item">
                        <strong>📊 Analyse Quotidienne</strong><br>
                        100-500 bâtiments, 1 an, 1D<br>
                        <em>~180K observations, 1min</em>
                    </div>
                    <div class="recommendation-item">
                        <strong>📈 Tendances Long Terme</strong><br>
                        1000+ bâtiments, 5+ ans, 1W/1M<br>
                        <em>~500K observations, 3-5min</em>
                    </div>
                </div>
            </div>

            <div class="button-group">
                <button class="btn" onclick="generateData()">🚀 Générer et Visualiser</button>
                <button class="btn btn-success" onclick="downloadData()">💾 Générer et Télécharger</button>
                <button class="btn btn-warning" onclick="showSample()">👁️ Voir un Échantillon</button>
            </div>
        </div>

        <!-- Zone de chargement -->
        <div class="loading" id="loading">
            <h2>🌴 Génération en cours pour la Malaisie...</h2>
            <p>Création de données électriques tropicales réalistes, veuillez patienter.</p>
            <div style="margin-top: 20px;">
                <div class="spinner"></div>
            </div>
        </div>

        <!-- Résultats -->
        <div class="results" id="results">
            <div id="alerts"></div>
            <div class="stats-grid" id="statsGrid"></div>
            <div id="dataPreview"></div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="{{ url_for('static', filename='script.js') }}"></script>
    <script>
        // Script intégré pour le prédicteur
        class IntegratedBuildingPredictor {
            constructor() {
                this.apiEndpoint = '/api/predict-buildings';
                this.currentPrediction = null;
                this.isLoading = false;
                
                this.initializeEventListeners();
                console.log('🔮 Prédicteur intégré initialisé');
            }
            
            initializeEventListeners() {
                const watchedElements = [
                    'numBuildings', 'locationMode', 'filterRegion', 'filterState', 
                    'filterCity', 'populationRange', 'popMin', 'popMax',
                    'customCity', 'customState', 'customRegion', 'customPopulation'
                ];

                watchedElements.forEach(elementId => {
                    const element = document.getElementById(elementId);
                    if (element) {
                        element.addEventListener('change', () => this.updatePrediction());
                        element.addEventListener('input', () => this.debouncedUpdate());
                    }
                });
            }
            
            debouncedUpdate() {
                clearTimeout(this.updateTimeout);
                this.updateTimeout = setTimeout(() => this.updatePrediction(), 500);
            }
            
            async updatePrediction() {
                if (this.isLoading) return;
                
                try {
                    const numBuildings = parseInt(document.getElementById('numBuildings')?.value) || 0;
                    
                    if (numBuildings === 0) {
                        this.showEmptyState();
                        return;
                    }
                    
                    this.showLoading();
                    this.isLoading = true;
                    
                    const requestData = this.buildRequestData(numBuildings);
                    const response = await fetch(this.apiEndpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(requestData)
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        this.currentPrediction = result;
                        this.displayPrediction(result);
                    } else {
                        this.showError(result.error || 'Erreur de prédiction');
                    }
                    
                } catch (error) {
                    console.error('Erreur prédiction:', error);
                    this.showError(error.message);
                } finally {
                    this.isLoading = false;
                }
            }
            
            buildRequestData(numBuildings) {
                const locationMode = document.getElementById('locationMode')?.value || 'all';
                
                const requestData = {
                    num_buildings: numBuildings,
                    location_mode: locationMode
                };
                
                if (locationMode === 'filter') {
                    const region = document.getElementById('filterRegion')?.value;
                    const state = document.getElementById('filterState')?.value;
                    const city = document.getElementById('filterCity')?.value;
                    const popMin = document.getElementById('popMin')?.value;
                    const popMax = document.getElementById('popMax')?.value;
                    
                    requestData.location_filter = {
                        region: region !== 'all' ? region : null,
                        state: state !== 'all' ? state : null,
                        city: city !== 'all' ? city : null,
                        population_min: popMin ? parseInt(popMin) : null,
                        population_max: popMax ? parseInt(popMax) : null
                    };
                } else if (locationMode === 'custom') {
                    const customCity = document.getElementById('customCity')?.value?.trim();
                    const customState = document.getElementById('customState')?.value?.trim();
                    const customRegion = document.getElementById('customRegion')?.value;
                    const customPop = document.getElementById('customPopulation')?.value;
                    
                    if (customCity && customState && customPop) {
                        requestData.custom_location = {
                            name: customCity,
                            state: customState,
                            region: customRegion || 'Central',
                            population: parseInt(customPop) || 100000
                        };
                    }
                }
                
                return requestData;
            }
            
            displayPrediction(result) {
                const prediction = result.prediction;
                const quality = result.quality_metrics;
                const locationParams = result.location_params;
                
                this.updatePredictionInfo(prediction, quality, locationParams);
                this.updateDistribution(prediction);
                this.updateConfidence(quality);
                
                console.log('✅ Prédiction affichée:', prediction.total_buildings, 'bâtiments');
            }
            
            updatePredictionInfo(prediction, quality, locationParams) {
                const locationElement = document.getElementById('predictorLocation');
                const populationElement = document.getElementById('predictorPopulation');
                const buildingsElement = document.getElementById('predictorBuildings');
                const methodElement = document.getElementById('predictorMethod');
                const statusElement = document.getElementById('predictorStatus');
                
                if (locationElement) {
                    const cities = locationParams.cities || [];
                    if (cities.length === 1) {
                        locationElement.textContent = `${cities[0].name} (${cities[0].region})`;
                    } else if (cities.length <= 3) {
                        locationElement.textContent = cities.map(c => c.name).join(', ');
                    } else {
                        const regions = [...new Set(cities.map(c => c.region))];
                        locationElement.textContent = `${cities.length} villes (${regions.join(', ')})`;
                    }
                }
                
                if (populationElement) {
                    const totalPop = locationParams.total_population || 0;
                    populationElement.textContent = `${totalPop.toLocaleString()} habitants`;
                }
                
                if (buildingsElement) {
                    buildingsElement.textContent = `${prediction.total_buildings} bâtiments`;
                }
                
                if (methodElement) {
                    methodElement.textContent = locationParams.method || 'Prédiction basée sur données Malaysia';
                }
                
                if (statusElement) {
                    const isRealData = quality.data_quality === 'OFFICIAL';
                    statusElement.textContent = isRealData ? '🎯 VRAIES DONNÉES MALAYSIA' : '📊 ESTIMATION INTELLIGENTE';
                    statusElement.className = isRealData ? 'predictor-status' : 'predictor-status estimated';
                }
            }
            
            updateDistribution(prediction) {
                const distributionContent = document.getElementById('predictorDistributionContent');
                if (!distributionContent) return;
                
                const buildingCounts = prediction.building_counts || {};
                const percentages = prediction.percentages || {};
                
                const sortedTypes = Object.entries(buildingCounts)
                    .filter(([type, count]) => count > 0)
                    .sort(([,a], [,b]) => b - a);
                
                if (sortedTypes.length === 0) {
                    distributionContent.innerHTML = '<div class="prediction-loading">Aucun bâtiment prédit</div>';
                    return;
                }
                
                let html = '';
                
                sortedTypes.forEach(([buildingType, count]) => {
                    const percentage = percentages[buildingType] || 0;
                    const isMajor = count >= prediction.total_buildings * 0.1;
                    
                    const icons = {
                        'Residential': '🏠', 'Commercial': '🏪', 'Office': '🏢',
                        'Industrial': '🏭', 'Hospital': '🏥', 'Clinic': '⚕️',
                        'School': '🏫', 'Hotel': '🏨', 'Restaurant': '🍽️',
                        'Retail': '🛍️', 'Warehouse': '📦', 'Factory': '⚙️',
                        'Apartment': '🏗️'
                    };
                    
                    html += `
                        <div class="building-prediction-item ${isMajor ? 'major' : ''}">
                            <div>
                                <strong>${icons[buildingType] || '🏗️'} ${buildingType}</strong>
                            </div>
                            <div>
                                <span class="prediction-count">${count}</span>
                                <span class="prediction-percentage">(${percentage.toFixed(1)}%)</span>
                            </div>
                        </div>
                    `;
                });
                
                distributionContent.innerHTML = html;
            }
            
            updateConfidence(quality) {
                const confidenceElement = document.getElementById('predictorConfidence');
                const confidenceTextElement = document.getElementById('predictorConfidenceText');
                
                if (confidenceElement && confidenceTextElement) {
                    const confidence = quality.overall_confidence || 0;
                    
                    confidenceElement.style.width = `${confidence}%`;
                    confidenceTextElement.textContent = `${confidence}%`;
                    
                    if (confidence >= 90) {
                        confidenceElement.style.background = 'linear-gradient(90deg, #4caf50 0%, #2e7d32 100%)';
                    } else if (confidence >= 75) {
                        confidenceElement.style.background = 'linear-gradient(90deg, #ff9800 0%, #4caf50 100%)';
                    } else {
                        confidenceElement.style.background = 'linear-gradient(90deg, #ff5722 0%, #ff9800 100%)';
                    }
                }
            }
            
            showLoading() {
                const distributionContent = document.getElementById('predictorDistributionContent');
                if (distributionContent) {
                    distributionContent.innerHTML = `
                        <div class="prediction-loading">
                            <div style="display: inline-block; animation: spin 1s linear infinite;">🔄</div>
                            Calcul de la prédiction...
                        </div>
                    `;
                }
            }
            
            showEmptyState() {
                const distributionContent = document.getElementById('predictorDistributionContent');
                if (distributionContent) {
                    distributionContent.innerHTML = `
                        <div class="prediction-loading">
                            🏗️ Spécifiez le nombre de bâtiments pour voir la prédiction
                        </div>
                    `;
                }
                
                document.getElementById('predictorLocation').textContent = 'Toute la Malaisie';
                document.getElementById('predictorPopulation').textContent = 'Population mixte';
                document.getElementById('predictorBuildings').textContent = '0 bâtiments';
                document.getElementById('predictorConfidence').style.width = '0%';
                document.getElementById('predictorConfidenceText').textContent = '0%';
            }
            
            showError(message) {
                const distributionContent = document.getElementById('predictorDistributionContent');
                if (distributionContent) {
                    distributionContent.innerHTML = `
                        <div class="prediction-error">
"""