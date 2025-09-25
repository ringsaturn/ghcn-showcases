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
          <p style="margin: 5px 0"><strong>${t.longitude}:</strong> ${
      coordinates[0].toFixed(2)
    }°</p>
          <p style="margin: 5px 0"><strong>${t.latitude}:</strong> ${
      coordinates[1].toFixed(2)
    }°</p>
          <p style="margin: 5px 0"><strong>${t.elevation}:</strong> ${properties.ELEVATION}${t.meters}</p>
        </div>
        <div style="margin-bottom: 15px; display: flex; gap: 10px;">
          <button class="add-to-compare" onclick="addStationToCompare('${stationId}', '${properties.NAME}')">${t.compareBtn}</button>
          <button class="copy-link-btn" onclick="copyStationLink('${stationId}')">${t.copyLinkBtn}</button>
        </div>
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
          <div>
            <h4 style="margin: 0 0 10px;">${t.monthlyHistoryChart}</h4>
            <div style="width: 100%; background: #f8f9fa; padding: 10px; border-radius: 4px; box-sizing: border-box;">
              <div id="monthlyHistoryPlaceholder-${stationId}" style="text-align: center; color: #666; font-size: 14px; padding: 20px 0;">
                ${t.historyLoading}
              </div>
              <canvas id="monthlyHistoryChart-${stationId}" style="width: 100%; height: 250px; display: none;"></canvas>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

// Create global popup manager instance
window.popupManager = new PopupManager();

// Copy station link function
function copyStationLink(stationId) {
  const url =
    `${window.location.origin}${window.location.pathname}?station_id=${stationId}`;

  if (navigator.clipboard && window.isSecureContext) {
    // Modern clipboard API
    navigator.clipboard.writeText(url).then(() => {
      showCopySuccess();
    }).catch((err) => {
      console.error("Failed to copy link: ", err);
      fallbackCopyToClipboard(url);
    });
  } else {
    // Fallback for older browsers or non-secure contexts
    fallbackCopyToClipboard(url);
  }
}

// Fallback copy method for older browsers
function fallbackCopyToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.left = "-999999px";
  textArea.style.top = "-999999px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    document.execCommand("copy");
    showCopySuccess();
  } catch (err) {
    console.error("Fallback: Could not copy text: ", err);
  }

  document.body.removeChild(textArea);
}

// Show copy success message
function showCopySuccess() {
  const t = window.languageManager.getTranslations();

  // Create toast notification
  const toast = document.createElement("div");
  toast.textContent = t.copyLinkSuccess;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #4CAF50;
    color: white;
    padding: 12px 20px;
    border-radius: 4px;
    z-index: 10000;
    font-family: Arial, sans-serif;
    font-size: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    animation: slideIn 0.3s ease-out;
  `;

  // Add animation keyframes if not already added
  if (!document.getElementById("toast-animation-style")) {
    const style = document.createElement("style");
    style.id = "toast-animation-style";
    style.textContent = `
      @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }

  document.body.appendChild(toast);

  // Remove toast after 3 seconds
  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease-in";
    setTimeout(() => {
      if (toast.parentNode) {
        document.body.removeChild(toast);
      }
    }, 300);
  }, 3000);
}
