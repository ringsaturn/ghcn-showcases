// Map manager
class MapManager {
  constructor() {
    this.map = null;
    this.baseLayer = null;
    this.init();
  }

  init() {
    // Initialize map, set center and zoom level
    this.map = L.map("map").setView([35, 130], 5); // Set view center in East China Sea area to see both China and Japan
    this.updateMapLanguage();
  }

  updateMapLanguage() {
    const currentLang = window.languageManager.getCurrentLang();

    // If map layer already exists, remove it
    if (this.baseLayer) {
      this.map.removeLayer(this.baseLayer);
    }

    // Create new map layer
    this.baseLayer = protomapsL.leafletLayer({
      url:
        "https://api.protomaps.com/tiles/v4/{z}/{x}/{y}.mvt?key=019532177fa38e19",
      flavor: "white",
      attribution:
        '© <a href="https://protomaps.com">Protomaps</a> © <a href="https://openstreetmap.org">OpenStreetMap</a>',
      lang: currentLang === "zh" ? "zh" : currentLang === "ja" ? "ja" : "en",
    });
    this.baseLayer.addTo(this.map);
  }

  getMap() {
    return this.map;
  }
}

// Create global map manager instance
window.mapManager = new MapManager();
