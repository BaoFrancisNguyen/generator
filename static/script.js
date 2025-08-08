// script.js - Version corrigée pour le générateur de données électriques Malaysia
// Corrige les problèmes d'affichage des résultats

// Variables globales
let malaysiaData = {};
let systemCapabilities = {};

// Charger les données au démarrage
window.onload = function() {
    console.log('🚀 Initialisation de l\'application Malaysia...');
    loadMalaysiaData();
    loadSystemStatus();
    updateEstimation();
};

// ==================== CHARGEMENT DES DONNÉES ====================

async function loadMalaysiaData() {
    try {
        console.log('🇲🇾 Chargement des données Malaysia...');
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success && data.malaysia_locations) {
            malaysiaData = data.malaysia_locations;
            populateFilterOptions();
            console.log(`✅ ${Object.keys(malaysiaData).length} villes chargées`);
        } else {
            console.warn('⚠️ Erreur API stats, utilisation données de base');
            useFallbackData();
        }
    } catch (error) {
        console.error('❌ Erreur chargement Malaysia data:', error);
        useFallbackData();
    }
}

function useFallbackData() {
    malaysiaData = {
        'Kuala Lumpur': {'population': 1800000, 'state': 'Federal Territory', 'region': 'Central'},
        'George Town': {'population': 708000, 'state': 'Penang', 'region': 'Northern'},
        'Johor Bahru': {'population': 497000, 'state': 'Johor', 'region': 'Southern'},
        'Ipoh': {'population': 657000, 'state': 'Perak', 'region': 'Northern'},
        'Shah Alam': {'population': 641000, 'state': 'Selangor', 'region': 'Central'}
    };
    populateFilterOptions();
    console.log('⚠️ Utilisation données de fallback');
}

async function loadSystemStatus() {
    try {
        const response = await fetch('/api/real-data-status');
        const data = await response.json();
        
        if (data.success && data.status) {
            systemCapabilities = data.status;
            updateSystemStatusUI(data.status);
        } else {
            setDefaultCapabilities();
        }
    } catch (error) {
        console.warn('⚠️ Impossible de charger le statut système:', error);
        setDefaultCapabilities();
    }
}

function setDefaultCapabilities() {
    systemCapabilities = {
        real_data_available: false,
        validation_enabled: false,
        building_distributor_available: false
    };
    updateSystemStatusUI(systemCapabilities);
}

// ==================== MISE À JOUR UI ====================

function updateSystemStatusUI(status) {
    console.log('🎨 Mise à jour UI avec statut:', status);
    
    const statusIndicator = document.getElementById('dataStatusIndicator');
    if (statusIndicator) {
        if (status.real_data_available) {
            statusIndicator.innerHTML = `
                <div class="real-data-indicator">
                    🎯 VRAIES DONNÉES OFFICIELLES MALAYSIA ACTIVÉES
                    <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">
                        Sources: Ministry of Health, Education, Tourism Malaysia
                    </div>
                </div>
            `;
        } else {
            statusIndicator.innerHTML = `
                <div class="estimation-indicator">
                    📊 MODE ESTIMATION - Distribution intelligente selon villes
                    <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">
                        Basé sur population et caractéristiques urbaines
                    </div>
                </div>
            `;
        }
    }
}

// ==================== FONCTIONS DE FILTRAGE ====================

function populateFilterOptions() {
    const regionSelect = document.getElementById('filterRegion');
    if (!regionSelect || !malaysiaData) return;
    
    try {
        const regions = [...new Set(Object.values(malaysiaData).map(loc => loc.region))];
        regionSelect.innerHTML = '<option value="all">Toutes les régions</option>';
        
        regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region;
            option.textContent = region;
            regionSelect.appendChild(option);
        });
        
        console.log(`✅ ${regions.length} régions ajoutées`);
    } catch (error) {
        console.error('❌ Erreur peuplement filtres:', error);
    }
}

function toggleLocationMode() {
    const mode = document.getElementById('locationMode')?.value;
    const filterSection = document.getElementById('filterSection');
    const customSection = document.getElementById('customSection');
    
    if (filterSection) filterSection.style.display = mode === 'filter' ? 'block' : 'none';
    if (customSection) customSection.style.display = mode === 'custom' ? 'block' : 'none';
}

function updateStateOptions() {
    const selectedRegion = document.getElementById('filterRegion')?.value;
    const stateSelect = document.getElementById('filterState');
    const citySelect = document.getElementById('filterCity');
    
    if (!stateSelect || !citySelect || !malaysiaData) return;
    
    stateSelect.innerHTML = '<option value="all">Tous les états</option>';
    citySelect.innerHTML = '<option value="all">Toutes les villes</option>';
    
    try {
        let states;
        if (selectedRegion === 'all') {
            states = [...new Set(Object.values(malaysiaData).map(loc => loc.state))];
        } else {
            states = [...new Set(
                Object.values(malaysiaData)
                    .filter(loc => loc.region === selectedRegion)
                    .map(loc => loc.state)
            )];
        }
        
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
    } catch (error) {
        console.error('❌ Erreur mise à jour états:', error);
    }
}

function updateCityOptions() {
    const selectedRegion = document.getElementById('filterRegion')?.value;
    const selectedState = document.getElementById('filterState')?.value;
    const citySelect = document.getElementById('filterCity');
    
    if (!citySelect || !malaysiaData) return;
    
    citySelect.innerHTML = '<option value="all">Toutes les villes</option>';
    
    try {
        let filteredCities = Object.entries(malaysiaData);
        
        if (selectedRegion !== 'all') {
            filteredCities = filteredCities.filter(([name, info]) => info.region === selectedRegion);
        }
        
        if (selectedState !== 'all') {
            filteredCities = filteredCities.filter(([name, info]) => info.state === selectedState);
        }
        
        filteredCities
            .sort((a, b) => b[1].population - a[1].population)
            .forEach(([name, info]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${name} (${info.population.toLocaleString()} hab.)`;
                citySelect.appendChild(option);
            });
    } catch (error) {
        console.error('❌ Erreur mise à jour villes:', error);
    }
}

function updatePopulationInputs() {
    const range = document.getElementById('populationRange')?.value;
    const customRange = document.getElementById('customPopulationRange');
    const popMin = document.getElementById('popMin');
    const popMax = document.getElementById('popMax');
    
    if (customRange) {
        customRange.style.display = range === 'custom' ? 'block' : 'none';
    }
    
    if (popMin && popMax) {
        switch(range) {
            case 'large':
                popMin.value = 500000;
                popMax.value = '';
                break;
            case 'medium':
                popMin.value = 200000;
                popMax.value = 500000;
                break;
            case 'small':
                popMin.value = '';
                popMax.value = 200000;
                break;
            default:
                if (range !== 'custom') {
                    popMin.value = '';
                    popMax.value = '';
                }
        }
    }
}

// ==================== ESTIMATION ====================

function updateEstimation() {
    const numBuildings = parseInt(document.getElementById('numBuildings')?.value) || 0;
    const startDate = document.getElementById('startDate')?.value;
    const endDate = document.getElementById('endDate')?.value;
    const freq = document.getElementById('freq')?.value;
    
    if (numBuildings === 0 || !startDate || !endDate) {
        return;
    }
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    let observationsPerBuilding;
    let freqDescription;
    
    switch(freq) {
        case '5T':
            observationsPerBuilding = diffDays * 288;
            freqDescription = "Très haute résolution";
            break;
        case '15T':
            observationsPerBuilding = diffDays * 96;
            freqDescription = "Haute résolution";
            break;
        case '30T':
            observationsPerBuilding = diffDays * 48;
            freqDescription = "Résolution standard";
            break;
        case '1H':
            observationsPerBuilding = diffDays * 24;
            freqDescription = "Résolution horaire";
            break;
        case '2H':
            observationsPerBuilding = diffDays * 12;
            freqDescription = "Résolution bi-horaire";
            break;
        case '6H':
            observationsPerBuilding = diffDays * 4;
            freqDescription = "4 fois par jour";
            break;
        case '12H':
            observationsPerBuilding = diffDays * 2;
            freqDescription = "2 fois par jour";
            break;
        case '1D':
            observationsPerBuilding = diffDays * 1;
            freqDescription = "Quotidien";
            break;
        case '1W':
            observationsPerBuilding = Math.ceil(diffDays / 7);
            freqDescription = "Hebdomadaire";
            break;
        case '1M':
            observationsPerBuilding = Math.ceil(diffDays / 30);
            freqDescription = "Mensuel";
            break;
        default:
            observationsPerBuilding = diffDays * 48;
            freqDescription = "Résolution par défaut";
    }
    
    const totalObservations = numBuildings * observationsPerBuilding;
    const bytesPerObservation = 80;
    const fileSizeMB = (totalObservations * bytesPerObservation) / (1024 * 1024);
    
    let generationTimeEstimate;
    if (totalObservations < 10000) {
        generationTimeEstimate = "< 10 secondes";
    } else if (totalObservations < 100000) {
        generationTimeEstimate = "10-30 secondes";
    } else if (totalObservations < 500000) {
        generationTimeEstimate = "30 sec - 2 min";
    } else if (totalObservations < 1000000) {
        generationTimeEstimate = "2-5 minutes";
    } else {
        generationTimeEstimate = "5+ minutes";
    }
    
    let useCase;
    if (totalObservations < 50000) {
        useCase = "🧪 Test/Développement";
    } else if (totalObservations < 500000) {
        useCase = "📚 Recherche";
    } else if (totalObservations < 2000000) {
        useCase = "🤖 Machine Learning";
    } else {
        useCase = "🏭 Production";
    }
    
    // Mise à jour de l'interface
    const updates = {
        'totalObservations': totalObservations.toLocaleString(),
        'fileSize': fileSizeMB > 1 ? `${Math.round(fileSizeMB)} MB` : `${Math.round(fileSizeMB * 1024)} KB`,
        'generationTime': generationTimeEstimate,
        'useCase': useCase,
        'freqInfo': freqDescription
    };
    
    Object.entries(updates).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

// ==================== FONCTIONS PRINCIPALES - VERSION CORRIGÉE ====================

async function generateData() {
    console.log('🚀 Début génération...');
    
    try {
        showLoading(true);
        hideResults();
        
        const params = getFormParams();
        if (!params) {
            console.error('❌ Paramètres invalides');
            showLoading(false);
            return;
        }
        
        console.log('📤 Envoi requête:', params);
        
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        console.log('📥 Réponse reçue, status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('✅ Données parsées:', data);
        
        showLoading(false);
        
        if (data.success) {
            showResults(data);
            console.log('🎉 Génération réussie!');
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
        
    } catch (error) {
        console.error('❌ Erreur génération:', error);
        showLoading(false);
        showError(`Erreur de génération: ${error.message}`);
    }
}

async function downloadData() {
    console.log('💾 Début téléchargement...');
    
    try {
        showLoading(true);
        
        const params = getFormParams();
        if (!params) {
            showLoading(false);
            return;
        }
        
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        showLoading(false);
        
        if (data.success) {
            showSuccess(`✅ Fichiers générés avec succès!\n${data.message}`);
            
            if (data.data_sources) {
                showDataQualityInfo(data.data_sources);
            }
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('❌ Erreur téléchargement:', error);
        showLoading(false);
        showError(`Erreur: ${error.message}`);
    }
}

async function showSample() {
    console.log('👁️ Génération échantillon...');
    
    try {
        showLoading(true);
        
        const response = await fetch('/sample');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        showLoading(false);
        
        if (data.success) {
            showResults(data, true);
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('❌ Erreur échantillon:', error);
        showLoading(false);
        showError(`Erreur: ${error.message}`);
    }
}

// ==================== GESTION DES PARAMÈTRES ====================

function getFormParams() {
    try {
        const numBuildings = parseInt(document.getElementById('numBuildings')?.value);
        const startDate = document.getElementById('startDate')?.value;
        const endDate = document.getElementById('endDate')?.value;
        const freq = document.getElementById('freq')?.value;
        const locationMode = document.getElementById('locationMode')?.value;
        
        // Validations de base
        if (!numBuildings || numBuildings <= 0) {
            alert('⚠️ Veuillez spécifier un nombre de bâtiments valide');
            return null;
        }
        
        if (!startDate || !endDate) {
            alert('⚠️ Veuillez spécifier les dates');
            return null;
        }
        
        if (new Date(startDate) >= new Date(endDate)) {
            alert('⚠️ La date de début doit être antérieure à la date de fin');
            return null;
        }
        
        let params = {
            num_buildings: numBuildings,
            start_date: startDate,
            end_date: endDate,
            freq: freq || '30T'
        };
        
        // Gestion du filtrage géographique
        if (locationMode === 'filter') {
            const region = document.getElementById('filterRegion')?.value;
            const state = document.getElementById('filterState')?.value;
            const city = document.getElementById('filterCity')?.value;
            const popMin = document.getElementById('popMin')?.value;
            const popMax = document.getElementById('popMax')?.value;
            
            if (region !== 'all' || state !== 'all' || city !== 'all' || popMin || popMax) {
                params.location_filter = {
                    region: region === 'all' ? null : region,
                    state: state === 'all' ? null : state,
                    city: city === 'all' ? null : city,
                    population_min: popMin ? parseInt(popMin) : null,
                    population_max: popMax ? parseInt(popMax) : null
                };
            }
        } else if (locationMode === 'custom') {
            const customCity = document.getElementById('customCity')?.value?.trim();
            const customState = document.getElementById('customState')?.value?.trim();
            const customRegion = document.getElementById('customRegion')?.value;
            const customPop = document.getElementById('customPopulation')?.value;
            const customLat = document.getElementById('customLat')?.value;
            const customLon = document.getElementById('customLon')?.value;
            
            if (customCity && customState && customRegion && customPop) {
                params.custom_location = {
                    name: customCity,
                    state: customState,
                    region: customRegion,
                    population: parseInt(customPop) || 100000,
                    latitude: parseFloat(customLat) || 3.1390,
                    longitude: parseFloat(customLon) || 101.6869
                };
            } else if (customCity || customState || customPop) {
                alert('⚠️ Pour la localisation personnalisée, remplissez : ville, état, région et population');
                return null;
            }
        }
        
        console.log('✅ Paramètres validés:', params);
        return params;
        
    } catch (error) {
        console.error('❌ Erreur validation paramètres:', error);
        alert('⚠️ Erreur dans les paramètres du formulaire');
        return null;
    }
}

// ==================== AFFICHAGE DES RÉSULTATS - VERSION CORRIGÉE ====================

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.toggle('show', show);
    }
}

function hideResults() {
    const results = document.getElementById('results');
    const validationPanel = document.getElementById('validationPanel');
    
    if (results) results.classList.remove('show');
    if (validationPanel) validationPanel.classList.remove('show');
}

function showResults(data, isSample = false) {
    console.log('🎨 Affichage des résultats:', data);
    
    const resultsDiv = document.getElementById('results');
    const alertsDiv = document.getElementById('alerts');
    const statsDiv = document.getElementById('statsGrid');
    const previewDiv = document.getElementById('dataPreview');
    
    if (!resultsDiv || !alertsDiv) {
        console.error('❌ Éléments de résultats manquants');
        return;
    }
    
    // Message de succès
    const dataSource = data.data_sources?.real_data_used ? 'VRAIES DONNÉES' : 'ESTIMATIONS';
    const sourceEmoji = data.data_sources?.real_data_used ? '🎯' : '📊';
    
    alertsDiv.innerHTML = `
        <div class="alert alert-success">
            ${sourceEmoji} ${isSample ? 'Échantillon généré' : 'Données générées avec succès!'} 
            - Source: ${dataSource}
        </div>
    `;
    
    // Statistiques - CORRECTION CRITIQUE: utiliser les bonnes clés
    if (data.stats && statsDiv) {
        const stats = data.stats;
        statsDiv.innerHTML = `
            <div class="stat-card">
                <h3>${(stats.total_records || stats.buildings_count || 0).toLocaleString()}</h3>
                <p>Bâtiments</p>
            </div>
            <div class="stat-card">
                <h3>${(data.location_analysis?.length || 0)}</h3>
                <p>Villes</p>
            </div>
            <div class="stat-card">
                <h3>${(stats.avg_consumption || 0).toFixed(1)}</h3>
                <p>Consommation Moy. (kWh)</p>
            </div>
            <div class="stat-card">
                <h3>${(stats.max_consumption || 0).toFixed(1)}</h3>
                <p>Pic Max (kWh)</p>
            </div>
        `;
    }
    
    // Aperçu des données - CORRECTION CRITIQUE: gérer les différentes structures
    if (previewDiv) {
        let buildingsData = [];
        let timeseriesData = [];
        let locationAnalysis = [];
        
        // Extraction flexible des données selon la structure de réponse
        if (data.buildings && Array.isArray(data.buildings)) {
            buildingsData = data.buildings;
        } else if (data.sample_buildings && Array.isArray(data.sample_buildings)) {
            buildingsData = data.sample_buildings;
        }
        
        if (data.timeseries && Array.isArray(data.timeseries)) {
            timeseriesData = data.timeseries;
        } else if (data.sample_timeseries && Array.isArray(data.sample_timeseries)) {
            timeseriesData = data.sample_timeseries;
        }
        
        if (data.location_analysis && Array.isArray(data.location_analysis)) {
            locationAnalysis = data.location_analysis;
        }
        
        console.log('📊 Données extraites:', {
            buildings: buildingsData.length,
            timeseries: timeseriesData.length,
            locations: locationAnalysis.length
        });
        
        let locationAnalysisHTML = '';
        
        if (locationAnalysis.length > 0) {
            locationAnalysisHTML = `
                <div style="margin-top: 20px;">
                    <h4>🏙️ Analyse par Ville</h4>
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 10px;">
            `;
            
            locationAnalysis.forEach(location => {
                const isRealData = location.data_source === 'VRAIES DONNÉES';
                const badge = isRealData ? 
                    '<span class="data-quality-badge badge-official">OFFICIEL</span>' :
                    '<span class="data-quality-badge badge-estimated">ESTIMÉ</span>';
                
                locationAnalysisHTML += `
                    <div class="city-data-item ${isRealData ? 'official' : 'estimated'}">
                        <div>
                            <strong>${location.location}</strong> (${location.state || 'État inconnu'})
                            <br><small>${(location.population || 0).toLocaleString()} hab. - ${location.building_count || 0} bâtiments</small>
                        </div>
                        <div>${badge}</div>
                    </div>
                `;
            });
            
            locationAnalysisHTML += '</div></div>';
        }
        
        // Affichage des bâtiments
        let buildingsHTML = '';
        if (buildingsData.length > 0) {
            buildingsHTML = `
                <h3>📋 Aperçu des Métadonnées - Villes de Malaisie</h3>
                <div style="overflow-x: auto; margin-bottom: 30px;">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Classe</th>
                                <th>Ville</th>
                                <th>État</th>
                                <th>Population</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${buildingsData.slice(0, 10).map(b => `
                                <tr>
                                    <td>${(b.unique_id || b.building_id || '').substring(0, 8)}...</td>
                                    <td><strong>${b.building_class || 'N/A'}</strong></td>
                                    <td>${b.location || 'N/A'}</td>
                                    <td>${b.state || 'N/A'}</td>
                                    <td>${(b.population || 0).toLocaleString()}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        // Affichage des séries temporelles
        let timeseriesHTML = '';
        if (timeseriesData.length > 0) {
            timeseriesHTML = `
                <h3>⚡ Aperçu des Données de Consommation</h3>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>ID Bâtiment</th>
                                <th>Timestamp</th>
                                <th>Consommation (kWh)</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${timeseriesData.slice(0, 15).map(t => `
                                <tr>
                                    <td>${(t.unique_id || '').substring(0, 8)}...</td>
                                    <td>${t.ds || t.timestamp ? new Date(t.ds || t.timestamp).toLocaleString('fr-FR') : 'N/A'}</td>
                                    <td><strong>${t.y || 0}</strong></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        // Assemblage final
        previewDiv.innerHTML = `
            <div class="data-preview">
                ${locationAnalysisHTML}
                ${buildingsHTML}
                ${timeseriesHTML}
                ${buildingsData.length === 0 && timeseriesData.length === 0 ? 
                    '<div style="text-align: center; padding: 20px; color: #666;"><p>🔄 Aperçu des données en cours de génération...</p></div>' : ''
                }
            </div>
        `;
    }
    
    // Afficher les informations sur la qualité des données
    if (data.data_sources) {
        showDataQualityInfo(data.data_sources);
    }
    
    // Validation si disponible
    if (data.validation && data.validation.enabled) {
        showValidation(data.validation);
    }
    
    resultsDiv.classList.add('show');
    console.log('✅ Résultats affichés avec succès');
}

function showValidation(validationData) {
    const validationPanel = document.getElementById('validationPanel');
    const validationScore = document.getElementById('validationScore');
    const validationDetails = document.getElementById('validationDetails');
    
    if (!validationPanel || !validationScore || !validationDetails) return;
    
    validationScore.textContent = `${validationData.quality_score}%`;
    
    const scoreClass = validationData.quality_score >= 80 ? 'excellent' : 
                      validationData.quality_score >= 70 ? 'good' : 
                      validationData.quality_score >= 50 ? 'fair' : 'poor';
    
    validationScore.className = `validation-score ${scoreClass}`;
    
    let detailsHTML = `
        <div style="text-align: center; margin-bottom: 15px;">
            <strong>Grade: ${validationData.grade}</strong><br>
            <small>Villes validées: ${validationData.cities_validated}</small>
        </div>
    `;
    
    if (validationData.recommendations && validationData.recommendations.length > 0) {
        detailsHTML += '<h4>🔧 Recommandations:</h4><ul>';
        validationData.recommendations.forEach(rec => {
            detailsHTML += `<li>${rec.action || rec}</li>`;
        });
        detailsHTML += '</ul>';
    }
    
    validationDetails.innerHTML = detailsHTML;
    validationPanel.classList.add('show');
}

function showDataQualityInfo(dataSources) {
    const dataQualityPanel = document.getElementById('dataQualityPanel');
    if (!dataQualityPanel) return;
    
    if (dataSources.real_data_used) {
        dataQualityPanel.className = 'data-source-panel official';
        dataQualityPanel.innerHTML = `
            <h3>🎯 VRAIES DONNÉES UTILISÉES</h3>
            <p><strong>Qualité:</strong> ${dataSources.data_quality}</p>
            <p><strong>Sources:</strong> Ministry of Health Malaysia, Ministry of Education, Tourism Malaysia</p>
            <div style="margin-top: 15px;">
                <span class="data-quality-badge badge-official">DONNÉES OFFICIELLES</span>
            </div>
        `;
    } else {
        dataQualityPanel.className = 'data-source-panel estimated';
        dataQualityPanel.innerHTML = `
            <h3>📊 ESTIMATIONS UTILISÉES</h3>
            <p><strong>Qualité:</strong> ${dataSources.data_quality}</p>
            <p><strong>Méthode:</strong> Distribution intelligente basée sur population</p>
            <div style="margin-top: 15px;">
                <span class="data-quality-badge badge-estimated">ESTIMATIONS</span>
            </div>
        `;
    }
    
    dataQualityPanel.style.display = 'block';
}

function showSuccess(message) {
    const alertsDiv = document.getElementById('alerts');
    const resultsDiv = document.getElementById('results');
    
    if (!alertsDiv || !resultsDiv) return;
    
    const dataSource = systemCapabilities.real_data_available ? '🎯 VRAIES DONNÉES' : '📊 ESTIMATIONS';
    
    alertsDiv.innerHTML = `
        <div class="alert alert-success">
            ${message}
            <br><small>Source: ${dataSource}</small>
        </div>
    `;
    
    resultsDiv.classList.add('show');
}

function showError(message) {
    const alertsDiv = document.getElementById('alerts');
    const resultsDiv = document.getElementById('results');
    
    if (!alertsDiv || !resultsDiv) {
        console.error('❌ Impossible d\'afficher l\'erreur:', message);
        alert(`Erreur: ${message}`);
        return;
    }
    
    alertsDiv.innerHTML = `
        <div class="alert alert-error">❌ ${message}</div>
    `;
    
    resultsDiv.classList.add('show');
}

// ==================== FONCTIONS DE DÉBOGAGE ====================

function debugApp() {
    console.log('🐛 DEBUG - État de l\'application:');
    console.log('- malaysiaData:', Object.keys(malaysiaData).length, 'villes');
    console.log('- systemCapabilities:', systemCapabilities);
    
    // Vérifier éléments DOM critiques
    const criticalElements = [
        'dataStatusIndicator', 'systemStatus', 'realDataPanel',
        'numBuildings', 'startDate', 'endDate', 'freq',
        'locationMode', 'filterRegion', 'loading', 'results', 'alerts',
        'statsGrid', 'dataPreview'
    ];
    
    const elementStatus = {};
    criticalElements.forEach(id => {
        const element = document.getElementById(id);
        elementStatus[id] = element ? '✅' : '❌';
    });
    
    console.table(elementStatus);
    
    // Test des paramètres actuels
    const currentParams = getFormParams();
    console.log('- Paramètres actuels:', currentParams);
    
    return {
        malaysiaData: Object.keys(malaysiaData).length,
        systemCapabilities,
        elementStatus,
        currentParams
    };
}

async function testAPI() {
    console.log('🔗 Test de connectivité API...');
    const results = {};
    
    try {
        console.log('Testing /api/stats...');
        const statsResponse = await fetch('/api/stats');
        results.stats = {
            status: statsResponse.status,
            ok: statsResponse.ok,
            data: statsResponse.ok ? await statsResponse.json() : null
        };
    } catch (error) {
        results.stats = { error: error.message };
    }
    
    try {
        console.log('Testing /api/real-data-status...');
        const statusResponse = await fetch('/api/real-data-status');
        results.realDataStatus = {
            status: statusResponse.status,
            ok: statusResponse.ok,
            data: statusResponse.ok ? await statusResponse.json() : null
        };
    } catch (error) {
        results.realDataStatus = { error: error.message };
    }
    
    try {
        console.log('Testing /sample...');
        const sampleResponse = await fetch('/sample');
        results.sample = {
            status: sampleResponse.status,
            ok: sampleResponse.ok,
            data: sampleResponse.ok ? await sampleResponse.json() : null
        };
    } catch (error) {
        results.sample = { error: error.message };
    }
    
    console.table(results);
    return results;
}

function resetApp() {
    console.log('🔄 Réinitialisation...');
    
    // Reset formulaire
    const elements = ['numBuildings', 'startDate', 'endDate', 'freq'];
    const defaults = { 'numBuildings': 50, 'startDate': '2024-01-01', 'endDate': '2024-01-31', 'freq': '30T' };
    
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.value = defaults[id] || '';
        }
    });
    
    // Reset sélecteurs
    const selectors = ['locationMode', 'filterRegion', 'filterState', 'filterCity'];
    selectors.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.selectedIndex = 0;
        }
    });
    
    hideResults();
    toggleLocationMode();
    updateEstimation();
    
    console.log('✅ Application réinitialisée');
}

function helpApp() {
    const help = `
🇲🇾 AIDE - GÉNÉRATEUR ÉLECTRICITÉ MALAYSIA
=========================================

🔧 FONCTIONS DE DÉBOGAGE:
debugApp()    - État de l'application
testAPI()     - Test connectivité API
resetApp()    - Réinitialiser interface

🎯 FONCTIONS PRINCIPALES:
generateData()     - Générer et afficher
downloadData()     - Générer et télécharger
showSample()       - Afficher échantillon

📊 VÉRIFICATIONS:
- Vérifiez la console pour les erreurs
- Utilisez F12 pour ouvrir les outils développeur
- Testez avec un petit échantillon d'abord

🆘 PROBLÈMES COURANTS:
1. Erreur 500: Problème serveur, vérifiez les logs
2. Pas de réponse: Vérifiez la connexion
3. Interface figée: Rafraîchissez (F5)
4. Paramètres invalides: Vérifiez les champs
5. Résultats vides: Vérifiez la structure des données

💡 CONSEILS:
- Commencez avec 5-10 bâtiments
- Utilisez une période courte (1 semaine)
- Vérifiez que les dates sont valides
- Ouvrez les outils développeur pour plus d'infos
`;
    
    console.log(help);
    return help;
}

// Exposer les fonctions de débogage globalement
window.debugApp = debugApp;
window.testAPI = testAPI;
window.resetApp = resetApp;
window.helpApp = helpApp;

// ==================== GESTION D'ERREURS GLOBALES ====================

window.addEventListener('error', function(e) {
    console.error('🚨 Erreur JavaScript:', e.message, 'à', e.filename + ':' + e.lineno);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('🚨 Promesse rejetée:', e.reason);
});

// ==================== VÉRIFICATIONS FINALES ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM chargé, vérifications finales...');
    
    // Vérifier éléments essentiels
    const essential = ['numBuildings', 'startDate', 'endDate', 'freq', 'results', 'alerts', 'statsGrid', 'dataPreview'];
    const missing = essential.filter(id => !document.getElementById(id));
    
    if (missing.length > 0) {
        console.error('❌ Éléments manquants:', missing);
        alert('⚠️ Interface incomplète. Rechargez la page.');
    } else {
        console.log('✅ Tous les éléments essentiels présents');
    }
    
    // Vérification retardée
    setTimeout(() => {
        if (Object.keys(malaysiaData).length === 0) {
            console.warn('⚠️ Rechargement données Malaysia...');
            loadMalaysiaData();
        }
    }, 3000);
});

// Message de bienvenue
console.log(`
🇲🇾 GÉNÉRATEUR MALAYSIA - VERSION CORRIGÉE AFFICHAGE
=====================================================
✅ JavaScript fonctionnel chargé
🔧 Fonctions de débogage disponibles
🎯 Support vraies données officielles
🐛 Gestion d'erreurs améliorée
📊 Affichage des résultats corrigé

Pour déboguer: debugApp()
Pour aide: helpApp()
Pour test API: testAPI()

CORRECTIFS APPLIQUÉS:
- Structure flexible des données de réponse
- Gestion des différents formats (buildings/sample_buildings)
- Extraction sécurisée des statistiques
- Affichage robuste même avec données partielles
- Debugging amélioré pour identifier les problèmes

Prêt à générer des données pour Malaysia! 🚀
`);

// Auto-test au chargement (optionnel)
setTimeout(() => {
    if (window.location.search.includes('debug=true')) {
        console.log('🔍 Auto-diagnostic activé...');
        debugApp();
    }
}, 5000);