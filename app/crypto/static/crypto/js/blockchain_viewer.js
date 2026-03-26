document.addEventListener('DOMContentLoaded', function () {
    const labelsElement = document.getElementById('price-chart-labels-data');
    const valuesElement = document.getElementById('price-chart-values-data');
    const chartCanvas = document.getElementById('priceHistoryChart');

    if (labelsElement && valuesElement && chartCanvas && typeof Chart !== 'undefined') {
        const labels = JSON.parse(labelsElement.textContent);
        const values = JSON.parse(valuesElement.textContent);

        if (labels.length && values.length) {
            new Chart(chartCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Price',
                            data: values,
                            borderColor: '#8fd3ff',
                            backgroundColor: 'rgba(143, 211, 255, 0.10)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.35,
                            pointRadius: 3,
                            pointHoverRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: '#111111',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            callbacks: {
                                label: function (context) {
                                    return '£' + Number(context.parsed.y).toFixed(2);
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#bfbfbf',
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 6
                            }
                        },
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: '#3a3a3a'
                            },
                            ticks: {
                                color: '#bfbfbf',
                                callback: function (value) {
                                    return '£' + Number(value).toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    const networkSelect = document.getElementById('network-select');
    const networkForm = document.getElementById('network-form');

    if (networkSelect && networkForm) {
        networkSelect.addEventListener('change', function () {
            networkForm.submit();
        });
    }
});