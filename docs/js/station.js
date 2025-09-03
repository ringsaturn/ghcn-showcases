// Station manager
class StationManager {
  constructor() {
    this.stationFeatures = [];
    this.markersMap = new Map(); // 按ID存储标记
    this.stationsLayer = L.layerGroup();
    this.heatmapLayer = null;
    this.init();
  }

  init() {
    // Initialize global variables to maintain compatibility
    window.stationsLayer = this.stationsLayer;
    window.heatmapLayer = this.heatmapLayer;
    window.stationFeatures = this.stationFeatures;
    window.markersMap = this.markersMap;

    this.setupMapEvents();
    this.loadStationData();
  }

  setupMapEvents() {
    const map = window.mapManager.getMap();
    // Add event listeners for map movement and zoom
    map.on("moveend", () => this.updateVisibleMarkers());
    map.on("zoomend", () => this.updateVisibleMarkers());
  }

  // Check if a point is within the current map bounds
  isPointInBounds(coords, bounds) {
    return bounds.contains(L.latLng(coords[1], coords[0]));
  }

  // Update visible markers based on bounds and zoom level
  updateVisibleMarkers() {
    const map = window.mapManager.getMap();
    const zoomLevel = map.getZoom();
    const bounds = map.getBounds();

    if (zoomLevel >= 10) {
      // Show markers in view, hide heatmap
      if (this.heatmapLayer) {
        map.removeLayer(this.heatmapLayer);
      }

      // Don't clear all layers, instead manage them individually
      const markersToShow = new Set();

      // Add only markers in current view
      this.stationFeatures.forEach((feature) => {
        // Skip stations with MISSING property set to true
        if (feature.properties.MISSING === true) {
          return;
        }
        
        const coords = feature.geometry.coordinates;
        if (this.isPointInBounds(coords, bounds)) {
          markersToShow.add(feature.properties.ID);
          let marker = this.markersMap.get(feature.properties.ID);

          if (!marker) {
            // Create marker if it doesn't exist
            marker = L.marker([coords[1], coords[0]]);
            marker.feature = feature;

            marker.bindPopup(
              window.popupManager.generatePopupContent(feature),
              {
                closeButton: true,
                autoPan: true,
                keepInView: true,
                maxWidth: 800,
              },
            );

            marker.on("popupopen", () => {
              setTimeout(
                () => window.chartManager.loadChartData(feature.properties.ID),
                200,
              );
            });

            this.markersMap.set(feature.properties.ID, marker);
          }

          // Only add if not already in layer
          if (!this.stationsLayer.hasLayer(marker)) {
            this.stationsLayer.addLayer(marker);
          }
        }
      });

      // Remove markers that are no longer in view
      this.stationsLayer.eachLayer((layer) => {
        if (layer.feature && !markersToShow.has(layer.feature.properties.ID)) {
          this.stationsLayer.removeLayer(layer);
        }
      });

      this.stationsLayer.addTo(map);
    } else {
      // Show heatmap, hide markers
      if (!this.heatmapLayer) {
        const heatData = this.stationFeatures
          .filter((feature) => feature.properties.MISSING !== true) // Filter out stations with MISSING = true
          .map((feature) => {
            const coords = feature.geometry.coordinates;
            return [coords[1], coords[0], 1]; // lat, lng, intensity
          });
        this.heatmapLayer = L.heatLayer(heatData, {
          radius: 10, // Reduce heat point radius
          blur: 10, // Increase blur effect
          maxZoom: 10,
          minOpacity: 0.3, // Set minimum opacity
          max: 2.0, // Increase max value to reduce red areas
          gradient: {
            0.2: "blue",
            0.4: "cyan",
            0.6: "lime",
            0.8: "yellow",
            1: "red",
          }, // Use more color transitions
        }).addTo(map);

        // Update global variable
        window.heatmapLayer = this.heatmapLayer;
      } else {
        this.heatmapLayer.addTo(map);
      }
      map.removeLayer(this.stationsLayer);
    }
  }

  // Parse URL query parameters
  getQueryParams() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split("&");

    for (let i = 0; i < pairs.length; i++) {
      const pair = pairs[i].split("=");
      if (pair[0]) {
        params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || "");
      }
    }
    return params;
  }

  // Find and open station by ID
  findAndOpenStation(stationId) {
    const feature = this.stationFeatures.find((f) =>
      f.properties.ID === stationId
    );
    if (feature) {
      const coords = feature.geometry.coordinates;
      const map = window.mapManager.getMap();
      map.setView([coords[1], coords[0]], 10);

      // Wait for the next moveend event to ensure the marker is created
      setTimeout(() => {
        const marker = this.markersMap.get(stationId);
        if (marker) {
          marker.openPopup();
        }
      }, 100);

      return true;
    }
    return false;
  }

  // Load station data
  loadStationData() {
    fetch("./matched_stations.geojson")
      .then((response) => response.json())
      .then((data) => {
        this.stationFeatures = data.features;
        window.stationFeatures = this.stationFeatures; // Update global variable

        // Initial visualization based on current view
        this.updateVisibleMarkers();

        // Check for station_id in URL and navigate to it
        const params = this.getQueryParams();
        if (params.station_id) {
          const found = this.findAndOpenStation(params.station_id);
          if (!found) {
            console.warn("Station with ID " + params.station_id + " not found");
          }
        }
      });
  }
}

// Create global station manager instance
window.stationManager = new StationManager();
