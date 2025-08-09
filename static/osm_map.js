/**
 * Module de cartographie OpenStreetMap 2D
 * Fichier: static/osm_map.js
 * 
 * Intègre une carte interactive avec données OSM réelles
 * pour l'application Malaysia existante
 */

class OSMMapModule {
    constructor() {
        this.map = null;
        this.buildingLayers = {};
        this.currentMarkers = [];
        this.osmData = [];
        this.isInitialized = false;
        
        // Configuration des couleurs et styles par type de bâtiment
        this.buildingStyles = {
            'residential': { color: '#2E8B57', fillColor: '#90EE90', name: 'Résidentiel' },
            'apartments': { color: '#228B22', fillColor: '#98FB98', name: 'Appartements' },
            'house': { color: '#32CD32', fillColor: '#ADFF2F', name: 'Maisons' },
            'commercial': { color: '#4682B4', fillColor: '#87CEEB', name: 'Commercial' },
            'retail': { color: '#1E90FF', fillColor: '#87CEFA', name: 'Commerce de détail' },
            'office': { color: '#708090', fillColor: '#B0C4DE', name: 'Bureaux' },
            'industrial': { color: '#696969', fillColor: '#A9A9A9', name: 'Industriel' },
            'warehouse': { color: '#2F4F4F', fillColor: '#708090', name: 'Entrepôts' },
            'factory': { color: '#191970', fillColor: '#6495ED', name: 'Usines' },
            'hospital': { color: '#DC143C', fillColor: '#FFB6C1', name: 'Hôpitaux' },
            'clinic': { color: '#FF1493', fillColor: '#FFC0CB', name: 'Cliniques' },
            'school': { color: '#9932CC', fillColor: '#DDA0DD', name: 'Écoles' },
            'university': { color: '#8B008B', fillColor: '#DA70D6', name: 'Universités' },
            'hotel': { color: '#FF8C00', fillColor: '#FFDF7F', name: 'Hôtels' },
            'restaurant': { color: '#FF6347', fillColor: '#FFA07A', name: 'Restaurants' },
            'church': { color: '#8B4513', fillColor: '#D2B48C', name: 'Églises' },
            'mosque': { color: '#006400', fillColor: '#7CFC00', name: 'Mosquées' },
            'temple': { color: '#B8860B', fillColor: '#F0E68C', name: 'Temples' },
            'default': { color: '#808080', fillColor: '#D3D3D3', name: 'Autres bâtiments' }
        };
        
        // Configuration OSM
        this.config = {
            overpassUrl: 'https://overpass-api.de/api/interpreter',
            nominatimUrl: 'https://nominatim.openstreetmap.org',
            defaultCenter: [3.1390, 101.6869], // Kuala Lumpur
            defaultZoom: 13,
            maxRadius: 2000,
            requestTimeout: 30000
        };
        
        console.log('🗺️ OSM Map Module - Initialisé');
    }

    /**
     * Initialisation de la carte et de l'interface
     */
    async initialize() {
        try {
            this.createMapInterface();
            await this.initializeLeafletMap();
            this.createLegend();
            this.setupEventListeners();
            
            this.isInitialized = true;
            console.log('✅ Carte OSM initialisée avec succès');
            
            return true;
        } catch (error) {
            console.error('❌ Erreur initialisation carte:', error);
            return false;
        }
    }

    /**
     * Création de l'interface cartographique dans le DOM existant
     */
    createMapInterface() {
        // Chercher où insérer la carte dans l'interface existante
        const resultsDiv = document.getElementById('results');
        if (!resultsDiv) {
            throw new Error('Element results non trouvé');
        }

        // Créer le conteneur de la carte
        const mapContainer = document.createElement('div');
        mapContainer.id = 'osmMapContainer';
        mapContainer.innerHTML = `
            <div class="map-section">
                <div class="map-header">
                    <h3><span class="map-icon">🗺️</span> Cartographie des Bâtiments</h3>
                    <div class="map-controls">
                        <button id="loadOSMData" class="btn btn-primary">
                            📡 Charger données OSM
                        </button>
                        <button id="showAllBuildings" class="btn btn-secondary">
                            👁️ Tout afficher
                        </button>
                        <button id="clearMap" class="btn btn-outline">
                            🧹 Effacer
                        </button>
                    </div>
                </div>
                
                <div class="map-wrapper">
                    <div id="leafletMap" class="leaflet-map"></div>
                    <div id="mapLegend" class="map-legend"></div>
                </div>
                
                <div class="map-status">
                    <div id="mapStatusText" class="status-text">
                        Prêt à charger les données OSM
                    </div>
                    <div id="buildingCounter" class="building-counter">
                        <span id="buildingCount">0</span> bâtiments affichés
                    </div>
                </div>
            </div>
        `;

        // Insérer au début des résultats
        resultsDiv.insertBefore(mapContainer, resultsDiv.firstChild);
        
        // Ajouter les styles CSS
        this.addMapStyles();
    }

    /**
     * Ajout des styles CSS pour la carte
     */
    addMapStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* === STYLES CARTE OSM === */
            .map-section {
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                margin: 20px 0;
                overflow: hidden;
                border: 1px solid #e0e6ed;
            }

            .map-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 15px;
            }

            .map-header h3 {
                margin: 0;
                font-size: 1.3em;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .map-icon {
                font-size: 1.2em;
            }

            .map-controls {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }

            .map-controls .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-size: 0.9em;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                white-space: nowrap;
            }

            .map-controls .btn-primary {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
            }

            .map-controls .btn-primary:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-1px);
            }

            .map-controls .btn-secondary {
                background: rgba(255,255,255,0.15);
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
            }

            .map-controls .btn-outline {
                background: transparent;
                color: white;
                border: 1px solid rgba(255,255,255,0.4);
            }

            .map-wrapper {
                position: relative;
                height: 500px;
                display: flex;
            }

            .leaflet-map {
                flex: 1;
                height: 100%;
                border: none;
            }

            .map-legend {
                width: 280px;
                background: #f8f9fa;
                border-left: 1px solid #e0e6ed;
                padding: 15px;
                overflow-y: auto;
                font-size: 0.9em;
            }

            .legend-title {
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #3498db;
                font-size: 1em;
            }

            .legend-item {
                display: flex;
                align-items: center;
                margin-bottom: 8px;
                padding: 5px;
                border-radius: 5px;
                transition: background 0.2s ease;
                cursor: pointer;
            }

            .legend-item:hover {
                background: #e9ecef;
            }

            .legend-color {
                width: 20px;
                height: 20px;
                border-radius: 3px;
                margin-right: 10px;
                border: 2px solid #333;
                flex-shrink: 0;
            }

            .legend-label {
                font-weight: 500;
                color: #34495e;
            }

            .legend-count {
                margin-left: auto;
                background: #6c757d;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 600;
                min-width: 25px;
                text-align: center;
            }

            .map-status {
                background: #f8f9fa;
                padding: 12px 20px;
                border-top: 1px solid #e0e6ed;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 10px;
            }

            .status-text {
                color: #6c757d;
                font-size: 0.9em;
            }

            .building-counter {
                background: #007bff;
                color: white;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 0.9em;
                font-weight: 600;
            }

            .building-counter #buildingCount {
                font-weight: bold;
                font-size: 1.1em;
            }

            /* Responsive */
            @media (max-width: 768px) {
                .map-wrapper {
                    flex-direction: column;
                    height: auto;
                }
                
                .leaflet-map {
                    height: 400px;
                }
                
                .map-legend {
                    width: 100%;
                    max-height: 200px;
                    border-left: none;
                    border-top: 1px solid #e0e6ed;
                }
                
                .map-header {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .map-controls {
                    justify-content: center;
                }
                
                .map-status {
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                }
            }

            /* Styles pour les popups Leaflet */
            .building-popup {
                font-size: 0.9em;
                line-height: 1.4;
            }

            .building-popup .popup-title {
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 8px;
                font-size: 1em;
            }

            .building-popup .popup-info {
                margin-bottom: 5px;
            }

            .building-popup .popup-label {
                font-weight: 500;
                color: #7f8c8d;
            }
        `;
        
        document.head.appendChild(style);
    }

    /**
     * Initialisation de la carte Leaflet
     */
    async initializeLeafletMap() {
        const mapElement = document.getElementById('leafletMap');
        if (!mapElement) {
            throw new Error('Element leafletMap non trouvé');
        }

        // Initialiser la carte Leaflet
        this.map = L.map('leafletMap').setView(this.config.defaultCenter, this.config.defaultZoom);

        // Ajouter la couche de tuiles OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);

        // Initialiser les groupes de couches pour chaque type de bâtiment
        for (const buildingType in this.buildingStyles) {
            this.buildingLayers[buildingType] = L.layerGroup().addTo(this.map);
        }

        console.log('✅ Carte Leaflet initialisée');
    }

    /**
     * Création de la légende interactive
     */
    createLegend() {
        const legendElement = document.getElementById('mapLegend');
        if (!legendElement) return;

        legendElement.innerHTML = `
            <div class="legend-title">Types de Bâtiments</div>
            <div id="legendItems"></div>
        `;

        this.updateLegend();
    }

    /**
     * Mise à jour de la légende avec compteurs
     */
    updateLegend() {
        const legendItems = document.getElementById('legendItems');
        if (!legendItems) return;

        let legendHTML = '';
        
        for (const [type, style] of Object.entries(this.buildingStyles)) {
            const count = this.buildingLayers[type] ? this.buildingLayers[type].getLayers().length : 0;
            
            legendHTML += `
                <div class="legend-item" data-building-type="${type}">
                    <div class="legend-color" style="background-color: ${style.fillColor}; border-color: ${style.color};"></div>
                    <span class="legend-label">${style.name}</span>
                    <span class="legend-count">${count}</span>
                </div>
            `;
        }
        
        legendItems.innerHTML = legendHTML;

        // Ajouter les événements de clic pour toggle des couches
        legendItems.querySelectorAll('.legend-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const buildingType = e.currentTarget.dataset.buildingType;
                this.toggleBuildingLayer(buildingType);
            });
        });
    }

    /**
     * Configuration des écouteurs d'événements
     */
    setupEventListeners() {
        // Bouton de chargement des données OSM
        const loadButton = document.getElementById('loadOSMData');
        if (loadButton) {
            loadButton.addEventListener('click', () => this.loadOSMDataForCurrentView());
        }

        // Bouton d'affichage de tous les bâtiments
        const showAllButton = document.getElementById('showAllBuildings');
        if (showAllButton) {
            showAllButton.addEventListener('click', () => this.showAllBuildingLayers());
        }

        // Bouton d'effacement
        const clearButton = document.getElementById('clearMap');
        if (clearButton) {
            clearButton.addEventListener('click', () => this.clearAllBuildings());
        }

        // Intégration avec l'application principale - écouter la génération de données
        if (window.generateData) {
            const originalGenerateData = window.generateData;
            window.generateData = async () => {
                const result = await originalGenerateData();
                // Après génération, proposer de charger les données OSM pour les localisations
                if (result && this.isInitialized) {
                    this.handleGeneratedData(result);
                }
                return result;
            };
        }
    }

    /**
     * Chargement des données OSM pour la vue actuelle
     */
    async loadOSMDataForCurrentView() {
        const bounds = this.map.getBounds();
        const center = this.map.getCenter();
        
        // Calculer le rayon approximatif de la vue
        const radius = Math.min(
            center.distanceTo(bounds.getNorthWest()),
            this.config.maxRadius
        );

        await this.loadOSMData(center.lat, center.lng, radius);
    }

    /**
     * Récupération des données OpenStreetMap
     */
    async loadOSMData(lat, lon, radius) {
        this.updateStatus('🔄 Chargement des données OSM...');
        
        const query = `
            [out:json][timeout:${this.config.requestTimeout / 1000}];
            (
                way["building"](around:${Math.round(radius)},${lat},${lon});
                relation["building"](around:${Math.round(radius)},${lat},${lon});
            );
            out geom;
        `;

        try {
            const response = await fetch(this.config.overpassUrl, {
                method: 'POST',
                body: query,
                headers: {
                    'Content-Type': 'text/plain'
                }
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            this.osmData = data.elements || [];
            
            console.log(`📊 ${this.osmData.length} bâtiments OSM récupérés`);
            
            // Traiter et afficher les bâtiments
            this.processOSMBuildings();
            this.updateStatus(`✅ ${this.osmData.length} bâtiments chargés depuis OSM`);
            
        } catch (error) {
            console.error('❌ Erreur chargement OSM:', error);
            this.updateStatus('❌ Erreur de chargement OSM - Utilisation du fallback');
            
            // Fallback: générer des bâtiments de démonstration
            this.generateFallbackBuildings(lat, lon, radius);
        }
    }

    /**
     * Traitement et affichage des bâtiments OSM
     */
    processOSMBuildings() {
        // Effacer les bâtiments existants
        this.clearAllBuildings();

        let processedCount = 0;
        
        this.osmData.forEach(element => {
            if (element.geometry && element.geometry.length > 2) {
                const buildingPolygon = this.createBuildingPolygon(element);
                if (buildingPolygon) {
                    processedCount++;
                }
            }
        });

        // Mettre à jour la légende et les compteurs
        this.updateLegend();
        this.updateBuildingCounter();
        
        console.log(`✅ ${processedCount} bâtiments affichés sur la carte`);
    }

    /**
     * Création d'un polygone de bâtiment sur la carte
     */
    createBuildingPolygon(element) {
        try {
            // Extraire les coordonnées
            const coordinates = element.geometry.map(point => [point.lat, point.lon]);
            
            // Déterminer le type de bâtiment
            const buildingType = this.getBuildingType(element.tags);
            const style = this.buildingStyles[buildingType];
            
            // Créer le polygone
            const polygon = L.polygon(coordinates, {
                color: style.color,
                fillColor: style.fillColor,
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.6
            });

            // Ajouter le popup avec informations
            const popupContent = this.createBuildingPopup(element, buildingType);
            polygon.bindPopup(popupContent);

            // Ajouter à la couche appropriée
            polygon.addTo(this.buildingLayers[buildingType]);

            return polygon;
            
        } catch (error) {
            console.warn('Erreur création polygone:', error);
            return null;
        }
    }

    /**
     * Détermination du type de bâtiment à partir des tags OSM
     */
    getBuildingType(tags) {
        if (!tags || !tags.building) return 'default';

        // Mapping des types OSM vers nos catégories
        const buildingType = tags.building.toLowerCase();
        
        // Types exacts
        if (this.buildingStyles[buildingType]) {
            return buildingType;
        }
        
        // Correspondances spéciales
        const mappings = {
            'yes': 'default',
            'house': 'residential',
            'detached': 'house',
            'terrace': 'residential',
            'semidetached_house': 'house',
            'bungalow': 'house',
            'static_caravan': 'residential',
            'shop': 'retail',
            'supermarket': 'retail',
            'mall': 'commercial',
            'department_store': 'retail',
            'pharmacy': 'clinic',
            'doctors': 'clinic',
            'dentist': 'clinic',
            'veterinary': 'clinic',
            'kindergarten': 'school',
            'college': 'university',
            'polytechnic': 'university',
            'library': 'school',
            'place_of_worship': 'church',
            'cathedral': 'church',
            'chapel': 'church',
            'synagogue': 'church',
            'monastery': 'church',
            'shrine': 'temple',
            'civic': 'office',
            'government': 'office',
            'public': 'office',
            'fire_station': 'office',
            'police': 'office',
            'courthouse': 'office',
            'townhall': 'office',
            'embassy': 'office'
        };
        
        return mappings[buildingType] || 'default';
    }

    /**
     * Création du contenu popup pour un bâtiment
     */
    createBuildingPopup(element, buildingType) {
        const tags = element.tags || {};
        const style = this.buildingStyles[buildingType];
        
        let content = `<div class="building-popup">`;
        content += `<div class="popup-title">${style.name}</div>`;
        
        // Informations principales
        if (tags.name) {
            content += `<div class="popup-info"><span class="popup-label">Nom:</span> ${tags.name}</div>`;
        }
        
        if (tags.building && tags.building !== 'yes') {
            content += `<div class="popup-info"><span class="popup-label">Type:</span> ${tags.building}</div>`;
        }
        
        // Informations d'adresse
        if (tags['addr:street'] || tags['addr:housenumber']) {
            const address = [
                tags['addr:housenumber'],
                tags['addr:street'],
                tags['addr:city']
            ].filter(Boolean).join(' ');
            
            if (address) {
                content += `<div class="popup-info"><span class="popup-label">Adresse:</span> ${address}</div>`;
            }
        }
        
        // Informations sur la hauteur
        if (tags.height) {
            content += `<div class="popup-info"><span class="popup-label">Hauteur:</span> ${tags.height}</div>`;
        }
        
        if (tags['building:levels']) {
            content += `<div class="popup-info"><span class="popup-label">Étages:</span> ${tags['building:levels']}</div>`;
        }
        
        // ID OSM
        content += `<div class="popup-info"><span class="popup-label">ID OSM:</span> ${element.id}</div>`;
        
        content += `</div>`;
        
        return content;
    }

    /**
     * Génération de bâtiments de fallback
     */
    generateFallbackBuildings(lat, lon, radius) {
        console.log('🔄 Génération de bâtiments de fallback...');
        
        const buildingCount = Math.min(50, Math.max(10, Math.round(radius / 50)));
        const types = Object.keys(this.buildingStyles).filter(t => t !== 'default');
        
        for (let i = 0; i < buildingCount; i++) {
            // Position aléatoire dans le rayon
            const angle = Math.random() * 2 * Math.PI;
            const distance = Math.random() * radius * 0.8;
            
            const offsetLat = (distance * Math.cos(angle)) / 111320; // Approximation mètres -> degrés
            const offsetLon = (distance * Math.sin(angle)) / (111320 * Math.cos(lat * Math.PI / 180));
            
            const buildingLat = lat + offsetLat;
            const buildingLon = lon + offsetLon;
            
            // Créer un petit polygone carré
            const size = 0.0001; // Taille approximative
            const coordinates = [
                [buildingLat - size, buildingLon - size],
                [buildingLat - size, buildingLon + size],
                [buildingLat + size, buildingLon + size],
                [buildingLat + size, buildingLon - size]
            ];
            
            // Type aléatoire
            const buildingType = types[Math.floor(Math.random() * types.length)];
            const style = this.buildingStyles[buildingType];
            
            // Créer le polygone
            const polygon = L.polygon(coordinates, {
                color: style.color,
                fillColor: style.fillColor,
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.6
            });
            
            // Popup simple
            polygon.bindPopup(`
                <div class="building-popup">
                    <div class="popup-title">${style.name} (Fallback)</div>
                    <div class="popup-info"><span class="popup-label">Type:</span> ${buildingType}</div>
                    <div class="popup-info"><span class="popup-label">Source:</span> Génération automatique</div>
                </div>
            `);
            
            polygon.addTo(this.buildingLayers[buildingType]);
        }
        
        this.updateLegend();
        this.updateBuildingCounter();
        this.updateStatus(`✅ ${buildingCount} bâtiments générés (mode fallback)`);
    }

    /**
     * Toggle d'affichage d'une couche de bâtiments
     */
    toggleBuildingLayer(buildingType) {
        const layer = this.buildingLayers[buildingType];
        if (!layer) return;
        
        if (this.map.hasLayer(layer)) {
            this.map.removeLayer(layer);
        } else {
            this.map.addLayer(layer);
        }
    }

    /**
     * Affichage de toutes les couches de bâtiments
     */
    showAllBuildingLayers() {
        for (const layer of Object.values(this.buildingLayers)) {
            if (!this.map.hasLayer(layer)) {
                this.map.addLayer(layer);
            }
        }
    }

    /**
     * Effacement de tous les bâtiments
     */
    clearAllBuildings() {
        for (const layer of Object.values(this.buildingLayers)) {
            layer.clearLayers();
        }
        this.updateLegend();
        this.updateBuildingCounter();
        this.updateStatus('🧹 Carte effacée');
    }

    /**
     * Mise à jour du compteur de bâtiments
     */
    updateBuildingCounter() {
        const countElement = document.getElementById('buildingCount');
        if (!countElement) return;
        
        let totalBuildings = 0;
        for (const layer of Object.values(this.buildingLayers)) {
            totalBuildings += layer.getLayers().length;
        }
        
        countElement.textContent = totalBuildings;
    }

    /**
     * Mise à jour du statut
     */
    updateStatus(message) {
        const statusElement = document.getElementById('mapStatusText');
        if (statusElement) {
            statusElement.textContent = message;
        }
        console.log('🗺️ Status:', message);
    }

    /**
     * Gestion des données générées par l'application principale
     */
    handleGeneratedData(data) {
        if (!data || !data.location_analysis) return;
        
        // Centrer la carte sur la première ville générée
        const firstLocation = data.location_analysis[0];
        if (firstLocation && firstLocation.location) {
            this.centerMapOnLocation(firstLocation.location);
        }
    }

    /**
     * Centrage de la carte sur une localisation
     */
    async centerMapOnLocation(locationName) {
        try {
            const response = await fetch(
                `${this.config.nominatimUrl}/search?format=json&q=${encodeURIComponent(locationName + ', Malaysia')}&limit=1`
            );
            
            const data = await response.json();
            if (data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                
                this.map.setView([lat, lon], 14);
                this.updateStatus(`📍 Centré sur ${locationName}`);
                
                // Proposer de charger les données OSM
                setTimeout(() => {
                    if (confirm(`Voulez-vous charger les bâtiments OSM pour ${locationName} ?`)) {
                        this.loadOSMData(lat, lon, 1000);
                    }
                }, 1000);
            }
        } catch (error) {
            console.error('Erreur géocodage:', error);
            this.updateStatus('❌ Impossible de localiser la ville');
        }
    }

    /**
     * Recherche et affichage d'une ville spécifique
     */
    async searchAndDisplayCity(cityName) {
        try {
            this.updateStatus(`🔍 Recherche de ${cityName}...`);
            
            const response = await fetch(
                `${this.config.nominatimUrl}/search?format=json&q=${encodeURIComponent(cityName + ', Malaysia')}&limit=1&addressdetails=1`
            );
            
            const data = await response.json();
            if (data.length === 0) {
                throw new Error('Ville non trouvée');
            }
            
            const result = data[0];
            const lat = parseFloat(result.lat);
            const lon = parseFloat(result.lon);
            
            // Centrer la carte
            this.map.setView([lat, lon], 15);
            
            // Ajouter un marqueur pour la ville
            const cityMarker = L.marker([lat, lon])
                .addTo(this.map)
                .bindPopup(`
                    <div class="building-popup">
                        <div class="popup-title">${result.display_name}</div>
                        <div class="popup-info"><span class="popup-label">Coordonnées:</span> ${lat.toFixed(4)}, ${lon.toFixed(4)}</div>
                        <div class="popup-info"><span class="popup-label">Type:</span> ${result.type}</div>
                    </div>
                `)
                .openPopup();
            
            // Charger automatiquement les bâtiments OSM
            await this.loadOSMData(lat, lon, 1500);
            
            return { lat, lon, name: cityName };
            
        } catch (error) {
            console.error('Erreur recherche ville:', error);
            this.updateStatus(`❌ Erreur recherche: ${error.message}`);
            return null;
        }
    }

    /**
     * Export des données de la carte
     */
    exportMapData() {
        const exportData = {
            timestamp: new Date().toISOString(),
            center: this.map.getCenter(),
            zoom: this.map.getZoom(),
            bounds: this.map.getBounds(),
            buildings: []
        };
        
        // Collecter les données de tous les bâtiments
        for (const [type, layer] of Object.entries(this.buildingLayers)) {
            layer.eachLayer(building => {
                if (building.getLatLngs) {
                    exportData.buildings.push({
                        type: type,
                        coordinates: building.getLatLngs(),
                        popupContent: building.getPopup() ? building.getPopup().getContent() : null
                    });
                }
            });
        }
        
        return exportData;
    }

    /**
     * Statistiques de la carte
     */
    getMapStatistics() {
        const stats = {
            totalBuildings: 0,
            buildingsByType: {},
            mapCenter: this.map.getCenter(),
            mapZoom: this.map.getZoom(),
            hasOSMData: this.osmData.length > 0,
            osmDataCount: this.osmData.length
        };
        
        for (const [type, layer] of Object.entries(this.buildingLayers)) {
            const count = layer.getLayers().length;
            stats.buildingsByType[type] = count;
            stats.totalBuildings += count;
        }
        
        return stats;
    }
}

// === FONCTIONS D'INTÉGRATION AVEC L'APPLICATION PRINCIPALE ===

/**
 * Initialisation du module OSM Map
 */
let osmMapModule = null;

async function initializeOSMMap() {
    try {
        // Vérifier que Leaflet est chargé
        if (typeof L === 'undefined') {
            console.warn('⚠️ Leaflet non chargé, chargement en cours...');
            await loadLeafletLibrary();
        }
        
        osmMapModule = new OSMMapModule();
        const success = await osmMapModule.initialize();
        
        if (success) {
            console.log('✅ Module OSM Map initialisé avec succès');
            
            // Exposer l'API globalement
            window.osmMap = {
                module: osmMapModule,
                searchCity: (cityName) => osmMapModule.searchAndDisplayCity(cityName),
                loadOSMData: (lat, lon, radius) => osmMapModule.loadOSMData(lat, lon, radius),
                clearMap: () => osmMapModule.clearAllBuildings(),
                exportData: () => osmMapModule.exportMapData(),
                getStats: () => osmMapModule.getMapStatistics(),
                centerOn: (lat, lon, zoom = 15) => osmMapModule.map.setView([lat, lon], zoom)
            };
            
            return osmMapModule;
        } else {
            throw new Error('Échec de l\'initialisation');
        }
        
    } catch (error) {
        console.error('❌ Erreur initialisation OSM Map:', error);
        return null;
    }
}

/**
 * Chargement dynamique de Leaflet si nécessaire
 */
async function loadLeafletLibrary() {
    return new Promise((resolve, reject) => {
        // CSS Leaflet
        const cssLink = document.createElement('link');
        cssLink.rel = 'stylesheet';
        cssLink.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(cssLink);
        
        // JS Leaflet
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = () => {
            console.log('✅ Leaflet chargé dynamiquement');
            resolve();
        };
        script.onerror = () => {
            console.error('❌ Erreur chargement Leaflet');
            reject(new Error('Impossible de charger Leaflet'));
        };
        document.head.appendChild(script);
    });
}

/**
 * Fonction d'aide pour intégrer avec l'application existante
 */
function integrateWithMainApp() {
    // Écouter l'événement DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeOSMMap);
    } else {
        // DOM déjà chargé
        setTimeout(initializeOSMMap, 100);
    }
    
    // Ajouter une fonction à l'objet window pour diagnostics
    window.debugOSMMap = function() {
        if (!osmMapModule) {
            console.log('❌ Module OSM Map non initialisé');
            return;
        }
        
        const stats = osmMapModule.getMapStatistics();
        console.log('📊 Statistiques de la carte OSM:', stats);
        
        console.log('🗺️ État du module:', {
            initialized: osmMapModule.isInitialized,
            hasMap: !!osmMapModule.map,
            osmDataLoaded: osmMapModule.osmData.length,
            totalLayers: Object.keys(osmMapModule.buildingLayers).length,
            visibleLayers: Object.entries(osmMapModule.buildingLayers)
                .filter(([, layer]) => osmMapModule.map.hasLayer(layer))
                .map(([type]) => type)
        });
        
        return stats;
    };
}

// === API PUBLIQUE ===

/**
 * Fonctions exposées globalement
 */
window.OSMMapAPI = {
    /**
     * Initialise le module de carte
     */
    initialize: initializeOSMMap,
    
    /**
     * Recherche et affiche une ville
     */
    searchCity: function(cityName) {
        if (osmMapModule) {
            return osmMapModule.searchAndDisplayCity(cityName);
        }
        console.warn('Module OSM Map non initialisé');
        return null;
    },
    
    /**
     * Charge les données OSM pour une zone
     */
    loadOSMData: function(lat, lon, radius = 1000) {
        if (osmMapModule) {
            return osmMapModule.loadOSMData(lat, lon, radius);
        }
        console.warn('Module OSM Map non initialisé');
        return null;
    },
    
    /**
     * Centre la carte sur des coordonnées
     */
    centerMap: function(lat, lon, zoom = 15) {
        if (osmMapModule && osmMapModule.map) {
            osmMapModule.map.setView([lat, lon], zoom);
            return true;
        }
        return false;
    },
    
    /**
     * Efface tous les bâtiments de la carte
     */
    clearBuildings: function() {
        if (osmMapModule) {
            osmMapModule.clearAllBuildings();
            return true;
        }
        return false;
    },
    
    /**
     * Retourne les statistiques de la carte
     */
    getStatistics: function() {
        if (osmMapModule) {
            return osmMapModule.getMapStatistics();
        }
        return null;
    },
    
    /**
     * Vérifie si le module est prêt
     */
    isReady: function() {
        return osmMapModule && osmMapModule.isInitialized;
    },
    
    /**
     * Export des données de la carte
     */
    exportData: function() {
        if (osmMapModule) {
            return osmMapModule.exportMapData();
        }
        return null;
    }
};

// Auto-initialisation
integrateWithMainApp();

// Message de chargement
console.log(`
🗺️ OSM MAP INTEGRATION - MODULE CHARGÉ
======================================
✅ Cartographie 2D avec données OpenStreetMap réelles
🏗️ Légende interactive par types de bâtiments
🎯 Intégration avec l'application Malaysia existante
🔧 Système de fallback automatique
📍 Géocodage et recherche de villes
🎨 Interface professionnelle responsive

API disponible:
- window.OSMMapAPI.initialize()
- window.OSMMapAPI.searchCity(cityName)
- window.OSMMapAPI.loadOSMData(lat, lon, radius)
- window.OSMMapAPI.centerMap(lat, lon, zoom)
- window.OSMMapAPI.clearBuildings()
- window.OSMMapAPI.getStatistics()
- window.debugOSMMap()

Le module s'initialise automatiquement au chargement de la page.
Prêt pour l'intégration! 🚀
`);