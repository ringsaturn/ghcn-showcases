// Language switching functionality
class LanguageManager {
  constructor() {
    this.currentLang = window.GHCNConfig.getInitialLanguage();
    this.init();
  }

  init() {
    document.addEventListener("DOMContentLoaded", () => {
      this.updateLanguageDisplay();
    });
  }

  updateLanguageDisplay() {
    if (this.currentLang === "zh") {
      document.getElementById("langText").textContent = "EN";
    } else if (this.currentLang === "en") {
      document.getElementById("langText").textContent = "JP";
    } else {
      document.getElementById("langText").textContent = "中";
    }
    // Update HTML document language attribute
    document.documentElement.lang = this.currentLang;
    // Update data source note
    const dsEl = document.getElementById("dataSourceNote");
    if (dsEl) {
      dsEl.innerHTML = window.GHCNConfig.translations[this.currentLang].dataSource || "";
    }
  }

  toggleLanguage() {
    // Rotate through languages: zh -> en -> ja -> zh
    if (this.currentLang === "zh") {
      this.currentLang = "en";
    } else if (this.currentLang === "en") {
      this.currentLang = "ja";
    } else {
      this.currentLang = "zh";
    }

    this.updateLanguageDisplay();

    // Update map language
    if (window.mapManager) {
      window.mapManager.updateMapLanguage();
    }
    
    // Update popup content for all markers
    if (window.stationsLayer) {
      window.stationsLayer.eachLayer((layer) => {
        // Update popup content
        if (window.popupManager) {
          layer.bindPopup(window.popupManager.generatePopupContent(layer.feature));
        }
        // If popup is currently open, refresh display and reload chart
        if (layer.getPopup() && layer.getPopup().isOpen()) {
          layer.getPopup().update();
          if (window.chartManager) {
            window.chartManager.loadChartData(layer.feature.properties.ID);
          }
        }
      });
    }

    // Update comparison functionality translations
    if (window.comparisonManager) {
      window.comparisonManager.updateTranslations();
    }
  }

  getCurrentLang() {
    return this.currentLang;
  }

  getTranslations() {
    return window.GHCNConfig.translations[this.currentLang];
  }
}

// Create global language manager instance
window.languageManager = new LanguageManager();

// Global toggle language function (for HTML calls)
function toggleLanguage() {
  window.languageManager.toggleLanguage();
}
