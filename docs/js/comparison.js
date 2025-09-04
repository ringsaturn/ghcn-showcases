// Comparison functionality manager
class ComparisonManager {
  constructor() {
    this.selectedStations = [];
    this.compareChart = null;
    this.allStationData = {};
    this.activeCompareTab = "temperature";
    this.useExtremeData = true; // Default to extreme data (min/max)
    this.init();
  }

  init() {
    this.updateTranslations();
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    document
      .getElementById("toggleComparePanel")
      .addEventListener("click", () => this.toggleComparePanel());
    document
      .getElementById("closeComparePanel")
      .addEventListener("click", () => this.toggleComparePanel());
    document
      .getElementById("viewComparisonBtn")
      .addEventListener("click", () => this.showComparisonModal());
    document
      .getElementById("clearComparisonBtn")
      .addEventListener("click", () => this.clearSelectedStations());
    document
      .getElementById("closeComparisonModal")
      .addEventListener("click", () => this.hideComparisonModal());

    // Set up tab switching
    document
      .getElementById("temperatureTab")
      .addEventListener("click", () => this.switchComparisonTab("temperature"));
    document
      .getElementById("precipitationTab")
      .addEventListener(
        "click",
        () => this.switchComparisonTab("precipitation"),
      );
  }

  updateTranslations() {
    const t = window.languageManager.getTranslations();
    document.getElementById("comparePanelTitle").textContent = t.comparePanel;
    document.getElementById("compareLimit").textContent = t.compareLimit;
    document.getElementById("viewComparisonBtn").textContent = t.showComparison;
    document.getElementById("clearComparisonBtn").textContent = t.clear;
    document.getElementById("compareModalTitle").textContent = t.compareMonthly;
    document.getElementById("temperatureTab").textContent =
      t.compareTemperature;
    document.getElementById("precipitationTab").textContent =
      t.comparePrecipitation;
    document.getElementById("noStationsMessage").textContent =
      t.noStationSelected;
  }

  // Toggle between extreme and percentile data
  toggleDataType() {
    this.useExtremeData = !this.useExtremeData;
    if (this.compareChart) {
      this.renderComparisonChart();
    }
  }

  // Get current data type labels
  getCurrentLabels() {
    const t = window.languageManager.getTranslations();
    if (this.useExtremeData) {
      return {
        maxTemp: t.maxTempExtreme,
        minTemp: t.minTempExtreme,
        dataType: t.dataTypeExtreme
      };
    } else {
      return {
        maxTemp: t.maxTemp,
        minTemp: t.minTemp,
        dataType: t.dataTypePercentile
      };
    }
  }

  toggleComparePanel() {
    const panel = document.getElementById("comparePanel");
    const button = document.getElementById("toggleComparePanel");

    if (panel.style.display === "none" || !panel.style.display) {
      panel.style.display = "block";
      button.style.display = "none";
    } else {
      panel.style.display = "none";
      button.style.display = "flex";
    }
  }

  addStationToCompare(stationId, stationName) {
    if (this.selectedStations.some((station) => station.id === stationId)) {
      return; // Station already in the list
    }

    if (this.selectedStations.length >= 3) {
      const t = window.languageManager.getTranslations();
      alert(t.compareLimit);
      return;
    }

    this.selectedStations.push({
      id: stationId,
      name: stationName,
    });

    this.updateCompareStationsList();

    // If we don't have the station data for comparison yet, fetch it
    if (!this.allStationData[stationId]) {
      this.fetchStationDataForComparison(stationId);
    }
  }

  removeStationFromCompare(stationId) {
    this.selectedStations = this.selectedStations.filter(
      (station) => station.id !== stationId,
    );
    this.updateCompareStationsList();
  }

  clearSelectedStations() {
    this.selectedStations = [];
    this.updateCompareStationsList();
  }

  updateCompareStationsList() {
    const listContainer = document.getElementById("compareStationList");
    const noStationsMessage = document.getElementById("noStationsMessage");

    // Clear the current list
    while (listContainer.firstChild) {
      listContainer.removeChild(listContainer.firstChild);
    }

    if (this.selectedStations.length === 0) {
      listContainer.appendChild(noStationsMessage);
      return;
    } else {
      if (noStationsMessage.parentNode === listContainer) {
        listContainer.removeChild(noStationsMessage);
      }
    }

    // Add each station to the list
    this.selectedStations.forEach((station) => {
      const stationItem = document.createElement("div");
      stationItem.className = "compare-station-item";

      const stationName = document.createElement("div");
      stationName.className = "compare-station-name";
      stationName.textContent = `${station.name} (${station.id})`;
      stationItem.appendChild(stationName);

      const removeButton = document.createElement("button");
      removeButton.className = "remove-station-btn";
      removeButton.textContent = "×";
      removeButton.addEventListener(
        "click",
        () => this.removeStationFromCompare(station.id),
      );
      stationItem.appendChild(removeButton);

      listContainer.appendChild(stationItem);
    });
  }

  async fetchStationDataForComparison(stationId) {
    try {
      const monthlyResponse = await fetch(
        window.chartManager.getStationCsvPath(stationId, "monthly"),
      );
      const monthlyText = await monthlyResponse.text();
      const monthlyResults = Papa.parse(monthlyText, { header: true });

      // Construct monthly data
      const baseDate = new Date(2020, 0, 1);
      const monthlyData = monthlyResults.data
        .filter((row) => row.MONTH) // Ensure we have valid rows
        .map((row) => {
          const month = parseInt(row.MONTH);
          return {
            month: month,
            x: new Date(baseDate.getFullYear(), month - 1, 1),
            tmax_max: parseFloat(row.TMAX_MAX),
            tmin_min: parseFloat(row.TMIN_MIN),
            tmax_p90: parseFloat(row.TMAX_P90),
            tmin_p10: parseFloat(row.TMIN_P10),
            prcp_sum: parseFloat(row.PRCP_SUM) || 0,
          };
        })
        .filter((point) => !isNaN(point.tmax_max) && !isNaN(point.tmin_min) && 
                           !isNaN(point.tmax_p90) && !isNaN(point.tmin_p10));

      // Store data
      this.allStationData[stationId] = {
        monthly: monthlyData,
      };
    } catch (error) {
      console.error("Error fetching data for station:", stationId, error);
    }
  }

  async showComparisonModal() {
    const t = window.languageManager.getTranslations();
    if (this.selectedStations.length === 0) {
      alert(t.noStationSelected);
      return;
    }

    document.getElementById("comparisonModal").style.display = "flex";

    // Wait for all data to be fetched
    for (const station of this.selectedStations) {
      if (!this.allStationData[station.id]) {
        await this.fetchStationDataForComparison(station.id);
      }
    }

    // Show comparison chart
    this.renderComparisonChart();
  }

  hideComparisonModal() {
    document.getElementById("comparisonModal").style.display = "none";
    if (this.compareChart) {
      this.compareChart.destroy();
      this.compareChart = null;
    }
  }

  switchComparisonTab(tab) {
    this.activeCompareTab = tab;

    // Update active tab styling
    document.querySelectorAll(".compare-tab").forEach((el) => {
      el.classList.remove("active");
    });
    document.getElementById(tab + "Tab").classList.add("active");

    // Re-render the chart
    if (this.compareChart) {
      this.compareChart.destroy();
      this.compareChart = null;
    }

    this.renderComparisonChart();
  }

  renderComparisonChart() {
    const ctx = document.getElementById("compareChart").getContext("2d");
    const t = window.languageManager.getTranslations();
    const labels = this.getCurrentLabels();
    const currentLang = window.languageManager.getCurrentLang();

    if (this.compareChart) {
      this.compareChart.destroy();
    }

    const datasets = [];
    const colors = ["#FF6384", "#36A2EB", "#4BC0C0"]; // Colors for stations

    this.selectedStations.forEach((station, index) => {
      const stationData = this.allStationData[station.id];
      if (!stationData) return;

      const color = colors[index % colors.length];

      if (this.activeCompareTab === "temperature") {
        // Add max temperature dataset
        datasets.push({
          label: `${station.name} - ${labels.maxTemp}`,
          data: stationData.monthly.map((point) => ({
            x: point.x,
            y: this.useExtremeData ? point.tmax_max : point.tmax_p90,
          })),
          borderColor: color,
          backgroundColor: color + "33", // Add transparency
          borderWidth: 2,
          pointRadius: 5,
          fill: false,
          tension: 0.3,
        });

        // Add min temperature dataset
        datasets.push({
          label: `${station.name} - ${labels.minTemp}`,
          data: stationData.monthly.map((point) => ({
            x: point.x,
            y: this.useExtremeData ? point.tmin_min : point.tmin_p10,
          })),
          borderColor: color,
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 5,
          borderDash: [5, 5], // Dashed line for min temperature
          fill: false,
          tension: 0.3,
        });
      } else {
        // Add precipitation dataset
        datasets.push({
          label: `${station.name} - ${t.precip}`,
          data: stationData.monthly.map((point) => ({
            x: point.x,
            y: point.prcp_sum,
          })),
          borderColor: color,
          backgroundColor: color + "33", // Add transparency
          borderWidth: 2,
          pointRadius: 5,
          fill: true,
          tension: 0.3,
        });
      }
    });

    this.compareChart = new Chart(ctx, {
      type: "line",
      data: {
        datasets: datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: "nearest",
          axis: "x",
        },
        plugins: {
          legend: {
            position: "top",
            labels: {
              padding: 15,
              usePointStyle: true,
              pointStyle: "circle",
            },
          },
          tooltip: {
            enabled: true,
            backgroundColor: "rgba(255, 255, 255, 0.9)",
            titleColor: "#000",
            bodyColor: "#000",
            borderColor: "#ddd",
            borderWidth: 1,
            padding: 10,
            displayColors: true,
            titleAlign: "center",
            callbacks: {
              title: function (tooltipItems) {
                if (!tooltipItems.length) return "";
                const date = tooltipItems[0].raw.x;
                const month = date.getMonth() + 1;
                return currentLang === "zh"
                  ? month + t.month
                  : month.toString();
              },
            },
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: "month",
              displayFormats: {
                month: currentLang === "zh" ? `M${t.month}` : `M`,
              },
            },
            grid: {
              color: "#eee",
            },
            title: {
              display: true,
              text: t.monthAxis,
              padding: { top: 10, bottom: 10 },
              font: {
                size: 14,
              },
            },
            ticks: {
              maxRotation: 0,
              font: {
                size: 12,
              },
            },
          },
          y: {
            grid: {
              color: "#eee",
            },
            title: {
              display: true,
              text: this.activeCompareTab === "temperature"
                ? t.tempAxis
                : t.precipAxis,
              padding: { top: 10, bottom: 10 },
              font: {
                size: 14,
              },
            },
            ticks: {
              font: {
                size: 12,
              },
            },
          },
        },
      },
    });
  }
}

// Create global comparison manager instance
window.comparisonManager = new ComparisonManager();

// Global function for HTML calls
function addStationToCompare(stationId, stationName) {
  window.comparisonManager.addStationToCompare(stationId, stationName);
}
