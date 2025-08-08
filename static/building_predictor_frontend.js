/**
 * building_predictor_frontend.js
 * Prédicteur de bâtiments frontend
 * Version: 2.0 - Résolution des problèmes d'intégration
 */

class BuildingPredictorFixed {
    constructor() {
        console.log('🔮 Initialisation BuildingPredictorFixed...');
        
        // Vérification de la disponibilité des éléments DOM
        this.domReady = false;
        this.predictionPanelCreated = false;
        
        // Données de référence basées sur les vraies données Malaysia
        this.initializeReferenceData();
        
        // Attendre que le DOM soit prêt
        this.waitForDOMReady();
    }

    /**
     * Initialise les données de référence pour la prédiction
     */
    initializeReferenceData() {
        // Données réelles de référence Malaysia (basées sur real_data_integrator.py)
        this.referenceData = {
            'Kuala Lumpur': {
                population: 1800000,
                region: 'Central',
                type: 'metropolis',
                distribution: {
                    'Residential': 0.65, 'Commercial': 0.12, 'Office': 0.08,
                    'Industrial': 0.04, 'Hospital': 0.002, 'Clinic': 0.01,
                    'School': 0.025, 'Hotel': 0.025, 'Restaurant': 0.04,
                    'Retail': 0.06, 'Warehouse': 0.012, 'Apartment': 0.015
                },
                confidence: 95
            },
            'George Town': {
                population: 708000,
                region: 'Northern',
                type: 'major_city',
                distribution: {
                    'Residential': 0.70, 'Commercial': 0.14, 'Office': 0.05,
                    'Industrial': 0.04, 'Hospital': 0.001, 'Clinic': 0.006,
                    'School': 0.022, 'Hotel': 0.025, 'Restaurant': 0.028,
                    'Retail': 0.05, 'Warehouse': 0.008, 'Apartment': 0.012
                },
                confidence: 95
            },
            'Johor Bahru': {
                population: 497000,
                region: 'Southern',
                type: 'industrial_city',
                distribution: {
                    'Residential': 0.68, 'Commercial': 0.12, 'Office': 0.06,
                    'Industrial': 0.12, 'Hospital': 0.001, 'Clinic': 0.005,
                    'School': 0.018, 'Hotel': 0.012, 'Restaurant': 0.022,
                    'Retail': 0.04, 'Warehouse': 0.035, 'Factory': 0.025
                },
                confidence: 90
            },
            'Langkawi': {
                population: 65000,
                region: 'Northern',
                type: 'tourist_destination',
                distribution: {
                    'Residential': 0.60, 'Commercial': 0.15, 'Office': 0.02,
                    'Industrial': 0.01, 'Hospital': 0.0, 'Clinic': 0.005,
                    'School': 0.020, 'Hotel': 0.12, 'Restaurant': 0.15,
                    'Retail': 0.06, 'Warehouse': 0.005
                },
                confidence: 85
            }
        };

        // Ratios par défaut selon le type de ville
        this.defaultRatios = {
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
        };

        // Données des villes Malaysia
        this.malaysiaLocations = {
            'Kuala Lumpur': {population: 1800000, region: 'Central', type: 'metropolis'},
            'George Town': {population: 708000, region: 'Northern', type: 'major_city'},
            'Ipoh': {population: 657000, region: 'Northern', type: 'major_city'},
            'Shah Alam': {population: 641000, region: 'Central', type: 'major_city'},
            'Petaling Jaya': {population: 613000, region: 'Central', type: 'major_city'},
            'Johor Bahru': {population: 497000, region: 'Southern', type: 'industrial_city'},
            'Subang Jaya': {population: 469000, region: 'Central', type: 'major_city'},
            'Klang': {population: 440000, region: 'Central', type: 'medium_city'},
            'Kota Kinabalu': {population: 452000, region: 'East Malaysia', type: 'major_city'},
            'Malacca City': {population: 455000, region: 'Southern', type: 'medium_city'},
            'Alor Setar': {population: 405000, region: 'Northern', type: 'medium_city'},
            'Seremban': {population: 372000, region: 'Central', type: 'medium_city'},
            'Kuantan': {population: 366000, region: 'East Coast', type: 'medium_city'},
            'Langkawi': {population: 65000, region: 'Northern', type: 'tourist_destination'},
            'Cyberjaya': {population: 65000, region: 'Central', type: 'small_city'},
            'Putrajaya': {population: 109000, region: 'Central', type: 'small_city'},
            'Port Klang': {population: 180000, region: 'Central', type: 'industrial_city'},
            'Pasir Gudang': {population: 200000, region: 'Southern', type: 'industrial_city'}
        };

        console.log('✅ Données de référence initialisées:', Object.keys(this.referenceData).length, 'villes de référence');
    }

    /**
     * Attend que le DOM soit prêt pour l'initialisation
     */
    waitForDOMReady() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            // DOM déjà prêt, attendre que les autres scripts soient chargés
            setTimeout(() => this.initialize(), 1000);
        }
    }

    /**
     * Initialise le prédicteur une fois le DOM prêt
     */
    initialize() {
        console.log('🚀 Initialisation du prédicteur...');
        
        // Vérifier que les éléments essentiels existent
        const criticalElements = ['numBuildings', 'locationMode', 'estimationCard'];
        const missingElements = criticalElements.filter(id => !document.getElementById(id));
        
        if (missingElements.length > 0) {
            console.warn('⚠️ Éléments manquants:', missingElements);
            // Réessayer dans 2 secondes
            setTimeout(() => this.initialize(), 2000);
            return;
        }

        this.domReady = true;
        this.createPredictionPanel();
        this.setupEventListeners();
        this.addPredictionStyles();
        
        // Prédiction initiale
        setTimeout(() => this.updatePrediction(), 500);
        
        console.log('✅ BuildingPredictorFixed initialisé avec succès');
    }

    /**
     * Crée le panneau de prédiction dans l'interface
     */
    createPredictionPanel() {
        if (this.predictionPanelCreated) {
            console.log('ℹ️ Panneau de prédiction déjà créé');
            return;
        }

        const estimationCard = document.getElementById('estimationCard');
        if (!estimationCard) {
            console.error('❌ Impossible de trouver estimationCard');
            return;
        }

        const predictionHTML = `
            <div class="prediction-panel-fixed" id="buildingPredictionPanelFixed">
                <h3>🔮 Prédiction Distribution des Bâtiments</h3>
                
                <div class="prediction-mode-indicator-fixed" id="predictionModeIndicatorFixed">
                    <span class="mode-badge-fixed">📊 ESTIMATION</span>
                    <small>Basé sur vraies données Malaysia</small>
                </div>
                
                <div class="prediction-summary-fixed" id="predictionSummaryFixed">
                    <div class="summary-item-fixed">
                        <span class="summary-label-fixed">🏙️ Zone analysée:</span>
                        <span class="summary-value-fixed" id="predictedLocationFixed">Toute la Malaisie</span>
                    </div>
                    <div class="summary-item-fixed">
                        <span class="summary-label-fixed">👥 Population:</span>
                        <span class="summary-value-fixed" id="predictedPopulationFixed">Mixte</span>
                    </div>
                    <div class="summary-item-fixed">
                        <span class="summary-label-fixed">🎯 Confiance:</span>
                        <span class="summary-value-fixed" id="confidenceValueFixed">85%</span>
                    </div>
                </div>

                <div class="prediction-distribution-fixed" id="predictionDistributionFixed">
                    <div class="loading-prediction">
                        <p>🔄 Calcul de la prédiction...</p>
                    </div>
                </div>

                <div class="prediction-notes-fixed" id="predictionNotesFixed">
                    <small>💡 La prédiction s'adapte automatiquement selon votre sélection géographique</small>
                </div>
            </div>
        `;

        // Insérer après la carte d'estimation
        estimationCard.insertAdjacentHTML('afterend', predictionHTML);
        this.predictionPanelCreated = true;
        
        console.log('✅ Panneau de prédiction créé');
    }

    /**
     * Ajoute les styles CSS pour le prédicteur
     */
    addPredictionStyles() {
        if (document.getElementById('predictionStylesFixed')) {
            return; // Styles déjà ajoutés
        }

        const styles = `
            <style id="predictionStylesFixed">
            .prediction-panel-fixed {
                background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
                border: 2px solid #4caf50;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 8px 25px rgba(76, 175, 80, 0.2);
                transition: all 0.3s ease;
            }

            .prediction-panel-fixed:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 35px rgba(76, 175, 80, 0.3);
            }

            .prediction-panel-fixed h3 {
                color: #2e7d32;
                margin-bottom: 18px;
                text-align: center;
                font-size: 1.2em;
                font-weight: 600;
            }

            .prediction-mode-indicator-fixed {
                text-align: center;
                margin-bottom: 15px;
            }

            .mode-badge-fixed {
                background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
                color: white;
                padding: 5px 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 0.85em;
                display: inline-block;
            }

            .mode-badge-fixed.real-data {
                background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
            }

            .prediction-summary-fixed {
                display: grid;
                grid-template-columns: 1fr;
                gap: 8px;
                margin-bottom: 15px;
                background: white;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #c8e6c9;
            }

            .summary-item-fixed {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 3px 0;
                font-size: 0.9em;
            }

            .summary-label-fixed {
                font-weight: 600;
                color: #1b5e20;
            }

            .summary-value-fixed {
                font-weight: bold;
                color: #2e7d32;
            }

            .prediction-distribution-fixed {
                background: white;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
                border: 1px solid #c8e6c9;
                max-height: 250px;
                overflow-y: auto;
            }

            .loading-prediction {
                text-align: center;
                padding: 15px;
                color: #666;
                font-style: italic;
            }

            .building-type-prediction-fixed {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 6px 10px;
                margin: 3px 0;
                background: #fafafa;
                border-radius: 6px;
                border-left: 3px solid #4caf50;
                transition: all 0.2s ease;
                font-size: 0.9em;
            }

            .building-type-prediction-fixed:hover {
                background: #f0f0f0;
                transform: translateX(2px);
            }

            .building-type-prediction-fixed.major {
                border-left-color: #2e7d32;
                font-weight: 600;
                background: #e8f5e8;
            }

            .building-type-prediction-fixed.minor {
                border-left-color: #9e9e9e;
                opacity: 0.8;
            }

            .type-name-fixed {
                font-weight: 500;
                color: #424242;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .type-prediction-fixed {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .type-count-fixed {
                background: #4caf50;
                color: white;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 28px;
                text-align: center;
                font-size: 0.85em;
            }

            .type-percentage-fixed {
                color: #666;
                font-size: 0.8em;
            }

            .prediction-notes-fixed {
                text-align: center;
                color: #666;
                font-style: italic;
                margin-top: 10px;
            }

            .prediction-notes-fixed small {
                font-size: 0.8em;
            }

            /* Animation d'entrée */
            .prediction-panel-fixed {
                animation: slideInUp 0.5s ease-out;
            }

            @keyframes slideInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            /* Responsive */
            @media (max-width: 768px) {
                .prediction-panel-fixed {
                    padding: 15px;
                    margin: 15px 0;
                }
                
                .prediction-summary-fixed {
                    padding: 10px;
                }
                
                .building-type-prediction-fixed {
                    padding: 5px 8px;
                }
                
                .summary-item-fixed {
                    font-size: 0.85em;
                }
            }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
        console.log('✅ Styles CSS ajoutés');
    }

    /**
     * Configure les écouteurs d'événements
     */
    setupEventListeners() {
        // Éléments à surveiller pour déclencher la prédiction
        const watchedElements = [
            'numBuildings', 'locationMode', 'filterRegion', 'filterState', 
            'filterCity', 'populationRange', 'popMin', 'popMax',
            'customCity', 'customState', 'customRegion', 'customPopulation'
        ];

        let updateTimeout;

        watchedElements.forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                // Utiliser un debounce pour éviter trop d'appels
                const debouncedUpdate = () => {
                    clearTimeout(updateTimeout);
                    updateTimeout = setTimeout(() => this.updatePrediction(), 300);
                };

                element.addEventListener('change', debouncedUpdate);
                element.addEventListener('input', debouncedUpdate);
            }
        });

        console.log('✅ Écouteurs d\'événements configurés sur', watchedElements.length, 'éléments');
    }

    /**
     * Met à jour la prédiction
     */
    updatePrediction() {
        if (!this.domReady || !this.predictionPanelCreated) {
            console.log('⏳ Prédicteur pas encore prêt');
            return;
        }

        try {
            const numBuildings = parseInt(document.getElementById('numBuildings')?.value) || 0;
            
            if (numBuildings <= 0) {
                this.showEmptyPrediction();
                return;
            }

            // Obtenir les paramètres de localisation
            const locationParams = this.getLocationParameters();
            
            // Calculer la prédiction
            const prediction = this.calculatePrediction(numBuildings, locationParams);
            
            // Afficher les résultats
            this.displayPrediction(prediction, locationParams);
            
            console.log('🔮 Prédiction mise à jour:', {
                buildings: numBuildings,
                locations: locationParams.cities?.length || 'all',
                confidence: prediction.confidence
            });
            
        } catch (error) {
            console.error('❌ Erreur lors de la mise à jour de la prédiction:', error);
            this.showErrorPrediction(error.message);
        }
    }

    /**
     * Obtient les paramètres de localisation selon la sélection
     */
    getLocationParameters() {
        const locationMode = document.getElementById('locationMode')?.value || 'all';
        
        switch (locationMode) {
            case 'custom':
                return this.getCustomLocationParams();
            case 'filter':
                return this.getFilteredLocationParams();
            default:
                return this.getAllMalaysiaParams();
        }
    }

    /**
     * Paramètres pour localisation personnalisée
     */
    getCustomLocationParams() {
        const customCity = document.getElementById('customCity')?.value?.trim();
        const customPopulation = parseInt(document.getElementById('customPopulation')?.value) || 100000;
        const customRegion = document.getElementById('customRegion')?.value || 'Central';
        
        if (!customCity) {
            return this.getAllMalaysiaParams();
        }

        const cityType = this.determineCityType(customPopulation);
        
        return {
            mode: 'custom',
            cities: [{
                name: customCity,
                population: customPopulation,
                region: customRegion,
                type: cityType
            }],
            confidence: 65, // Moins de confiance pour villes personnalisées
            method: 'Estimation basée sur population'
        };
    }

    /**
     * Paramètres pour localisation filtrée
     */
    getFilteredLocationParams() {
        const region = document.getElementById('filterRegion')?.value;
        const state = document.getElementById('filterState')?.value;
        const city = document.getElementById('filterCity')?.value;
        const popMin = parseInt(document.getElementById('popMin')?.value) || 0;
        const popMax = parseInt(document.getElementById('popMax')?.value) || Infinity;

        // Filtrer les villes selon les critères
        let filteredCities = Object.entries(this.malaysiaLocations).filter(([name, info]) => {
            if (region && region !== 'all' && info.region !== region) return false;
            if (city && city !== 'all' && name !== city) return false;
            if (info.population < popMin || info.population > popMax) return false;
            return true;
        });

        if (filteredCities.length === 0) {
            return this.getAllMalaysiaParams();
        }

        const cities = filteredCities.map(([name, info]) => ({
            name: name,
            population: info.population,
            region: info.region,
            type: info.type
        }));

        return {
            mode: 'filtered',
            cities: cities,
            confidence: 90, // Haute confiance pour villes réelles
            method: 'Vraies données Malaysia'
        };
    }

    /**
     * Paramètres pour toute la Malaisie
     */
    getAllMalaysiaParams() {
        const cities = Object.entries(this.malaysiaLocations).map(([name, info]) => ({
            name: name,
            population: info.population,
            region: info.region,
            type: info.type
        }));

        return {
            mode: 'all',
            cities: cities,
            confidence: 95, // Très haute confiance
            method: 'Distribution Malaysia complète'
        };
    }

    /**
     * Détermine le type de ville selon la population
     */
    determineCityType(population) {
        if (population > 1000000) return 'metropolis';
        if (population > 500000) return 'major_city';
        if (population > 200000) return 'medium_city';
        if (population > 50000) return 'small_city';
        return 'small_city';
    }

    /**
     * Calcule la prédiction de distribution
     */
    calculatePrediction(numBuildings, locationParams) {
        const { cities, confidence, method } = locationParams;
        
        // Distribution pondérée selon les villes
        let combinedDistribution = {};
        let totalPopulation = 0;
        let totalWeight = 0;

        // Calculer les poids et la distribution combinée
        for (const city of cities) {
            const weight = city.population;
            totalWeight += weight;
            totalPopulation += city.population;
            
            // Obtenir la distribution pour cette ville
            const cityDistribution = this.getCityDistribution(city);
            
            // Ajouter avec pondération
            for (const [buildingType, percentage] of Object.entries(cityDistribution)) {
                if (!combinedDistribution[buildingType]) {
                    combinedDistribution[buildingType] = 0;
                }
                combinedDistribution[buildingType] += percentage * weight;
            }
        }
        
        // Normaliser la distribution
        for (const buildingType in combinedDistribution) {
            combinedDistribution[buildingType] /= totalWeight;
        }
        
        // Convertir en nombres de bâtiments
        const buildingCounts = this.distributeBuildingsFromPercentages(combinedDistribution, numBuildings);
        
        return {
            distribution: buildingCounts,
            percentages: combinedDistribution,
            confidence: confidence,
            method: method,
            summary: {
                totalBuildings: numBuildings,
                citiesCount: cities.length,
                averagePopulation: Math.round(totalPopulation / cities.length),
                regions: [...new Set(cities.map(c => c.region))]
            }
        };
    }

    /**
     * Obtient la distribution pour une ville donnée
     */
    getCityDistribution(city) {
        // Utiliser les vraies données si disponibles
        if (this.referenceData[city.name]) {
            return this.referenceData[city.name].distribution;
        }
        
        // Utiliser les ratios par défaut selon le type de ville
        return this.defaultRatios[city.type] || this.defaultRatios['medium_city'];
    }

    /**
     * Distribue les bâtiments selon les pourcentages
     */
    distributeBuildingsFromPercentages(percentages, totalBuildings) {
        const buildingCounts = {};
        let assignedBuildings = 0;
        
        // Trier par pourcentage décroissant
        const sortedTypes = Object.entries(percentages)
            .sort(([,a], [,b]) => b - a);
        
        // Assigner les bâtiments
        for (let i = 0; i < sortedTypes.length - 1; i++) {
            const [buildingType, percentage] = sortedTypes[i];
            const count = Math.round(percentage * totalBuildings);
            buildingCounts[buildingType] = count;
            assignedBuildings += count;
        }
        
        // Le dernier type récupère le reste pour avoir le total exact
        if (sortedTypes.length > 0) {
            const [lastType] = sortedTypes[sortedTypes.length - 1];
            buildingCounts[lastType] = totalBuildings - assignedBuildings;
        }
        
        // S'assurer qu'aucune valeur n'est négative
        for (const type in buildingCounts) {
            if (buildingCounts[type] < 0) {
                buildingCounts[type] = 0;
            }
        }
        
        return buildingCounts;
    }

    /**
     * Affiche la prédiction dans l'interface
     */
    displayPrediction(prediction, locationParams) {
        this.updatePredictionSummary(prediction, locationParams);
        this.updatePredictionDistribution(prediction);
        this.updatePredictionMode(prediction, locationParams);
    }

    /**
     * Met à jour le résumé de la prédiction
     */
    updatePredictionSummary(prediction, locationParams) {
        const locationElement = document.getElementById('predictedLocationFixed');
        const populationElement = document.getElementById('predictedPopulationFixed');
        const confidenceElement = document.getElementById('confidenceValueFixed');
        
        if (locationElement) {
            const { cities } = locationParams;
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
            if (locationParams.cities.length === 1) {
                populationElement.textContent = `${locationParams.cities[0].population.toLocaleString()} hab.`;
            } else {
                populationElement.textContent = `${prediction.summary.averagePopulation.toLocaleString()} hab. (moy.)`;
            }
        }
        
        if (confidenceElement) {
            confidenceElement.textContent = `${prediction.confidence}%`;
        }
    }

    /**
     * Met à jour l'affichage de la distribution
     */
    updatePredictionDistribution(prediction) {
        const distributionElement = document.getElementById('predictionDistributionFixed');
        if (!distributionElement) return;
        
        const { distribution } = prediction;
        
        // Filtrer et trier les types de bâtiments par nombre décroissant
        const sortedTypes = Object.entries(distribution)
            .filter(([type, count]) => count > 0)
            .sort(([,a], [,b]) => b - a);
        
        if (sortedTypes.length === 0) {
            distributionElement.innerHTML = '<div class="loading-prediction"><p>❌ Aucun bâtiment prédit</p></div>';
            return;
        }
        
        let distributionHTML = '';
        
        // Icônes pour chaque type de bâtiment
        const buildingIcons = {
            'Residential': '🏠', 'Commercial': '🏪', 'Office': '🏢',
            'Industrial': '🏭', 'Hospital': '🏥', 'Clinic': '⚕️',
            'School': '🏫', 'Hotel': '🏨', 'Restaurant': '🍽️',
            'Retail': '🛍️', 'Warehouse': '📦', 'Factory': '⚙️',
            'Apartment': '🏗️'
        };
        
        sortedTypes.forEach(([buildingType, count]) => {
            const percentage = ((count / prediction.summary.totalBuildings) * 100).toFixed(1);
            const icon = buildingIcons[buildingType] || '🏗️';
            
            // Déterminer la classe selon l'importance
            let typeClass = '';
            if (buildingType === 'Residential' || count >= prediction.summary.totalBuildings * 0.1) {
                typeClass = 'major'; // Types principaux
            } else if (count < prediction.summary.totalBuildings * 0.03) {
                typeClass = 'minor'; // Types secondaires
            }
            
            distributionHTML += `
                <div class="building-type-prediction-fixed ${typeClass}">
                    <div class="type-name-fixed">
                        <span>${icon}</span>
                        <span>${buildingType}</span>
                    </div>
                    <div class="type-prediction-fixed">
                        <span class="type-count-fixed">${count}</span>
                        <span class="type-percentage-fixed">(${percentage}%)</span>
                    </div>
                </div>
            `;
        });
        
        distributionElement.innerHTML = distributionHTML;
    }

    /**
     * Met à jour l'indicateur de mode
     */
    updatePredictionMode(prediction, locationParams) {
        const modeIndicator = document.getElementById('predictionModeIndicatorFixed');
        if (!modeIndicator) return;
        
        // Vérifier si on utilise des vraies données
        const hasRealData = locationParams.cities.some(city => this.referenceData[city.name]);
        
        if (hasRealData) {
            modeIndicator.innerHTML = `
                <span class="mode-badge-fixed real-data">🎯 VRAIES DONNÉES</span>
                <small>Basé sur sources officielles Malaysia</small>
            `;
        } else {
            modeIndicator.innerHTML = `
                <span class="mode-badge-fixed">📊 ESTIMATION</span>
                <small>Ratios intelligents selon type de ville</small>
            `;
        }
    }

    /**
     * Affiche un état vide
     */
    showEmptyPrediction() {
        const distributionElement = document.getElementById('predictionDistributionFixed');
        if (distributionElement) {
            distributionElement.innerHTML = `
                <div class="loading-prediction">
                    <p>🏗️ Spécifiez le nombre de bâtiments pour voir la prédiction</p>
                </div>
            `;
        }
    }

    /**
     * Affiche une erreur
     */
    showErrorPrediction(errorMessage) {
        const distributionElement = document.getElementById('predictionDistributionFixed');
        if (distributionElement) {
            distributionElement.innerHTML = `
                <div class="loading-prediction">
                    <p>❌ Erreur: ${errorMessage}</p>
                </div>
            `;
        }
    }

    /**
     * API publique pour obtenir la prédiction actuelle
     */
    getCurrentPrediction() {
        const numBuildings = parseInt(document.getElementById('numBuildings')?.value) || 0;
        if (numBuildings <= 0) return null;
        
        try {
            const locationParams = this.getLocationParameters();
            return this.calculatePrediction(numBuildings, locationParams);
        } catch (error) {
            console.error('Erreur getCurrentPrediction:', error);
            return null;
        }
    }

    /**
     * Force une mise à jour de la prédiction
     */
    forceUpdate() {
        this.updatePrediction();
    }

    /**
     * Obtient les données de référence (pour débogage)
     */
    getReferenceData() {
        return {
            referenceData: this.referenceData,
            defaultRatios: this.defaultRatios,
            malaysiaLocations: this.malaysiaLocations
        };
    }

    /**
     * Calcule une prédiction personnalisée
     */
    customPrediction(numBuildings, cityName, population = null) {
        if (numBuildings <= 0) return null;
        
        let cityInfo;
        if (this.malaysiaLocations[cityName]) {
            cityInfo = this.malaysiaLocations[cityName];
        } else if (population) {
            cityInfo = {
                population: population,
                region: 'Custom',
                type: this.determineCityType(population)
            };
        } else {
            return null;
        }
        
        const locationParams = {
            mode: 'custom',
            cities: [{
                name: cityName,
                population: cityInfo.population,
                region: cityInfo.region,
                type: cityInfo.type
            }],
            confidence: this.malaysiaLocations[cityName] ? 90 : 70,
            method: this.malaysiaLocations[cityName] ? 'Vraies données' : 'Estimation'
        };
        
        return this.calculatePrediction(numBuildings, locationParams);
    }
}

// ===================================================================
// INITIALISATION ET INTÉGRATION GLOBALE
// ===================================================================

/**
 * Instance globale du prédicteur
 */
let buildingPredictorFixed = null;

/**
 * Fonctions d'intégration avec le script principal
 */
function integrateWithMainScript() {
    console.log('🔗 Intégration avec le script principal...');
    
    // Sauvegarder les fonctions originales si elles existent
    const originalFunctions = {
        updateEstimation: window.updateEstimation,
        toggleLocationMode: window.toggleLocationMode,
        updateStateOptions: window.updateStateOptions,
        updateCityOptions: window.updateCityOptions,
        updatePopulationInputs: window.updatePopulationInputs
    };
    
    // Fonction d'update avec prédiction
    function updateWithPrediction(originalFunc, delay = 200) {
        return function(...args) {
            // Appeler la fonction originale
            if (originalFunc) {
                originalFunc.apply(this, args);
            }
            
            // Mettre à jour la prédiction avec un délai
            setTimeout(() => {
                if (buildingPredictorFixed) {
                    buildingPredictorFixed.updatePrediction();
                }
            }, delay);
        };
    }
    
    // Override des fonctions si elles existent
    if (originalFunctions.updateEstimation) {
        window.updateEstimation = updateWithPrediction(originalFunctions.updateEstimation, 100);
    }
    
    if (originalFunctions.toggleLocationMode) {
        window.toggleLocationMode = updateWithPrediction(originalFunctions.toggleLocationMode, 300);
    }
    
    if (originalFunctions.updateStateOptions) {
        window.updateStateOptions = updateWithPrediction(originalFunctions.updateStateOptions, 200);
    }
    
    if (originalFunctions.updateCityOptions) {
        window.updateCityOptions = updateWithPrediction(originalFunctions.updateCityOptions, 200);
    }
    
    if (originalFunctions.updatePopulationInputs) {
        window.updatePopulationInputs = updateWithPrediction(originalFunctions.updatePopulationInputs, 200);
    }
    
    console.log('✅ Intégration terminée');
}

/**
 * API publique pour le prédicteur
 */
window.BuildingPredictorAPI = {
    /**
     * Obtient la prédiction actuelle
     */
    getCurrentPrediction: function() {
        return buildingPredictorFixed ? buildingPredictorFixed.getCurrentPrediction() : null;
    },
    
    /**
     * Force une mise à jour
     */
    forceUpdate: function() {
        if (buildingPredictorFixed) {
            buildingPredictorFixed.forceUpdate();
        }
    },
    
    /**
     * Obtient les données de référence
     */
    getReferenceData: function() {
        return buildingPredictorFixed ? buildingPredictorFixed.getReferenceData() : null;
    },
    
    /**
     * Calcul d'une prédiction personnalisée
     */
    customPrediction: function(numBuildings, cityName, population = null) {
        return buildingPredictorFixed ? 
            buildingPredictorFixed.customPrediction(numBuildings, cityName, population) : null;
    },
    
    /**
     * Vérifie si le prédicteur est prêt
     */
    isReady: function() {
        return buildingPredictorFixed !== null && buildingPredictorFixed.domReady;
    },
    
    /**
     * Obtient les statistiques sur les villes de référence
     */
    getStats: function() {
        if (!buildingPredictorFixed) return null;
        
        const data = buildingPredictorFixed.getReferenceData();
        return {
            totalCities: Object.keys(data.malaysiaLocations).length,
            citiesWithRealData: Object.keys(data.referenceData).length,
            cityTypes: Object.keys(data.defaultRatios),
            regions: [...new Set(Object.values(data.malaysiaLocations).map(c => c.region))]
        };
    }
};

/**
 * Initialisation principale
 */
function initializeBuildingPredictor() {
    console.log('🔮 Démarrage de l\'initialisation du prédicteur...');
    
    try {
        buildingPredictorFixed = new BuildingPredictorFixed();
        
        // Attendre l'initialisation complète
        const checkInitialization = setInterval(() => {
            if (buildingPredictorFixed && buildingPredictorFixed.domReady) {
                clearInterval(checkInitialization);
                
                // Intégrer avec le script principal
                setTimeout(() => {
                    integrateWithMainScript();
                }, 1000);
                
                // Exposer globalement pour débogage
                window.buildingPredictorFixed = buildingPredictorFixed;
                
                console.log('✅ BuildingPredictorFixed complètement initialisé et intégré');
            }
        }, 500);
        
        // Timeout de sécurité
        setTimeout(() => {
            if (checkInitialization) {
                clearInterval(checkInitialization);
                console.warn('⚠️ Timeout d\'initialisation du prédicteur');
            }
        }, 10000);
        
    } catch (error) {
        console.error('❌ Erreur lors de l\'initialisation du prédicteur:', error);
    }
}

/**
 * Point d'entrée principal
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeBuildingPredictor);
} else {
    // DOM déjà chargé
    setTimeout(initializeBuildingPredictor, 500);
}

// ===================================================================
// FONCTIONS UTILITAIRES ET DÉBOGAGE
// ===================================================================

/**
 * Fonction de diagnostic
 */
window.diagnosticPredictor = function() {
    console.log('\n🔍 DIAGNOSTIC BUILDING PREDICTOR');
    console.log('=====================================');
    
    console.log('État:', {
        predictorExists: !!buildingPredictorFixed,
        isReady: buildingPredictorFixed?.domReady || false,
        panelCreated: buildingPredictorFixed?.predictionPanelCreated || false
    });
    
    console.log('Éléments DOM critiques:');
    const criticalElements = [
        'numBuildings', 'locationMode', 'estimationCard', 
        'buildingPredictionPanelFixed', 'predictionDistributionFixed'
    ];
    
    criticalElements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`  ${id}: ${element ? '✅' : '❌'}`);
    });
    
    if (buildingPredictorFixed) {
        const stats = window.BuildingPredictorAPI.getStats();
        console.log('Statistiques:', stats);
        
        const currentPrediction = window.BuildingPredictorAPI.getCurrentPrediction();
        console.log('Prédiction actuelle:', currentPrediction ? 
            `${currentPrediction.summary.totalBuildings} bâtiments, ${currentPrediction.confidence}% confiance` : 
            'Aucune'
        );
    }
};

/**
 * Fonction de test rapide
 */
window.testPredictor = function() {
    console.log('🧪 Test rapide du prédicteur...');
    
    if (!buildingPredictorFixed) {
        console.error('❌ Prédicteur non initialisé');
        return;
    }
    
    // Test avec Kuala Lumpur
    const prediction = window.BuildingPredictorAPI.customPrediction(100, 'Kuala Lumpur');
    console.log('Test Kuala Lumpur (100 bâtiments):', prediction);
    
    // Test avec ville personnalisée
    const customPrediction = window.BuildingPredictorAPI.customPrediction(50, 'Test City', 300000);
    console.log('Test ville personnalisée (50 bâtiments, 300K hab.):', customPrediction);
    
    console.log('✅ Tests terminés');
};

// Message de chargement
console.log(`
🔮 BUILDING PREDICTOR FRONTEND - VERSION CORRIGÉE
================================================
✅ Prédiction intelligente basée sur vraies données Malaysia
🏗️ Distribution réaliste selon types de villes
🎯 Intégration automatique avec l'interface existante
🔧 API complète pour intégration personnalisée

APIs disponibles:
- window.BuildingPredictorAPI.getCurrentPrediction()
- window.BuildingPredictorAPI.forceUpdate()
- window.BuildingPredictorAPI.customPrediction(buildings, city, population)
- window.diagnosticPredictor()
- window.testPredictor()

Prêt à l'initialisation! 🚀
`);