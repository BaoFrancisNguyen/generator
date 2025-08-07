// Variables globales pour les données géographiques
let malaysiaData = {};

// Charger les données géographiques au démarrage
window.onload = function() {
    loadMalaysiaData();
    updateEstimation(); // Calculer l'estimation initiale
};

// Fonction d'estimation du dataset
function updateEstimation() {
    const numBuildings = parseInt(document.getElementById('numBuildings').value) || 0;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const freq = document.getElementById('freq').value;
    
    if (numBuildings === 0 || !startDate || !endDate) {
        return;
    }
    
    // Calculer le nombre d'observations
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    let observationsPerBuilding;
    let freqDescription;
    
    // Calculs selon la fréquence
    switch(freq) {
        case '5T':
            observationsPerBuilding = diffDays * 288; // 24*60/5 = 288 obs/jour
            freqDescription = "Très haute résolution - Idéal pour l'analyse fine des patterns";
            break;
        case '15T':
            observationsPerBuilding = diffDays * 96; // 24*60/15 = 96 obs/jour
            freqDescription = "Haute résolution - Parfait pour les détails horaires";
            break;
        case '30T':
            observationsPerBuilding = diffDays * 48; // 24*60/30 = 48 obs/jour
            freqDescription = "Résolution standard - Compatible avec les données originales";
            break;
        case '1H':
            observationsPerBuilding = diffDays * 24; // 24 obs/jour
            freqDescription = "Résolution horaire - Équilibre taille/détail";
            break;
        case '2H':
            observationsPerBuilding = diffDays * 12; // 12 obs/jour
            freqDescription = "Résolution bi-horaire - Patterns généraux";
            break;
        case '6H':
            observationsPerBuilding = diffDays * 4; // 4 obs/jour
            freqDescription = "4 fois par jour - Grandes tendances";
            break;
        case '12H':
            observationsPerBuilding = diffDays * 2; // 2 obs/jour
            freqDescription = "2 fois par jour - Patterns jour/nuit";
            break;
        case '1D':
            observationsPerBuilding = diffDays * 1; // 1 obs/jour
            freqDescription = "Quotidien - Évolution journalière";
            break;
        case '1W':
            observationsPerBuilding = Math.ceil(diffDays / 7); // 1 obs/semaine
            freqDescription = "Hebdomadaire - Tendances à long terme";
            break;
        case '1M':
            observationsPerBuilding = Math.ceil(diffDays / 30); // 1 obs/mois
            freqDescription = "Mensuel - Évolution saisonnière";
            break;
        default:
            observationsPerBuilding = diffDays * 48;
            freqDescription = "Résolution par défaut";
    }
    
    const totalObservations = numBuildings * observationsPerBuilding;
    
    // Estimation de la taille de fichier (en MB)
    const bytesPerObservation = 80; // Estimation basée sur format Parquet
    const fileSizeMB = (totalObservations * bytesPerObservation) / (1024 * 1024);
    
    // Estimation du temps de génération
    let generationTimeEstimate;
    if (totalObservations < 10000) {
        generationTimeEstimate = "< 10 secondes";
    } else if (totalObservations < 100000) {
        generationTimeEstimate = "10-30 secondes";
    } else if (totalObservations < 500000) {
        generationTimeEstimate = "30 secondes - 2 minutes";
    } else if (totalObservations < 1000000) {
        generationTimeEstimate = "2-5 minutes";
    } else if (totalObservations < 5000000) {
        generationTimeEstimate = "5-15 minutes";
    } else {
        generationTimeEstimate = "15+ minutes";
    }
    
    // Cas d'usage recommandé
    let useCase;
    if (totalObservations < 50000) {
        useCase = "🧪 Test/Développement";
    } else if (totalObservations < 500000) {
        useCase = "📚 Recherche/Étude";
    } else if (totalObservations < 2000000) {
        useCase = "🤖 Machine Learning";
    } else {
        useCase = "🏭 Production/Big Data";
    }
    
    // Guidance sur le nombre de bâtiments
    let buildingGuidance;
    if (numBuildings < 10) {
        buildingGuidance = "Très petit échantillon - Idéal pour tester";
    } else if (numBuildings < 100) {
        buildingGuidance = "Échantillon léger - Bon pour le développement";
    } else if (numBuildings < 500) {
        buildingGuidance = "Échantillon moyen - Représentatif d'une ville";
    } else if (numBuildings < 2000) {
        buildingGuidance = "Grand échantillon - Représentatif d'une région";
    } else {
        buildingGuidance = "Très grand échantillon - Représentatif du pays";
    }
    
    // Mise à jour de l'interface
    document.getElementById('totalObservations').textContent = totalObservations.toLocaleString();
    document.getElementById('fileSize').textContent = fileSizeMB > 1 ? 
        `${Math.round(fileSizeMB)} MB` : `${Math.round(fileSizeMB * 1024)} KB`;
    document.getElementById('generationTime').textContent = generationTimeEstimate;
    document.getElementById('useCase').textContent = useCase;
    document.getElementById('freqInfo').textContent = freqDescription;
    document.getElementById('buildingGuidance').textContent = buildingGuidance;
}

async function loadMalaysiaData() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        if (data.success) {
            malaysiaData = data.malaysia_locations;
            populateFilterOptions();
        }
    } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
    }
}

function populateFilterOptions() {
    // Populate regions
    const regions = [...new Set(Object.values(malaysiaData).map(loc => loc.region))];
    const regionSelect = document.getElementById('filterRegion');
    regions.forEach(region => {
        const option = document.createElement('option');
        option.value = region;
        option.textContent = region;
        regionSelect.appendChild(option);
    });
}

function toggleLocationMode() {
    const mode = document.getElementById('locationMode').value;
    const filterSection = document.getElementById('filterSection');
    const customSection = document.getElementById('customSection');
    
    filterSection.style.display = mode === 'filter' ? 'block' : 'none';
    customSection.style.display = mode === 'custom' ? 'block' : 'none';
}

function updateStateOptions() {
    const selectedRegion = document.getElementById('filterRegion').value;
    const stateSelect = document.getElementById('filterState');
    const citySelect = document.getElementById('filterCity');
    
    // Reset states and cities
    stateSelect.innerHTML = '<option value="all">Tous les états</option>';
    citySelect.innerHTML = '<option value="all">Toutes les villes</option>';
    
    if (selectedRegion === 'all') {
        const states = [...new Set(Object.values(malaysiaData).map(loc => loc.state))];
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
    } else {
        const states = [...new Set(
            Object.values(malaysiaData)
                .filter(loc => loc.region === selectedRegion)
                .map(loc => loc.state)
        )];
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
    }
}

function updateCityOptions() {
    const selectedRegion = document.getElementById('filterRegion').value;
    const selectedState = document.getElementById('filterState').value;
    const citySelect = document.getElementById('filterCity');
    
    // Reset cities
    citySelect.innerHTML = '<option value="all">Toutes les villes</option>';
    
    let filteredCities = Object.entries(malaysiaData);
    
    if (selectedRegion !== 'all') {
        filteredCities = filteredCities.filter(([name, info]) => info.region === selectedRegion);
    }
    
    if (selectedState !== 'all') {
        filteredCities = filteredCities.filter(([name, info]) => info.state === selectedState);
    }
    
    filteredCities
        .sort((a, b) => b[1].population - a[1].population) // Sort by population
        .forEach(([name, info]) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = `${name} (${info.population.toLocaleString()} hab.)`;
            citySelect.appendChild(option);
        });
}

function updatePopulationInputs() {
    const range = document.getElementById('populationRange').value;
    const customRange = document.getElementById('customPopulationRange');
    
    customRange.style.display = range === 'custom' ? 'block' : 'none';
    
    // Set preset ranges
    const popMin = document.getElementById('popMin');
    const popMax = document.getElementById('popMax');
    
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

async function generateData() {
    showLoading(true);
    hideResults();
    
    try {
        const params = getFormParams();
        if (!params) {
            showLoading(false);
            return;
        }
        
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        showLoading(false);
        
        if (data.success) {
            showResults(data);
        } else {
            showError(data.error);
        }
    } catch (error) {
        showLoading(false);
        showError('Erreur de connexion: ' + error.message);
    }
}

async function downloadData() {
    showLoading(true);
    
    try {
        const params = getFormParams();
        if (!params) {
            showLoading(false);
            return;
        }
        
        const response = await fetch('/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        showLoading(false);
        
        if (data.success) {
            showSuccess('✅ Fichiers générés avec succès!\n' + data.message);
        } else {
            showError(data.error);
        }
    } catch (error) {
        showLoading(false);
        showError('Erreur: ' + error.message);
    }
}

async function showSample() {
    try {
        const response = await fetch('/sample');
        const data = await response.json();
        
        if (data.success) {
            showResults(data, true);
        }
    } catch (error) {
        showError('Erreur: ' + error.message);
    }
}

function getFormParams() {
    const locationMode = document.getElementById('locationMode').value;
    
    let params = {
        num_buildings: parseInt(document.getElementById('numBuildings').value),
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        freq: document.getElementById('freq').value
    };
    
    // Add location filtering
    if (locationMode === 'filter') {
        const region = document.getElementById('filterRegion').value;
        const state = document.getElementById('filterState').value;
        const city = document.getElementById('filterCity').value;
        const popMin = document.getElementById('popMin').value;
        const popMax = document.getElementById('popMax').value;
        
        // Seulement ajouter le filtre s'il y a vraiment une sélection
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
        const customCity = document.getElementById('customCity').value.trim();
        const customState = document.getElementById('customState').value.trim();
        const customRegion = document.getElementById('customRegion').value;
        const customPop = document.getElementById('customPopulation').value;
        const customLat = document.getElementById('customLat').value;
        const customLon = document.getElementById('customLon').value;
        
        // Vérifier que les champs obligatoires sont remplis
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
            // Si certains champs sont remplis mais pas tous, alerter l'utilisateur
            alert('⚠️ Pour la localisation personnalisée, veuillez remplir au minimum : Nom de la ville, État, Région et Population');
            return null;
        }
    }
    
    return params;
}

function showLoading(show) {
    document.getElementById('loading').classList.toggle('show', show);
}

function hideResults() {
    document.getElementById('results').classList.remove('show');
}

function showResults(data, isSample = false) {
    const resultsDiv = document.getElementById('results');
    const alertsDiv = document.getElementById('alerts');
    const statsDiv = document.getElementById('statsGrid');
    const previewDiv = document.getElementById('dataPreview');
    
    // Success message
    alertsDiv.innerHTML = `
        <div class="alert alert-success">
            ${isSample ? '👁️ Échantillon généré' : '🎉 Données générées avec succès!'}
        </div>
    `;
    
    // Stats
    if (data.stats) {
        statsDiv.innerHTML = `
            <div class="stat-card">
                <h3>${data.stats.total_records.toLocaleString()}</h3>
                <p>Observations</p>
            </div>
            <div class="stat-card">
                <h3>${data.stats.buildings_count}</h3>
                <p>Bâtiments</p>
            </div>
            <div class="stat-card">
                <h3>${data.stats.avg_consumption}</h3>
                <p>Consommation Moy. (kWh)</p>
            </div>
            <div class="stat-card">
                <h3>${data.stats.max_consumption}</h3>
                <p>Pic Max (kWh)</p>
            </div>
        `;
    }
    
    // Data preview
    if (data.buildings && data.timeseries) {
        previewDiv.innerHTML = `
            <div class="data-preview">
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
                                <th>Coordonnées</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.buildings.slice(0, 10).map(b => `
                                <tr>
                                    <td>${b.unique_id.substring(0, 8)}...</td>
                                    <td><strong>${b.building_class}</strong></td>
                                    <td>${b.location}</td>
                                    <td>${b.state}</td>
                                    <td>${b.population.toLocaleString()}</td>
                                    <td>${b.latitude}, ${b.longitude}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <h3>⚡ Aperçu des Données de Consommation (Climat Tropical)</h3>
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
                            ${data.timeseries.slice(0, 15).map(t => `
                                <tr>
                                    <td>${t.unique_id.substring(0, 8)}...</td>
                                    <td>${new Date(t.timestamp).toLocaleString('fr-FR')}</td>
                                    <td><strong>${t.y}</strong></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    resultsDiv.classList.add('show');
}

function showSuccess(message) {
    document.getElementById('alerts').innerHTML = `
        <div class="alert alert-success">${message}</div>
    `;
    document.getElementById('results').classList.add('show');
}

function showError(message) {
    document.getElementById('alerts').innerHTML = `
        <div class="alert alert-error">❌ ${message}</div>
    `;
    document.getElementById('results').classList.add('show');
}