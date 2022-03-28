var tempChart = null;

function updateCharts() {
    if (tempChart !== null) {
        tempChart.data.datasets[0].data = tempData;
        tempChart.data.datasets[1].data = humidityData;
        tempChart.update();
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

    tempChart = createChart(datasets);
}

function createChart(ds) {
    return new Chart($("#temperatureChart"), {
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
