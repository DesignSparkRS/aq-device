var tempChart = null;
var VOCChart = null;
var CO2Chart = null;

function updateCharts(tempData, humidityData, VOCData) {
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
