// Popup manager
class PopupManager {
  generatePopupContent(feature) {
    const t = window.languageManager.getTranslations();
    const properties = feature.properties;
    const coordinates = feature.geometry.coordinates;
    const stationId = properties.ID;

    return `
      <div style="width: 80vw; max-width: 800px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); box-sizing: border-box;">
        <h3 style="margin-top: 0; margin-bottom: 10px;">${t.stationInfo}</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 20px">
          <p style="margin: 5px 0"><strong>${t.stationId}:</strong> ${properties.ID}</p>
          <p style="margin: 5px 0"><strong>${t.name}:</strong> ${properties.NAME}</p>
          <p style="margin: 5px 0"><strong>${t.longitude}:</strong> ${coordinates[0].toFixed(2)}°</p>
          <p style="margin: 5px 0"><strong>${t.latitude}:</strong> ${coordinates[1].toFixed(2)}°</p>
          <p style="margin: 5px 0"><strong>${t.elevation}:</strong> ${properties.ELEVATION}${t.meters}</p>
        </div>
        <button class="add-to-compare" onclick="addStationToCompare('${stationId}', '${properties.NAME}')">${t.compareBtn}</button>
        <div style="margin-top: 20px; display: flex; flex-direction: column; gap: 20px;">
          <div>
            <h4 style="margin: 0 0 10px;">${t.dailyChart}</h4>
            <div style="width: 100%; margin-bottom: 0; background: #f8f9fa; padding: 10px; border-radius: 4px; box-sizing: border-box;">
              <canvas id="dailyChart-${stationId}" style="width: 100%; height: 250px;"></canvas>
            </div>
          </div>
          <div>
            <h4 style="margin: 0 0 10px;">${t.monthlyChart}</h4>
            <div style="width: 100%; background: #f8f9fa; padding: 10px; border-radius: 4px; box-sizing: border-box;">
              <canvas id="monthlyChart-${stationId}" style="width: 100%; height: 250px;"></canvas>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

// Create global popup manager instance
window.popupManager = new PopupManager();
