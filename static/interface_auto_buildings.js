/**
 * MODIFICATIONS DE L'INTERFACE - NOMBRE AUTOMATIQUE DE BÂTIMENTS
 * Fichier: static/interface_auto_buildings.js
 * 
 * Modifie l'interface pour utiliser automatiquement le nombre réel de bâtiments OSM
 */

// ==================== MODIFICATIONS DE L'INTERFACE ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Application des modifications d\'interface...');
    
    // Modifier le champ nombre de bâtiments
    modifyBuildingsCountField();
    
    // Ajouter le nouveau sélecteur de zones complet
    addCompleteZoneSelector();
    
    // Modifier les textes explicatifs
    updateInterfaceTexts();
    
    // Ajouter les estimations en temps réel
    addRealTimeEstimations();
    
    console.log('✅ Interface modifiée pour utilisation automatique OSM');
});

/**
 * Modifie le champ "nombre de bâtiments" pour l'affichage uniquement
 */
function modifyBuildingsCountField() {
    const numBuildingsContainer = document.getElementById('numBuildings')?.parentElement;
    if (!numBuildingsContainer) return;
    
    // Remplacer le champ par un affichage en lecture seule
    numBuildingsContainer.innerHTML = `
        <label for="actualBuildingsCount">Nombre de bâtiments (automatique) :</label>
        <div class="buildings-count-display">
            <input type="number" id="actualBuildingsCount" class="form-control" 
                   value="0" readonly style="background-color: #f8f9fa; color: #495057; font-weight: bold;">
            <div class="buildings-count-info">
                <small class="form-text text-muted">
                    📊 <strong>Nombre automatique</strong> basé sur les vrais bâtiments OpenStreetMap de la zone sélectionnée
                </small>
                <div id="buildingsSourceInfo" class="mt-1" style="display: none;">
                    <span class="badge badge-success">✅ Données OSM officielles</span>
                    <small class="text-success ml-2">Mise à jour automatique lors du chargement</small>
                </div>
            </div>
        </div>
    `;
}

/**
 * Ajoute un sélecteur complet pour toutes les zones de Malaisie
 */
function addCompleteZoneSelector() {
    const zoneSelectContainer = document.getElementById('zoneSelect')?.parentElement;
    if (!zoneSelectContainer) return;
    
    // Remplacer par le sélecteur complet
    zoneSelectContainer.innerHTML = `
        <label for="completeZoneSelect">Zone géographique complète :</label>
        <select id="completeZoneSelect" class="form-control" aria-describedby="zoneCompleteHelp">
            <option value="">-- Choisir une zone --</option>
            
            <optgroup label="🇲🇾 PAYS ENTIER">
                <option value="Malaysia" data-type="country">Malaysia (Pays entier - ~4.8M bâtiments)</option>
            </optgroup>
            
            <optgroup label="🏛️ ÉTATS PRINCIPAUX">
                <option value="Selangor" data-type="state">Selangor (~980K bâtiments)</option>
                <option value="Johor" data-type="state">Johor (~750K bâtiments)</option>
                <option value="Perak" data-type="state">Perak (~480K bâtiments)</option>
                <option value="Penang" data-type="state">Penang (~420K bâtiments)</option>
                <option value="Sarawak" data-type="state">Sarawak (~410K bâtiments)</option>
                <option value="Sabah" data-type="state">Sabah (~320K bâtiments)</option>
            </optgroup>
            
            <optgroup label="🏙️ VILLES PRINCIPALES">
                <option value="Kuala Lumpur" data-type="city">Kuala Lumpur (~185K bâtiments)</option>
                <option value="George Town" data-type="city">George Town (~45K bâtiments)</option>
                <option value="Shah Alam" data-type="city">Shah Alam (~42K bâtiments)</option>
                <option value="Ipoh" data-type="city">Ipoh (~38K bâtiments)</option>
                <option value="Johor Bahru" data-type="city">Johor Bahru (~35K bâtiments)</option>
                <option value="Kota Kinabalu" data-type="city">Kota Kinabalu (~28K bâtiments)</option>
                <option value="Kuching" data-type="city">Kuching (~22K bâtiments)</option>
            </optgroup>
        </select>
        <small id="zoneCompleteHelp" class="form-text text-info">
            💡 <strong>Nouveau :</strong> Sélectionnez n'importe quelle zone. Le système chargera automatiquement 
            TOUS les vrais bâtiments de cette zone depuis OpenStreetMap.
        </small>
    `;
    
    // Ajouter l'écouteur d'événement
    document.getElementById('completeZoneSelect').addEventListener('change', handleCompleteZoneSelection);
}

/**
 * Met à jour les textes explicatifs de l'interface
 */
function updateInterfaceTexts() {
    // Modifier le titre de la section temporelle
    const temporalTitle = document.querySelector('h3:contains("Configuration temporelle")');
    if (temporalTitle) {
        temporalTitle.innerHTML = '⏰ Configuration temporelle <small class="text-muted">(pour les bâtiments OSM chargés)</small>';
    }
    
    // Ajouter une explication dans la section génération
    const generateCard = document.querySelector('.card-title:contains("Génération des données")');
    if (generateCard) {
        const cardBody = generateCard.closest('.professional-card').querySelector('.card-body');
        
        // Ajouter l'explication avant les boutons
        const explanation = document.createElement('div');
        explanation.className = 'alert alert-info mb-4';
        explanation.innerHTML = `
            <div class="alert-icon">💡</div>
            <div>
                <strong>Nouvelle approche automatique :</strong><br>
                • Sélectionnez une zone géographique (pays, état, ville)<br>
                • Le système charge automatiquement TOUS les vrais bâtiments OSM<br>
                • La génération utilise le nombre exact de bâtiments trouvés<br>
                • Fini les estimations : données 100% basées sur la réalité !
            </div>
        `;
        
        cardBody.insertBefore(explanation, cardBody.firstChild);
    }
}

/**
 * Ajoute les estimations en temps réel
 */
function addRealTimeEstimations() {
    // Créer le panneau d'estimation
    const estimationPanel = document.createElement('div');
    estimationPanel.className = 'professional-card';
    estimationPanel.id = 'estimationPanel';
    estimationPanel.style.display = 'none';
    estimationPanel.innerHTML = `
        <div class="card-header">
            <h3 class="card-title">📊 Estimation en temps réel</h3>
            <div class="card-badge">Données OSM</div>
        </div>
        <div class="card-body">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">🏗️</div>
                    <div class="stat-value" id="estimatedTotalBuildings">-</div>
                    <div class="stat-label">Bâtiments estimés</div>
                    <div class="stat-unit">dans la zone</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-value" id="estimatedLoadTime">-</div>
                    <div class="stat-label">Temps de chargement</div>
                    <div class="stat-unit">estimation</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value" id="estimatedDataSize">-</div>
                    <div class="stat-label">Taille des données</div>
                    <div class="stat-unit">approximative</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📈</div>
                    <div class="stat-value" id="estimatedRecords">-</div>
                    <div class="stat-label">Enregistrements</div>
                    <div class="stat-unit">temporels</div>
                </div>
            </div>
            
            <div class="mt-3">
                <div class="alert alert-warning">
                    <div class="alert-icon">⚠️</div>
                    <div>
                        <strong>Attention :</strong> Les grandes zones (pays entier, grands états) peuvent nécessiter 
                        plusieurs minutes de chargement et générer des datasets volumineux.
                        <br><strong>Recommandation :</strong> Commencez par une ville pour tester.
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insérer après la sélection de zone
    const zoneCard = document.querySelector('.card-title:contains("Configuration de la zone")').closest('.professional-card');
    zoneCard.parentNode.insertBefore(estimationPanel, zoneCard.nextSibling);
}

/**
 * Gère la sélection d'une zone complète
 */
function handleCompleteZoneSelection(event) {
    const selectedZone = event.target.value;
    const selectedOption = event.target.selectedOptions[0];
    
    if (!selectedZone || !window.MALAYSIA_COMPLETE_DATA) {
        hideEstimationPanel();
        return;
    }
    
    const zoneData = window.MALAYSIA_COMPLETE_DATA[selectedZone];
    if (!zoneData) {
        console.warn(`Zone ${selectedZone} non trouvée dans les données`);
        return;
    }
    
    console.log(`📍 Zone sélectionnée: ${selectedZone} (${zoneData.type})`);
    
    // Mettre à jour les variables globales
    window.currentZoneData = {
        name: selectedZone,
        type: zoneData.type,
        ...zoneData
    };
    
    // Afficher l'estimation
    showZoneEstimation(selectedZone, zoneData);
    
    // Mettre à jour l'affichage des informations de zone
    updateZoneInfoDisplay(selectedZone, zoneData);
    
    // Centrer la carte sur la zone
    if (window.previewMap && zoneData.center) {
        const zoomLevel = getZoomLevelForZoneType(zoneData.type);
        window.previewMap.setView(zoneData.center, zoomLevel);
    }
    
    // Réinitialiser le compteur de bâtiments
    resetBuildingsCount();
}

/**
 * Affiche l'estimation pour la zone sélectionnée
 */
function showZoneEstimation(zoneName, zoneData) {
    const estimationPanel = document.getElementById('estimationPanel');
    if (!estimationPanel) return;
    
    estimationPanel.style.display = 'block';
    
    // Calculer les estimations
    const estimatedBuildings = zoneData.estimated_buildings;
    const estimatedLoadTime = Math.ceil(estimatedBuildings / 5000); // ~5000 bâtiments par minute
    const estimatedDataSize = Math.ceil(estimatedBuildings * 2.5 / 1000); // ~2.5KB par bâtiment
    
    // Calculer les enregistrements temporels (basé sur 30 jours par défaut)
    const startDate = document.getElementById('startDate')?.value || '2024-01-01';
    const endDate = document.getElementById('endDate')?.value || '2024-01-31';
    const freq = document.getElementById('freq')?.value || 'D';
    
    const daysDiff = calculateDaysDifference(startDate, endDate);
    const recordsPerBuilding = freq === 'H' ? daysDiff * 24 : daysDiff;
    const estimatedRecords = estimatedBuildings * recordsPerBuilding;
    
    // Mettre à jour l'affichage
    document.getElementById('estimatedTotalBuildings').textContent = estimatedBuildings.toLocaleString();
    document.getElementById('estimatedLoadTime').textContent = `${estimatedLoadTime}min`;
    document.getElementById('estimatedDataSize').textContent = `${estimatedDataSize}MB`;
    document.getElementById('estimatedRecords').textContent = estimatedRecords.toLocaleString();
    
    // Ajouter un indicateur de complexité
    const complexity = getComplexityLevel(estimatedBuildings);
    updateComplexityWarning(complexity, zoneName);
}

/**
 * Met à jour l'affichage des informations de zone
 */
function updateZoneInfoDisplay(zoneName, zoneData) {
    const elements = {
        'zoneNameDisplay': zoneName,
        'zoneTypeDisplay': zoneData.type.replace('_', ' ').toUpperCase(),
        'zonePopulationDisplay': zoneData.population?.toLocaleString() || 'N/A',
        'zoneStateDisplay': zoneData.state || zoneName
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
    
    // Mettre à jour l'estimation OSM
    const estimatedBuildings = document.getElementById('estimatedBuildings');
    const apiStatus = document.getElementById('apiStatus');
    
    if (estimatedBuildings) {
        estimatedBuildings.textContent = zoneData.estimated_buildings.toLocaleString();
    }
    
    if (apiStatus) {
        apiStatus.innerHTML = '🟢 Prêt';
        apiStatus.style.color = '#28a745';
    }
}

/**
 * Réinitialise le compteur de bâtiments
 */
function resetBuildingsCount() {
    const buildingsCount = document.getElementById('actualBuildingsCount');
    const buildingsInfo = document.getElementById('buildingsSourceInfo');
    const loadedCount = document.getElementById('loadedBuildingsCount');
    
    if (buildingsCount) {
        buildingsCount.value = '0';
    }
    
    if (buildingsInfo) {
        buildingsInfo.style.display = 'none';
    }
    
    if (loadedCount) {
        loadedCount.textContent = '0';
    }
}

/**
 * Cache le panneau d'estimation
 */
function hideEstimationPanel() {
    const estimationPanel = document.getElementById('estimationPanel');
    if (estimationPanel) {
        estimationPanel.style.display = 'none';
    }
}

/**
 * Calcule la différence en jours entre deux dates
 */
function calculateDaysDifference(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
}

/**
 * Détermine le niveau de zoom selon le type de zone
 */
function getZoomLevelForZoneType(zoneType) {
    const zoomLevels = {
        'country': 6,
        'state': 8,
        'city': 11,
        'district': 13,
        'village': 14
    };
    
    return zoomLevels[zoneType] || 10;
}

/**
 * Détermine le niveau de complexité
 */
function getComplexityLevel(buildingsCount) {
    if (buildingsCount < 10000) return 'low';
    if (buildingsCount < 100000) return 'medium';
    if (buildingsCount < 500000) return 'high';
    return 'extreme';
}

/**
 * Met à jour l'avertissement de complexité
 */
function updateComplexityWarning(complexity, zoneName) {
    const warningElement = document.querySelector('#estimationPanel .alert-warning div');
    if (!warningElement) return;
    
    const messages = {
        'low': `✅ <strong>Zone recommandée :</strong> ${zoneName} est idéal pour commencer. Chargement rapide et dataset manageable.`,
        'medium': `⚡ <strong>Zone moyenne :</strong> ${zoneName} nécessitera quelques minutes de chargement. Dataset de taille raisonnable.`,
        'high': `⚠️ <strong>Zone importante :</strong> ${zoneName} peut prendre 10-30 minutes à charger. Dataset volumineux (>100MB).`,
        'extreme': `🚨 <strong>Zone très importante :</strong> ${zoneName} peut prendre plus d'une heure à charger. Dataset très volumineux (>1GB). Recommandé uniquement pour l'analyse complète.`
    };
    
    warningElement.innerHTML = messages[complexity];
}

// ==================== INTÉGRATION AVEC LE SYSTÈME EXISTANT ====================

/**
 * Surcharge la fonction de génération pour utiliser le nombre automatique
 */
document.addEventListener('DOMContentLoaded', function() {
    const originalGenerateBtn = document.getElementById('generateBtn');
    if (originalGenerateBtn) {
        originalGenerateBtn.addEventListener('click', function(e) {
            // Vérifier qu'on a des bâtiments chargés
            if (!window.loadedBuildings || window.loadedBuildings.length === 0) {
                e.preventDefault();
                
                if (window.showAlert) {
                    window.showAlert(
                        'Veuillez d\'abord charger les bâtiments OSM de la zone sélectionnée en cliquant sur "Charger bâtiments réels"', 
                        'warning'
                    );
                }
                return false;
            }
            
            console.log(`🚀 Génération avec ${window.loadedBuildings.length} bâtiments OSM réels`);
        });
    }
});

/**
 * Fonction pour mettre à jour le compteur après chargement OSM
 */
window.updateBuildingsCountAfterLoading = function(buildingsCount) {
    const buildingsCountField = document.getElementById('actualBuildingsCount');
    const buildingsInfo = document.getElementById('buildingsSourceInfo');
    
    if (buildingsCountField) {
        buildingsCountField.value = buildingsCount.toLocaleString();
    }
    
    if (buildingsInfo) {
        buildingsInfo.style.display = 'block';
    }
    
    console.log(`✅ Interface mise à jour: ${buildingsCount.toLocaleString()} bâtiments chargés`);
};

// ==================== MESSAGES DE DÉBOGAGE ====================

console.log(`
🔧 INTERFACE MODIFICATIONS CHARGÉES
===================================
✅ Champ "nombre de bâtiments" → lecture seule (automatique)
✅ Sélecteur de zones → complet pour toute la Malaisie
✅ Estimations en temps réel ajoutées
✅ Textes explicatifs mis à jour
✅ Intégration avec le système OSM amélioré

NOUVELLES FONCTIONNALITÉS:
• Sélection de n'importe quelle zone de Malaisie
• Estimation automatique du nombre de bâtiments
• Calcul du temps de chargement estimé
• Avertissements de complexité selon la zone
• Compteur automatique après chargement OSM

L'utilisateur n'a plus besoin de choisir le nombre de bâtiments !
`);