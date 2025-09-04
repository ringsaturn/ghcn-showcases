// Chart manager
class ChartManager {
  constructor() {
    this.chartDefaults = null;
    this.useExtremeData = true; // Default to extreme data (min/max)
    this.updateChartDefaults();
  }

  updateChartDefaults() {
    const currentLang = window.languageManager.getCurrentLang();
    const t = window.languageManager.getTranslations();

    this.chartDefaults = {
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
              const item = tooltipItems[0];
              if (!item || !item.raw) return "";
              return item.raw.dateStr;
            },
            label: function (item) {
              if (item.dataset.label === t.precip) {
                return `${item.dataset.label}: ${item.parsed.y.toFixed(1)}mm`;
              }
              return `${item.dataset.label}: ${item.parsed.y.toFixed(1)}°C`;
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
              month: currentLang === "zh" || currentLang === "ja"
                ? `M${t.month}`
                : `M`,
              day: currentLang === "zh" || currentLang === "ja"
                ? `M${t.month}d${t.day}`
                : `M-d`,
            },
            tooltipFormat: currentLang === "zh" || currentLang === "ja"
              ? `M${t.month}d${t.day}`
              : `M-d`,
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
          position: "left",
          grid: {
            color: "#eee",
          },
          title: {
            display: true,
            text: t.tempAxis,
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
        y1: {
          position: "right",
          grid: {
            drawOnChartArea: false,
          },
          title: {
            display: true,
            text: t.precipAxis,
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
    };
  }

  // Toggle between extreme and percentile data
  toggleDataType() {
    this.useExtremeData = !this.useExtremeData;
    this.updateChartDefaults();
    // Reload current charts if any station is selected
    this.reloadCurrentCharts();
  }

  // Reload current charts
  reloadCurrentCharts() {
    // Find all chart containers and get unique station IDs
    const dailyCharts = document.querySelectorAll('[id^="dailyChart-"]');
    const monthlyCharts = document.querySelectorAll('[id^="monthlyChart-"]');
    const stationIds = new Set();

    // Collect station IDs and destroy existing charts
    dailyCharts.forEach((chart) => {
      const stationId = chart.id.replace("dailyChart-", "");
      if (stationId) {
        stationIds.add(stationId);
        const chartInstance = Chart.getChart(chart);
        if (chartInstance) {
          chartInstance.destroy();
        }
      }
    });

    monthlyCharts.forEach((chart) => {
      const stationId = chart.id.replace("monthlyChart-", "");
      if (stationId) {
        stationIds.add(stationId);
        const chartInstance = Chart.getChart(chart);
        if (chartInstance) {
          chartInstance.destroy();
        }
      }
    });

    // Reload chart data for each unique station
    stationIds.forEach((stationId) => {
      this.loadChartData(stationId);
    });
  }

  // Get current data type labels
  getCurrentLabels() {
    const t = window.languageManager.getTranslations();
    if (this.useExtremeData) {
      return {
        maxTemp: t.maxTempExtreme,
        minTemp: t.minTempExtreme,
        dataType: t.dataTypeExtreme,
      };
    } else {
      return {
        maxTemp: t.maxTemp,
        minTemp: t.minTemp,
        dataType: t.dataTypePercentile,
      };
    }
  }

  // Generate CSV file path
  getStationCsvPath(stationId, type) {
    let prefix = stationId.substring(0, 3);
    if (prefix.endsWith("0")) {
      prefix = prefix.slice(0, -1);
    }
    return `plots/${prefix}/${stationId}/${stationId}-${type}.csv`;
  }

  async loadChartData(stationId) {
    this.updateChartDefaults(); // Update chart defaults to adapt to current language

    const currentLang = window.languageManager.getCurrentLang();
    const t = window.languageManager.getTranslations();

    // Load and draw charts
    await Promise.all([
      fetch(this.getStationCsvPath(stationId, "daily"))
        .then((response) => response.text())
        .then((csvData) => {
          const results = Papa.parse(csvData, { header: true });
          const data = results.data;

          // Construct date data
          // Set fixed year and ignore display
          const baseDate = new Date(2020, 0, 1);
          const chartData = data
            .map((row) => {
              const month = parseInt(row.MONTH);
              const day = parseInt(row.DAY_OF_MONTH);
              return {
                x: new Date(baseDate.getFullYear(), month - 1, day),
                tmax_max: parseFloat(row.TMAX_MAX),
                tmin_min: parseFloat(row.TMIN_MIN),
                tmax_p90: parseFloat(row.TMAX_P90),
                tmin_p10: parseFloat(row.TMIN_P10),
                y_prcp: parseFloat(row.PRCP_SUM) || 0,
                month: month,
                day: day,
                dateStr: currentLang === "zh" || currentLang === "ja"
                  ? month + t.month + day + t.day
                  : month + "-" + day,
              };
            })
            .filter((point) =>
              !isNaN(point.tmax_max) && !isNaN(point.tmin_min) &&
              !isNaN(point.tmax_p90) && !isNaN(point.tmin_p10)
            );

          // Calculate temperature range based on current data type
          const labels = this.getCurrentLabels();
          const temperatures = chartData.flatMap((point) => [
            this.useExtremeData ? point.tmax_max : point.tmax_p90,
            this.useExtremeData ? point.tmin_min : point.tmin_p10,
          ]);
          const minTemp = Math.floor(Math.min(...temperatures));
          const maxTemp = Math.ceil(Math.max(...temperatures));

          new Chart(document.getElementById("dailyChart-" + stationId), {
            type: "line",
            data: {
              datasets: [
                {
                  label: labels.maxTemp,
                  data: chartData.map((point) => ({
                    x: point.x,
                    y: this.useExtremeData ? point.tmax_max : point.tmax_p90,
                  })),
                  borderColor: "rgba(255, 99, 132, 0.8)",
                  backgroundColor: "rgba(255, 99, 132, 0.1)",
                  borderWidth: 1.5,
                  pointRadius: 0,
                  fill: false,
                  tension: 0.2,
                  yAxisID: "y",
                },
                {
                  label: labels.minTemp,
                  data: chartData.map((point) => ({
                    x: point.x,
                    y: this.useExtremeData ? point.tmin_min : point.tmin_p10,
                  })),
                  borderColor: "rgba(54, 162, 235, 0.8)",
                  backgroundColor: "rgba(54, 162, 235, 0.1)",
                  borderWidth: 1.5,
                  pointRadius: 0,
                  fill: false,
                  tension: 0.2,
                  yAxisID: "y",
                },
                {
                  label: t.precip,
                  data: chartData.map((point) => ({
                    x: point.x,
                    y: point.y_prcp,
                  })),
                  borderColor: "rgba(75, 192, 192, 0.8)",
                  backgroundColor: "rgba(75, 192, 192, 0.2)",
                  borderWidth: 1.5,
                  pointRadius: 0,
                  fill: true,
                  tension: 0.2,
                  yAxisID: "y1",
                },
              ],
            },
            options: {
              ...this.chartDefaults,
              scales: {
                ...this.chartDefaults.scales,
                y: {
                  ...this.chartDefaults.scales.y,
                  min: minTemp - 2,
                  max: maxTemp + 2,
                  ticks: {
                    stepSize: 5,
                  },
                },
              },
            },
          });
        }),

      fetch(this.getStationCsvPath(stationId, "monthly"))
        .then((response) => response.text())
        .then((csvData) => {
          const results = Papa.parse(csvData, { header: true });
          const data = results.data;

          // Construct monthly data
          // Set fixed year and ignore display
          const baseDate = new Date(2020, 0, 1);
          const chartData = data
            .map((row) => {
              const month = parseInt(row.MONTH);
              return {
                x: new Date(baseDate.getFullYear(), month - 1, 1),
                tmax_max: parseFloat(row.TMAX_MAX),
                tmin_min: parseFloat(row.TMIN_MIN),
                tmax_p90: parseFloat(row.TMAX_P90),
                tmin_p10: parseFloat(row.TMIN_P10),
                y_prcp: parseFloat(row.PRCP_SUM) || 0,
                month: month,
                dateStr: currentLang === "zh" || currentLang === "ja"
                  ? month + t.month
                  : month.toString(),
              };
            })
            .filter((point) =>
              !isNaN(point.tmax_max) && !isNaN(point.tmin_min) &&
              !isNaN(point.tmax_p90) && !isNaN(point.tmin_p10)
            );

          // Calculate temperature range based on current data type
          const labels = this.getCurrentLabels();
          const temperatures = chartData.flatMap((point) => [
            this.useExtremeData ? point.tmax_max : point.tmax_p90,
            this.useExtremeData ? point.tmin_min : point.tmin_p10,
          ]);
          const minTemp = Math.floor(Math.min(...temperatures));
          const maxTemp = Math.ceil(Math.max(...temperatures));

          new Chart(document.getElementById("monthlyChart-" + stationId), {
            type: "line",
            data: {
              datasets: [
                {
                  label: labels.maxTemp,
                  data: chartData.map((point) => ({
                    x: point.x,
                    y: this.useExtremeData ? point.tmax_max : point.tmax_p90,
                  })),
                  borderColor: "rgba(255, 99, 132, 0.8)",
                  backgroundColor: "rgba(255, 99, 132, 0.1)",
                  borderWidth: 2,
                  pointRadius: 4,
                  pointBackgroundColor: "rgba(255, 99, 132, 1)",
                  fill: false,
                  tension: 0.3,
                  yAxisID: "y",
                },
                {
                  label: labels.minTemp,
                  data: chartData.map((point) => ({
                    x: point.x,
                    y: this.useExtremeData ? point.tmin_min : point.tmin_p10,
                  })),
                  borderColor: "rgba(54, 162, 235, 0.8)",
                  backgroundColor: "rgba(54, 162, 235, 0.1)",
                  borderWidth: 2,
                  pointRadius: 4,
                  pointBackgroundColor: "rgba(54, 162, 235, 1)",
                  fill: false,
                  tension: 0.3,
                  yAxisID: "y",
                },
                {
                  label: t.precip,
                  data: chartData.map((point) => ({
                    x: point.x,
                    y: point.y_prcp,
                  })),
                  borderColor: "rgba(75, 192, 192, 0.8)",
                  backgroundColor: "rgba(75, 192, 192, 0.2)",
                  borderWidth: 2,
                  pointRadius: 4,
                  pointBackgroundColor: "rgba(75, 192, 192, 1)",
                  fill: true,
                  tension: 0.3,
                  yAxisID: "y1",
                },
              ],
            },
            options: {
              ...this.chartDefaults,
              scales: {
                ...this.chartDefaults.scales,
                y: {
                  ...this.chartDefaults.scales.y,
                  position: "left",
                  min: minTemp - 2,
                  max: maxTemp + 2,
                  ticks: {
                    stepSize: 5,
                  },
                },
                y1: {
                  position: "right",
                  grid: {
                    drawOnChartArea: false,
                  },
                  title: {
                    display: true,
                    text: t.precipAxis,
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
        }),
    ]);
  }
}

// Create global chart manager instance
window.chartManager = new ChartManager();
