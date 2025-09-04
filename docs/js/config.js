// Language configuration
const translations = {
  zh: {
    stationInfo: "气象站点信息",
    stationId: "站点编号",
    name: "站点名称",
    longitude: "经度",
    latitude: "纬度",
    elevation: "海拔高度",
    dailyChart: "日温度变化",
    monthlyChart: "月温度变化",
    meters: "米",
    month: "月",
    day: "日",
    monthAxis: "月份",
    tempAxis: "温度 (°C)",
    maxTemp: "90分位最高温度",
    minTemp: "10分位最低温度",
    maxTempExtreme: "极值最高温度",
    minTempExtreme: "极值最低温度",
    dataTypePercentile: "百分位数据",
    dataTypeExtreme: "极值数据",
    precipAxis: "降水量 (mm)",
    precip: "降水量",
    compareBtn: "对比此站点",
    copyLinkBtn: "复制链接",
    copyLinkSuccess: "链接已复制到剪贴板",
    compareTitle: "站点对比",
    compareStations: "已选择站点",
    comparePanel: "站点对比面板",
    compareLimit: "最多可选择3个站点",
    compareChart: "对比图表",
    compareTemperature: "温度对比",
    comparePrecipitation: "降水量对比",
    close: "关闭",
    showComparison: "查看对比",
    clear: "清空选择",
    compareMonthly: "月度数据对比",
    noStationSelected: "请至少选择一个站点进行对比",
    // Data source text (HTML allowed)
    dataSource:
      '数据来源：<a href="https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily" target="_blank" rel="noopener">GHCN</a>',
  },
  en: {
    stationInfo: "Weather Station Information",
    stationId: "Station ID",
    name: "Station Name",
    longitude: "Longitude",
    latitude: "Latitude",
    elevation: "Elevation",
    dailyChart: "Daily Temperature Variation",
    monthlyChart: "Monthly Temperature Variation",
    meters: "m",
    month: "-",
    day: "",
    monthAxis: "Month",
    tempAxis: "Temperature (°C)",
    maxTemp: "90th Percentile Max Temperature",
    minTemp: "10th Percentile Min Temperature",
    maxTempExtreme: "Extreme Max Temperature",
    minTempExtreme: "Extreme Min Temperature",
    dataTypePercentile: "Percentile Data",
    dataTypeExtreme: "Extreme Data",
    precipAxis: "Precipitation (mm)",
    precip: "Precipitation",
    compareBtn: "Compare This Station",
    copyLinkBtn: "Copy Link",
    copyLinkSuccess: "Link copied to clipboard",
    compareTitle: "Station Comparison",
    compareStations: "Selected Stations",
    comparePanel: "Comparison Panel",
    compareLimit: "Maximum 3 stations can be selected",
    compareChart: "Comparison Chart",
    compareTemperature: "Temperature Comparison",
    comparePrecipitation: "Precipitation Comparison",
    close: "Close",
    showComparison: "View Comparison",
    clear: "Clear Selection",
    compareMonthly: "Monthly Data Comparison",
    noStationSelected: "Please select at least one station to compare",
    // Data source text (HTML allowed)
    dataSource:
      'Data source: <a href="https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily" target="_blank" rel="noopener">GHCN (Global Historical Climatology Network)</a>',
  },
  ja: {
    stationInfo: "気象観測所情報",
    stationId: "観測所ID",
    name: "観測所名",
    longitude: "経度",
    latitude: "緯度",
    elevation: "標高",
    dailyChart: "日々の気温変動",
    monthlyChart: "月間気温変動",
    meters: "m",
    month: "月",
    day: "日",
    monthAxis: "月",
    tempAxis: "気温 (°C)",
    maxTemp: "90パーセンタイル最高気温",
    minTemp: "10パーセンタイル最低気温",
    maxTempExtreme: "極値最高気温",
    minTempExtreme: "極値最低気温",
    dataTypePercentile: "パーセンタイルデータ",
    dataTypeExtreme: "極値データ",
    precipAxis: "降水量 (mm)",
    precip: "降水量",
    compareBtn: "この観測所を比較",
    copyLinkBtn: "リンクをコピー",
    copyLinkSuccess: "リンクがクリップボードにコピーされました",
    compareTitle: "観測所の比較",
    compareStations: "選択された観測所",
    comparePanel: "比較パネル",
    compareLimit: "最大3つの観測所を選択できます",
    compareChart: "比較チャート",
    compareTemperature: "気温の比較",
    comparePrecipitation: "降水量の比較",
    close: "閉じる",
    showComparison: "比較を表示",
    clear: "選択をクリア",
    compareMonthly: "月間データ比較",
    noStationSelected: "比較するには少なくとも1つの観測所を選択してください",
    // Data source text (HTML allowed)
    dataSource:
      'データ出典：<a href="https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily" target="_blank" rel="noopener">GHCN（Global Historical Climatology Network）</a>',
  },
};

// Get browser language setting and set initial language
function getInitialLanguage() {
  const browserLang = navigator.language.toLowerCase();
  // If browser language starts with zh, use Chinese; if ja, use Japanese; otherwise English
  if (browserLang.startsWith("zh")) {
    return "zh";
  } else if (browserLang.startsWith("ja")) {
    return "ja";
  } else {
    return "en";
  }
}

// Export configuration
window.GHCNConfig = {
  translations,
  getInitialLanguage,
};
