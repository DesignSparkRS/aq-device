var tempChart = null;
var VOCChart = null;
var CO2Chart = null;
var PMChart = null;
var NO2Chart = null;
var NRDChart = null;
var FDHChart = null;

function updateCharts(tempData, humidityData, VOCData, CO2Data, PM1Data, PM25Data, PM4Data, PM10Data, NO2Data, NRDData, FDHData) {
    if (tempChart !== null && tempChart.ctx !== null) {
        tempChart.data.datasets[0].data = tempData;
        tempChart.data.datasets[1].data = humidityData;
        tempChart.update();
    }
    if (VOCChart !== null && VOCChart.ctx !== null) {
        VOCChart.data.datasets[0].data = VOCData;
        VOCChart.update();
    }
    if (CO2Chart !== null && CO2Chart.ctx !== null) {
        CO2Chart.data.datasets[0].data = CO2Data;
        CO2Chart.update();
    }
    if (PMChart !== null && PMChart.ctx !== null) {
        PMChart.data.datasets[0].data = PM1Data;
        PMChart.data.datasets[1].data = PM25Data;
        PMChart.data.datasets[2].data = PM4Data;
        PMChart.data.datasets[3].data = PM10Data;
        PMChart.update();
    }
    if (NO2Chart !== null && NO2Chart.ctx !== null) {
        NO2Chart.data.datasets[0].data = NO2Data;
        NO2Chart.update();
    }
    if (NRDChart !== null && NRDChart.ctx !== null) {
        NRDChart.data.datasets[0].data = NRDData;
        NRDChart.update();
    }
    if (FDHChart !== null && FDHChart.ctx !== null) {
        FDHChart.data.datasets[0].data = FDHData;
        FDHChart.update();
    }
}

function showTempChart(tempData, humidityData) {
    var datasets = [
        {
            label: 'Temperature (°C)',
            data: tempData,
            borderColor: 'orange',
            backgroundColor: 'orange',
            pointRadius: 0
        },
        {
            label: 'Humidity (%)',
            data: humidityData,
            borderColor: '#608dc4',
            backgroundColor: '#608dc4',
            pointRadius: 0
        }
    ]

    tempChart = createChart($("#temperatureChart"), datasets);
}

function showVOCChart(VOCData) {
    var datasets = [
        {
            label: 'Volatile Organic Compounds',
            data: VOCData,
            borderColor: 'green',
            backgroundColor: 'green',
            pointRadius: 0
        }
    ]

    VOCChart = createChart($("#VOCChart"), datasets);
}

function showCO2Chart(CO2Data) {
    var datasets = [
        {
            label: 'CO2',
            data: CO2Data,
            borderColor: '#3d426b',
            backgroundColor: '#3d426b',
            pointRadius: 0
        }
    ]

    CO2Chart = createChart($("#CO2Chart"), datasets);
}

function showPMChart(PM1Data, PM25Data, PM4Data, PM10Data) {
    var datasets = [
        {
            label: 'PM 1.0',
            data: PM1Data,
            borderColor: '#22eaaa',
            backgroundColor: '#22eaaa',
            pointRadius: 0
        },
        {
            label: 'PM 2.5',
            data: PM25Data,
            borderColor: '#ffb174',
            backgroundColor: '#ffb174',
            pointRadius: 0
        },
        {
            label: 'PM 4.0',
            data: PM4Data,
            borderColor: '#ee5a5a',
            backgroundColor: '#ee5a5a',
            pointRadius: 0
        },
        {
            label: 'PM 10',
            data: PM10Data,
            borderColor: '#b31e6f',
            backgroundColor: '#b31e6f',
            pointRadius: 0
        }
    ]

    PMChart = createChart($("#PMChart"), datasets);
}

function showNO2Chart(NO2Data) {
    var datasets = [
        {
            label: 'Nitrogen Dioxide',
            data: NO2Data,
            borderColor: 'green',
            backgroundColor: 'green',
            pointRadius: 0
        }
    ]

    NO2Chart = createChart($("#NO2Chart"), datasets);
}

function showNRDChart(NRDData) {
    var datasets = [
        {
            label: 'Nuclear Counts Per Minute',
            data: NRDData,
            borderColor: 'green',
            backgroundColor: 'green',
            pointRadius: 0
        }
    ]

    NRDChart = createChart($("#NRDChart"), datasets);
}

function showFDHChart(FDHData) {
    var datasets = [
        {
            label: 'Formaldehyde',
            data: FDHData,
            borderColor: 'green',
            backgroundColor: 'green',
            pointRadius: 0
        }
    ]

    FDHChart = createChart($("#FDHChart"), datasets);
}

function createChart(chartElem, ds) {
    return new Chart($(chartElem), {
        type: 'line',
        data: {
            datasets: ds
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function trimData(dataset, maxAge) {
    let now = Date.now();
    dataset.forEach(data => {
        if(typeof data[0] !== "undefined") {
            if(now - data[0].x > maxAge) {
                data.shift();
            }
        }
    });
}
