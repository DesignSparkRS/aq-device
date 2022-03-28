var tempChart = null;
var VOCChart = null;
var CO2Chart = null;
var PMChart = null;

function updateCharts(tempData, humidityData, VOCData, CO2Data, PM1Data, PM25Data, PM4Data, PM10Data) {
    if (tempChart !== null) {
        tempChart.data.datasets[0].data = tempData;
        tempChart.data.datasets[1].data = humidityData;
        tempChart.update();
    }
    if (VOCChart !== null) {
        VOCChart.data.datasets[0].data = VOCData;
        VOCChart.update();
    }
    if (CO2Chart !== null) {
        CO2Chart.data.datasets[0].data = CO2Data;
        CO2Chart.update();
    }
    if (PMChart !== null) {
        PMChart.data.datasets[0].data = PM1Data;
        PMChart.data.datasets[1].data = PM25Data;
        PMChart.data.datasets[2].data = PM4Data;
        PMChart.data.datasets[3].data = PM10Data;
        PMChart.update();
    }
}

function showTempChart(tempData, humidityData) {
    if (tempChart !== null) {
        tempChart.destroy();
    }
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
    if (VOCChart !== null) {
        VOCChart.destroy();
    }
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
    if (CO2Chart !== null) {
        CO2Chart.destroy();
    }
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
    if (PMChart !== null) {
        PMChart.destroy();
    }
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

function createChart(chartElem, ds) {
    return new Chart($(chartElem), {
        type: 'line',
        data: {
            datasets: ds
        },
        options: {
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
