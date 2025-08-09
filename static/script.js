/**
 * SCRIPT PRINCIPAL - GÉNÉRATEUR DE DONNÉES MALAYSIA
 * Fichier: static/script.js
 * 
 * Ce fichier gère l'interface utilisateur principale et l'affichage des données
 * Correctif des problèmes d'aperçu des données et de cartographie
 */

// ==================== CONFIGURATION GLOBALE ====================

// Variables globales pour l'état de l'application
let currentZoneData = null;
let loadedBuildings = [];
let previewMap = null;
let buildingMarkers = [];
let malaysiaCitiesData = {};

// Configuration API
const API_CONFIG = {
    generateUrl: '/generate',
    osmUrl: '/generate-from-osm',
    timeout: 300000, // 5 minutes
    retryAttempts: 3
};

// ==================== INITIALISATION ====================

/**
 * Initialise l'application au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation de l\'application Malaysia Generator...');
    
    // Charger les données des villes malaysiennes
    loadMalaysiaCitiesData();
    
    // Initialiser les écouteurs d'événements
    initEventListeners();
    
    // Initialiser la carte de prévisualisation
    initPreviewMap();
    
    // Valider l'interface utilisateur
    validateInterface();
    
    console.log('✅ Application initialisée avec succès');
});

/**
 * Charge les données des villes malaysiennes
 */
function loadMalaysiaCitiesData() {
    malaysiaCitiesData = {
        'Kuala Lumpur': { lat: 3.1390, lon: 101.6869, population: 1800000, state: 'Federal Territory' },
        'George Town': { lat: 5.4164, lon: 100.3327, population: 708000, state: 'Penang' },
        'Ipoh': { lat: 4.5975, lon: 101.0901, population: 657000, state: 'Perak' },
        'Shah Alam': { lat: 3.0733, lon: 101.5185, population: 641000, state: 'Selangor' },
        'Petaling Jaya': { lat: 3.1073, lon: 101.6059, population: 613000, state: 'Selangor' },
        'Johor Bahru': { lat: 1.4927, lon: 103.7414, population: 497000, state: 'Johor' },
        'Kota Kinabalu': { lat: 5.9788, lon: 116.0753, population: 452000, state: 'Sabah' },
        'Kuching': { lat: 1.5533, lon: 110.3592, population: 325000, state: 'Sarawak' }
    };
    
    console.log(`📍 ${Object.keys(malaysiaCitiesData).length} villes malaysiennes chargées`);
}

/**
 * Initialise tous les écouteurs d'événements
 */
function initEventListeners() {
    // Bouton de génération principal
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerate);
    }
    
    // Boutons de la carte
    const loadBuildingsBtn = document.getElementById('loadRealBuildings');
    if (loadBuildingsBtn) {
        loadBuildingsBtn.addEventListener('click', loadRealBuildings);
    }
    
    const centerBtn = document.getElementById('centerOnZone');
    if (centerBtn) {
        centerBtn.addEventListener('click', centerOnSelectedZone);
    }
    
    const clearBtn = document.getElementById('clearPreview');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearMapPreview);
    }
    
    // Sélection de zone
    const zoneSelect = document.getElementById('zoneSelect');
    if (zoneSelect) {
        zoneSelect.addEventListener('change', handleZoneSelection);
    }
    
    console.log('👂 Écouteurs d\'événements initialisés');
}

// ==================== GESTION DE LA CARTE ====================

/**
 * Initialise la carte de prévisualisation Leaflet
 */
function initPreviewMap() {
    try {
        const mapContainer = document.getElementById('previewMap');
        if (!mapContainer) {
            console.warn('⚠️ Conteneur de carte non trouvé');
            return;
        }
        
        // Créer la carte centrée sur la Malaisie
        previewMap = L.map('previewMap').setView([4.2105, 101.9758], 6);
        
        // Ajouter le layer de tuiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(previewMap);
        
        // Ajouter les marqueurs des villes principales
        addCityMarkers();
        
        updateMapStatus('Carte initialisée - Sélectionnez une zone');
        console.log('🗺️ Carte de prévisualisation initialisée');
        
    } catch (error) {
        console.error('❌ Erreur initialisation carte:', error);
        updateMapStatus('Erreur lors de l\'initialisation de la carte');
    }
}

/**
 * Ajoute les marqueurs des principales villes malaysiennes
 */
function addCityMarkers() {
    Object.entries(malaysiaCitiesData).forEach(([cityName, cityData]) => {
        const marker = L.marker([cityData.lat, cityData.lon])
            .addTo(previewMap)
            .bindPopup(`
                <div style="font-family: Arial; padding: 10px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c5aa0;">${cityName}</h4>
                    <p style="margin: 5px 0;"><strong>État:</strong> ${cityData.state}</p>
                    <p style="margin: 5px 0;"><strong>Population:</strong> ${cityData.population.toLocaleString()}</p>
                    <p style="margin: 5px 0;"><strong>Coordonnées:</strong> ${cityData.lat.toFixed(4)}, ${cityData.lon.toFixed(4)}</p>
                </div>
            `);
        
        // Événement de clic pour sélectionner automatiquement la ville
        marker.on('click', function() {
            selectCity(cityName, cityData);
        });
    });
}

/**
 * Sélectionne une ville et met à jour l'interface
 */
function selectCity(cityName, cityData) {
    currentZoneData = {
        name: cityName,
        type: 'city',
        lat: cityData.lat,
        lon: cityData.lon,
        population: cityData.population,
        state: cityData.state
    };
    
    // Mettre à jour l'affichage des données de zone
    updateZoneDisplay();
    
    // Centrer la carte sur la ville
    previewMap.setView([cityData.lat, cityData.lon], 12);
    
    console.log(`📍 Zone sélectionnée: ${cityName}`);
}

/**
 * Charge les vrais bâtiments depuis OSM
 */
async function loadRealBuildings() {
    if (!currentZoneData) {
        showAlert('Veuillez d\'abord sélectionner une zone', 'warning');
        return;
    }
    
    try {
        updateMapStatus('🏗️ Chargement des bâtiments OSM...');
        showLoading('Récupération des données OpenStreetMap');
        
        // Requête Overpass API pour récupérer les bâtiments
        const overpassQuery = `
            [out:json][timeout:25];
            (
                way["building"]
                (${currentZoneData.lat - 0.01}, ${currentZoneData.lon - 0.01}, ${currentZoneData.lat + 0.01}, ${currentZoneData.lon + 0.01});
                relation["building"]
                (${currentZoneData.lat - 0.01}, ${currentZoneData.lon - 0.01}, ${currentZoneData.lat + 0.01}, ${currentZoneData.lon + 0.01});
            );
            out geom;
        `;
        
        const response = await fetch('https://overpass-api.de/api/interpreter', {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain' },
            body: overpassQuery
        });
        
        if (!response.ok) {
            throw new Error(`Erreur API Overpass: ${response.status}`);
        }
        
        const osmData = await response.json();
        
        // Traiter les données OSM
        loadedBuildings = processOSMBuildings(osmData.elements);
        
        // Afficher les bâtiments sur la carte
        displayBuildingsOnMap(loadedBuildings);
        
        // Mettre à jour les statistiques
        updateBuildingStats();
        
        hideLoading();
        updateMapStatus(`✅ ${loadedBuildings.length} bâtiments chargés avec succès`);
        
        console.log(`🏗️ ${loadedBuildings.length} bâtiments OSM chargés`);
        
    } catch (error) {
        hideLoading();
        console.error('❌ Erreur chargement OSM:', error);
        showAlert(`Erreur lors du chargement des bâtiments: ${error.message}`, 'error');
        updateMapStatus('❌ Échec du chargement des bâtiments');
    }
}

/**
 * Traite les données brutes OSM en format utilisable
 */
function processOSMBuildings(elements) {
    const buildings = [];
    
    elements.forEach((element, index) => {
        if (element.geometry && element.geometry.length > 0) {
            const building = {
                id: element.id || `generated_${index}`,
                type: element.tags?.building || 'residential',
                tags: element.tags || {},
                geometry: element.geometry,
                // Ajouter des métadonnées pour la génération
                location: currentZoneData.name,
                state: currentZoneData.state,
                estimated_area: calculateBuildingArea(element.geometry),
                building_class: classifyBuilding(element.tags)
            };
            
            buildings.push(building);
        }
    });
    
    return buildings;
}

/**
 * Affiche les bâtiments sur la carte avec des couleurs selon le type
 */
function displayBuildingsOnMap(buildings) {
    // Nettoyer les anciens marqueurs
    clearBuildingMarkers();
    
    const buildingColors = {
        'residential': '#4CAF50',
        'commercial': '#2196F3',
        'industrial': '#FF9800',
        'public': '#9C27B0',
        'other': '#757575'
    };
    
    buildings.forEach(building => {
        if (building.geometry && building.geometry.length > 0) {
            // Convertir la géométrie en coordonnées Leaflet
            const coordinates = building.geometry.map(coord => [coord.lat, coord.lon]);
            
            const buildingType = building.building_class || 'other';
            const color = buildingColors[buildingType] || buildingColors.other;
            
            // Créer un polygone pour le bâtiment
            const polygon = L.polygon(coordinates, {
                color: color,
                weight: 2,
                fillOpacity: 0.6
            }).addTo(previewMap);
            
            // Ajouter une popup avec les informations du bâtiment
            polygon.bindPopup(`
                <div style="font-family: Arial; padding: 10px;">
                    <h4 style="margin: 0 0 10px 0; color: ${color};">Bâtiment #${building.id}</h4>
                    <p><strong>Type:</strong> ${building.type}</p>
                    <p><strong>Classe:</strong> ${building.building_class}</p>
                    <p><strong>Surface estimée:</strong> ${building.estimated_area}m²</p>
                    <p><strong>Lieu:</strong> ${building.location}, ${building.state}</p>
                </div>
            `);
            
            buildingMarkers.push(polygon);
        }
    });
    
    // Ajuster la vue pour inclure tous les bâtiments
    if (buildingMarkers.length > 0) {
        const group = new L.featureGroup(buildingMarkers);
        previewMap.fitBounds(group.getBounds().pad(0.1));
    }
}

// ==================== GESTION DES DONNÉES ====================

/**
 * Gère la génération des données principales
 */
async function handleGenerate() {
    if (!validateInputs()) {
        return;
    }
    
    try {
        showLoading('🏗️ Génération des données en cours...');
        updateLoadingStatus('Préparation des paramètres...');
        
        // Préparer les données de requête
        const requestData = {
            num_buildings: parseInt(document.getElementById('numBuildings').value),
            start_date: document.getElementById('startDate').value,
            end_date: document.getElementById('endDate').value,
            freq: document.getElementById('freq').value,
            zone_data: currentZoneData,
            use_real_buildings: loadedBuildings.length > 0,
            buildings_osm: loadedBuildings
        };
        
        updateLoadingStatus('Envoi vers le serveur...');
        
        // Appel API
        const response = await fetchWithTimeout(API_CONFIG.generateUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        }, API_CONFIG.timeout);
        
        if (!response.ok) {
            throw new Error(`Erreur serveur: ${response.status} - ${response.statusText}`);
        }
        
        updateLoadingStatus('Traitement des résultats...');
        const result = await response.json();
        
        hideLoading();
        
        // Afficher les résultats
        displayResults(result);
        
        console.log('✅ Génération terminée avec succès');
        
    } catch (error) {
        hideLoading();
        console.error('❌ Erreur lors de la génération:', error);
        showAlert(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche les résultats de génération - VERSION CORRIGÉE
 */
function displayResults(data) {
    console.log('📊 Affichage des résultats:', data);
    
    // Nettoyer l'affichage précédent
    clearResults();
    
    try {
        // 1. Afficher les statistiques générales
        displayGeneralStats(data);
        
        // 2. Afficher l'aperçu des données
        displayDataPreview(data);
        
        // 3. Afficher les graphiques si disponibles
        if (data.charts) {
            displayCharts(data.charts);
        }
        
        // 4. Activer les boutons de téléchargement
        enableDownloadButtons(data);
        
        // Faire défiler vers les résultats
        document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        
        showAlert('✅ Génération terminée avec succès!', 'success');
        
    } catch (error) {
        console.error('❌ Erreur affichage résultats:', error);
        showAlert('Erreur lors de l\'affichage des résultats', 'error');
    }
}

/**
 * Affiche les statistiques générales
 */
function displayGeneralStats(data) {
    const statsContainer = document.getElementById('statsGrid');
    if (!statsContainer) return;
    
    // Extraire les statistiques de manière flexible
    const stats = extractStats(data);
    
    let statsHTML = '<div class="stats-grid">';
    
    // Statistiques de base
    if (stats.buildings_count) {
        statsHTML += createStatCard('🏗️', 'Bâtiments', stats.buildings_count, 'générés');
    }
    
    if (stats.records_count) {
        statsHTML += createStatCard('📊', 'Enregistrements', stats.records_count.toLocaleString(), 'données');
    }
    
    if (stats.period) {
        statsHTML += createStatCard('📅', 'Période', stats.period, '');
    }
    
    if (stats.location) {
        statsHTML += createStatCard('📍', 'Localisation', stats.location, '');
    }
    
    statsHTML += '</div>';
    
    statsContainer.innerHTML = statsHTML;
    statsContainer.style.display = 'block';
}

/**
 * Affiche l'aperçu des données - VERSION CORRIGÉE
 */
function displayDataPreview(data) {
    const previewContainer = document.getElementById('dataPreview');
    if (!previewContainer) return;
    
    let previewHTML = '<div class="data-preview-content">';
    
    // 1. Aperçu des bâtiments/métadonnées
    const buildingsData = data.buildings || data.sample_buildings || data.metadata || [];
    if (buildingsData.length > 0) {
        previewHTML += generateBuildingsPreview(buildingsData.slice(0, 5));
    }
    
    // 2. Aperçu des données temporelles
    const timeseriesData = data.timeseries || data.consumption_data || data.data || [];
    if (timeseriesData.length > 0) {
        previewHTML += generateTimeseriesPreview(timeseriesData.slice(0, 10));
    }
    
    // 3. Informations de qualité des données
    if (data.data_quality || data.generation_info) {
        previewHTML += generateQualityInfo(data.data_quality || data.generation_info);
    }
    
    previewHTML += '</div>';
    
    previewContainer.innerHTML = previewHTML;
    previewContainer.style.display = 'block';
    
    console.log('📋 Aperçu des données affiché');
}

/**
 * Génère l'aperçu des bâtiments
 */
function generateBuildingsPreview(buildings) {
    let html = `
        <div class="preview-section">
            <h4>🏗️ Aperçu des Bâtiments (${buildings.length} premiers)</h4>
            <div class="table-responsive">
                <table class="preview-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Type</th>
                            <th>Localisation</th>
                            <th>Classe</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    buildings.forEach(building => {
        html += `
            <tr>
                <td>${(building.id || building.building_id || building.unique_id || 'N/A').toString().substring(0, 8)}...</td>
                <td><span class="badge badge-info">${building.type || building.building_type || 'N/A'}</span></td>
                <td>${building.location || building.city || currentZoneData?.name || 'N/A'}</td>
                <td>${building.building_class || building.class || 'N/A'}</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Génère l'aperçu des données temporelles
 */
function generateTimeseriesPreview(timeseries) {
    let html = `
        <div class="preview-section">
            <h4>⚡ Aperçu des Données de Consommation (${timeseries.length} premiers)</h4>
            <div class="table-responsive">
                <table class="preview-table">
                    <thead>
                        <tr>
                            <th>ID Bâtiment</th>
                            <th>Timestamp</th>
                            <th>Consommation (kWh)</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    timeseries.forEach(record => {
        const timestamp = record.ds || record.timestamp || record.date || 'N/A';
        const consumption = record.y || record.consumption || record.value || 0;
        const buildingId = record.unique_id || record.building_id || record.id || 'N/A';
        
        html += `
            <tr>
                <td>${buildingId.toString().substring(0, 8)}...</td>
                <td>${timestamp}</td>
                <td><strong>${consumption.toFixed(2)}</strong></td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

// ==================== UTILITAIRES ====================

/**
 * Extrait les statistiques de manière flexible depuis les données
 */
function extractStats(data) {
    const stats = {};
    
    // Nombre de bâtiments
    if (data.buildings) stats.buildings_count = data.buildings.length;
    else if (data.sample_buildings) stats.buildings_count = data.sample_buildings.length;
    else if (data.metadata) stats.buildings_count = data.metadata.length;
    
    // Nombre d'enregistrements
    if (data.timeseries) stats.records_count = data.timeseries.length;
    else if (data.consumption_data) stats.records_count = data.consumption_data.length;
    else if (data.data) stats.records_count = data.data.length;
    
    // Période
    if (data.period) stats.period = data.period;
    else if (data.start_date && data.end_date) {
        stats.period = `${data.start_date} → ${data.end_date}`;
    }
    
    // Localisation
    if (data.location) stats.location = data.location;
    else if (currentZoneData) stats.location = currentZoneData.name;
    
    return stats;
}

/**
 * Crée une carte de statistique
 */
function createStatCard(icon, label, value, unit) {
    return `
        <div class="stat-card">
            <div class="stat-icon">${icon}</div>
            <div class="stat-content">
                <div class="stat-value">${value}</div>
                <div class="stat-label">${label}</div>
                <div class="stat-unit">${unit}</div>
            </div>
        </div>
    `;
}

/**
 * Utilitaire de fetch avec timeout
 */
async function fetchWithTimeout(url, options, timeout = 30000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        if (error.name === 'AbortError') {
            throw new Error('Timeout: La requête a pris trop de temps');
        }
        throw error;
    }
}

// ==================== GESTION UI ====================

/**
 * Affiche un indicateur de chargement
 */
function showLoading(message = 'Chargement en cours...') {
    // Implémentation de l'indicateur de chargement
    console.log(`⏳ ${message}`);
}

/**
 * Cache l'indicateur de chargement
 */
function hideLoading() {
    console.log('✅ Chargement terminé');
}

/**
 * Met à jour le statut de chargement
 */
function updateLoadingStatus(message) {
    console.log(`📄 Statut: ${message}`);
}

/**
 * Affiche une alerte utilisateur
 */
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts');
    if (alertsContainer) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        alertsContainer.appendChild(alertDiv);
        
        // Supprimer l'alerte après 5 secondes
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
    
    console.log(`📢 [${type.toUpperCase()}] ${message}`);
}

/**
 * Valide les inputs du formulaire
 */
function validateInputs() {
    const numBuildings = document.getElementById('numBuildings')?.value;
    const startDate = document.getElementById('startDate')?.value;
    const endDate = document.getElementById('endDate')?.value;
    
    if (!numBuildings || numBuildings < 1) {
        showAlert('Veuillez entrer un nombre de bâtiments valide', 'error');
        return false;
    }
    
    if (!startDate || !endDate) {
        showAlert('Veuillez sélectionner des dates valides', 'error');
        return false;
    }
    
    if (new Date(startDate) >= new Date(endDate)) {
        showAlert('La date de fin doit être après la date de début', 'error');
        return false;
    }
    
    return true;
}

// ==================== FONCTIONS D'INTERFACE ====================

function updateZoneDisplay() {
    if (!currentZoneData) return;
    
    const elements = {
        'zoneNameDisplay': currentZoneData.name,
        'zoneTypeDisplay': currentZoneData.type,
        'zonePopulationDisplay': currentZoneData.population?.toLocaleString(),
        'zoneAreaDisplay': 'Zone métropolitaine'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element && value) {
            element.textContent = value;
        }
    });
}

function updateMapStatus(message) {
    const statusElement = document.getElementById('mapStatus');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

function updateBuildingStats() {
    const statsElement = document.getElementById('buildingTypesStats');
    const countElement = document.getElementById('loadedBuildingsCount');
    
    if (countElement) {
        countElement.textContent = loadedBuildings.length;
    }
    
    if (statsElement && loadedBuildings.length > 0) {
        const typeCount = {};
        loadedBuildings.forEach(building => {
            const type = building.building_class || 'other';
            typeCount[type] = (typeCount[type] || 0) + 1;
        });
        
        let statsHTML = '';
        Object.entries(typeCount).forEach(([type, count]) => {
            statsHTML += `
                <div class="stat-row">
                    <span class="stat-type">${type}</span>
                    <span class="stat-count">${count}</span>
                </div>
            `;
        });
        
        statsElement.innerHTML = statsHTML;
    }
}

function clearResults() {
    ['statsGrid', 'dataPreview'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.innerHTML = '';
            element.style.display = 'none';
        }
    });
}

function clearBuildingMarkers() {
    buildingMarkers.forEach(marker => {
        if (previewMap && previewMap.hasLayer(marker)) {
            previewMap.removeLayer(marker);
        }
    });
    buildingMarkers = [];
}

function clearMapPreview() {
    clearBuildingMarkers();
    loadedBuildings = [];
    updateBuildingStats();
    updateMapStatus('Carte nettoyée');
    console.log('🧹 Aperçu de carte nettoyé');
}

function centerOnSelectedZone() {
    if (currentZoneData && previewMap) {
        previewMap.setView([currentZoneData.lat, currentZoneData.lon], 12);
        updateMapStatus(`Centré sur ${currentZoneData.name}`);
    } else {
        showAlert('Veuillez d\'abord sélectionner une zone', 'warning');
    }
}

function handleZoneSelection(event) {
    const selectedCity = event.target.value;
    if (selectedCity && malaysiaCitiesData[selectedCity]) {
        selectCity(selectedCity, malaysiaCitiesData[selectedCity]);
    }
}

function validateInterface() {
    const requiredElements = ['generateBtn', 'previewMap', 'numBuildings', 'startDate', 'endDate'];
    const missing = requiredElements.filter(id => !document.getElementById(id));
    
    if (missing.length > 0) {
        console.warn('⚠️ Éléments manquants:', missing);
    } else {
        console.log('✅ Interface validée');
    }
}

// ==================== UTILITAIRES BÂTIMENTS ====================

function calculateBuildingArea(geometry) {
    // Calcul approximatif de l'aire d'un bâtiment
    if (!geometry || geometry.length < 3) return 0;
    
    // Formule de Shoelace pour calculer l'aire d'un polygone
    let area = 0;
    const n = geometry.length;
    
    for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        area += geometry[i].lat * geometry[j].lon;
        area -= geometry[j].lat * geometry[i].lon;
    }
    
    // Convertir en mètres carrés approximatifs
    return Math.abs(area * 111000 * 111000 / 2);
}

function classifyBuilding(tags) {
    if (!tags) return 'residential';
    
    const buildingType = tags.building;
    
    if (['residential', 'house', 'apartment', 'apartments'].includes(buildingType)) {
        return 'residential';
    } else if (['commercial', 'retail', 'shop', 'office'].includes(buildingType)) {
        return 'commercial';
    } else if (['industrial', 'warehouse', 'factory'].includes(buildingType)) {
        return 'industrial';
    } else if (['public', 'school', 'hospital', 'government'].includes(buildingType)) {
        return 'public';
    }
    
    return 'other';
}

// ==================== FONCTIONS DE TÉLÉCHARGEMENT ====================

function enableDownloadButtons(data) {
    // Créer ou mettre à jour les boutons de téléchargement
    const downloadContainer = document.getElementById('downloadButtons') || createDownloadContainer();
    
    downloadContainer.innerHTML = `
        <div class="download-buttons">
            <h4>📥 Télécharger les données</h4>
            <div class="button-group">
                <button onclick="downloadJSON()" class="btn btn-primary">
                    📄 JSON
                </button>
                <button onclick="downloadCSV()" class="btn btn-success">
                    📊 CSV
                </button>
                <button onclick="downloadExcel()" class="btn btn-info">
                    📈 Excel
                </button>
            </div>
        </div>
    `;
    
    // Stocker les données pour le téléchargement
    window.lastGeneratedData = data;
}

function createDownloadContainer() {
    const container = document.createElement('div');
    container.id = 'downloadButtons';
    container.className = 'download-container';
    
    const resultsSection = document.getElementById('results');
    if (resultsSection) {
        resultsSection.appendChild(container);
    }
    
    return container;
}

function downloadJSON() {
    if (!window.lastGeneratedData) {
        showAlert('Aucune donnée à télécharger', 'error');
        return;
    }
    
    const dataStr = JSON.stringify(window.lastGeneratedData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    downloadFile(dataBlob, 'malaysia_energy_data.json');
}

function downloadCSV() {
    if (!window.lastGeneratedData) {
        showAlert('Aucune donnée à télécharger', 'error');
        return;
    }
    
    // Convertir les données en CSV
    const timeseries = window.lastGeneratedData.timeseries || 
                      window.lastGeneratedData.consumption_data || 
                      window.lastGeneratedData.data || [];
    
    if (timeseries.length === 0) {
        showAlert('Aucune donnée temporelle à exporter', 'error');
        return;
    }
    
    let csvContent = 'building_id,timestamp,consumption_kwh\n';
    
    timeseries.forEach(record => {
        const buildingId = record.unique_id || record.building_id || record.id || '';
        const timestamp = record.ds || record.timestamp || record.date || '';
        const consumption = record.y || record.consumption || record.value || 0;
        
        csvContent += `${buildingId},${timestamp},${consumption}\n`;
    });
    
    const csvBlob = new Blob([csvContent], { type: 'text/csv' });
    downloadFile(csvBlob, 'malaysia_energy_timeseries.csv');
}

function downloadExcel() {
    showAlert('Fonction Excel en développement', 'info');
}

function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    
    document.body.appendChild(a);
    a.click();
    
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showAlert(`✅ Fichier ${filename} téléchargé`, 'success');
}

// ==================== FONCTIONS DE DÉBOGAGE ====================

function debugApp() {
    console.log('🔍 DIAGNOSTIC DE L\'APPLICATION');
    console.log('================================');
    console.log('Zone actuelle:', currentZoneData);
    console.log('Bâtiments chargés:', loadedBuildings.length);
    console.log('Carte initialisée:', !!previewMap);
    console.log('Données Malaysia:', Object.keys(malaysiaCitiesData).length, 'villes');
    
    // Vérifier les éléments DOM
    const elements = ['generateBtn', 'previewMap', 'numBuildings', 'startDate', 'endDate', 'results', 'dataPreview'];
    elements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`Élément ${id}:`, element ? '✅' : '❌');
    });
    
    return {
        currentZone: currentZoneData,
        buildingsCount: loadedBuildings.length,
        mapInitialized: !!previewMap,
        citiesLoaded: Object.keys(malaysiaCitiesData).length
    };
}

function testConnection() {
    return fetch('/health')
        .then(response => {
            if (response.ok) {
                showAlert('✅ Connexion serveur OK', 'success');
                return true;
            } else {
                showAlert('❌ Problème de connexion serveur', 'error');
                return false;
            }
        })
        .catch(error => {
            showAlert('❌ Serveur inaccessible', 'error');
            return false;
        });
}

// ==================== INITIALISATION FINALE ====================

// Exposer les fonctions pour le debugging
window.debugApp = debugApp;
window.testConnection = testConnection;
window.loadRealBuildings = loadRealBuildings;
window.downloadJSON = downloadJSON;
window.downloadCSV = downloadCSV;
window.downloadExcel = downloadExcel;

// Message de chargement complet
console.log(`
🇲🇾 GÉNÉRATEUR MALAYSIA - FRONTEND CORRIGÉ
==========================================
✅ Script principal chargé
🗺️ Système de cartographie opérationnel  
📊 Affichage des données corrigé
🔧 Fonctions de débogage disponibles
📥 Système de téléchargement intégré

CORRECTIFS APPLIQUÉS:
- Affichage flexible des données
- Gestion robuste des réponses API
- Cartographie interactive complète
- Extraction sécurisée des statistiques
- Interface utilisateur améliorée

Pour déboguer: debugApp()
Pour tester la connexion: testConnection()

Prêt à générer des données Malaysia! 🚀
`);