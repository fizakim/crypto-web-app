document.addEventListener('DOMContentLoaded', function () {
    const labelsElem = document.getElementById('chart-labels');
    const valuesElem = document.getElementById('chart-values');
    const canvasElem = document.getElementById('walletChart');

    if (labelsElem && valuesElem && canvasElem) {
        const labels = JSON.parse(labelsElem.textContent);
        const values = JSON.parse(valuesElem.textContent);
        const ctx = canvasElem.getContext('2d');

        window.walletChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Wallet Value',
                    data: values,
                    borderColor: '#f5f5f5',
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: '#f5f5f5'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f5f5f5'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#cfcfcf' },
                        grid: { color: '#222' }
                    },
                    y: {
                        ticks: { color: '#cfcfcf' },
                        grid: { color: '#222' }
                    }
                }
            }
        });
    }

    document.body.addEventListener('click', function (e) {
        if (e.target.classList.contains('period-btn')) {
            e.preventDefault();
            const url = e.target.getAttribute('href');

            fetch(url)
                .then(res => res.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    const newWallet = doc.querySelector('.wallet-display');
                    if (newWallet) document.querySelector('.wallet-display').innerHTML = newWallet.innerHTML;

                    const newEarnings = doc.querySelector('.earnings-box');
                    if (newEarnings) document.querySelector('.earnings-box').innerHTML = newEarnings.innerHTML;

                    const newActions = doc.querySelector('.chart-actions');
                    if (newActions) document.querySelector('.chart-actions').innerHTML = newActions.innerHTML;

                    const newLabelsElem = doc.getElementById('chart-labels');
                    const newValuesElem = doc.getElementById('chart-values');

                    if (newLabelsElem && newValuesElem && window.walletChart) {
                        const newLabels = JSON.parse(newLabelsElem.textContent);
                        const newValues = JSON.parse(newValuesElem.textContent);
                        window.walletChart.data.labels = newLabels;
                        window.walletChart.data.datasets[0].data = newValues;
                        window.walletChart.update();
                    }
                })
                .catch(err => console.error("Error fetching data:", err));
        }
    });
});
