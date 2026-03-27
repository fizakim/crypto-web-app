const BlockchainExplorer = {
    config: {
        symbol: '',
        apiUrl: '',
        refreshInterval: 5000
    },
    chart: null,

    init(config) {
        Object.assign(this.config, config);
        this.initChart();
        this.startRefresh();
    },

    initChart() {
        const labelsElement = document.getElementById('price-chart-labels-data');
        const valuesElement = document.getElementById('price-chart-values-data');
        const chartCanvas = document.getElementById('priceHistoryChart');

        if (labelsElement && valuesElement && chartCanvas && typeof Chart !== 'undefined') {
            const labels = JSON.parse(labelsElement.textContent);
            const values = JSON.parse(valuesElement.textContent);

            this.chart = new Chart(chartCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Price',
                        data: values,
                        borderColor: '#8fd3ff',
                        backgroundColor: 'rgba(143, 211, 255, 0.10)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#111111',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            callbacks: {
                                label: (context) => '\u00A3' + Number(context.parsed.y).toFixed(2)
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#bfbfbf', maxRotation: 0, autoSkip: true, maxTicksLimit: 6 }
                        },
                        y: {
                            beginAtZero: false,
                            grid: { color: '#3a3a3a' },
                            ticks: {
                                color: '#bfbfbf',
                                callback: (value) => '\u00A3' + Number(value).toFixed(2)
                            }
                        }
                    }
                }
            });
        }
    },

    startRefresh() {
        setInterval(() => this.refreshData(), this.config.refreshInterval);
    },

    refreshData() {
        $.ajax({
            url: `${this.config.apiUrl}?network=${this.config.symbol}`,
            method: 'GET',
            success: (data) => this.renderUpdate(data)
        });
    },

    renderUpdate(data) {
        // Update Stats
        const stats = data.stats;
        $('#stats-height').text(stats.height);
        $('#stats-difficulty').text(stats.difficulty);
        $('#stats-reward').text(stats.reward);
        $('#stats-price').html('&pound;' + Number(stats.price).toFixed(2));
        $('#stats-utxo-count').text(stats.utxo_count);
        $('#stats-total-blocks').text(stats.total_blocks);
        $('#stats-total-transactions').text(stats.total_transactions);
        $('#stats-latest-hash').text(stats.latest_hash || 'No blocks yet');

        // Update Recent Blocks
        const blocksContainer = $('#blocks-container');
        if (data.recent_blocks && data.recent_blocks.length > 0) {
            let blocksHtml = '';
            data.recent_blocks.forEach((block, index) => {
                blocksHtml += `
                    <article class="block-card">
                        <div class="block-card-title">Block #${block.index}</div>
                        <div class="block-row"><span class="block-label">Nonce</span><span class="block-value">${block.nonce}</span></div>
                        <div class="block-row"><span class="block-label">Difficulty</span><span class="block-value">${block.difficulty}</span></div>
                        <div class="block-row"><span class="block-label">Transactions</span><span class="block-value">${block.tx_count}</span></div>
                        <div class="block-row"><span class="block-label">Timestamp</span><span class="block-value">${this.formatTimestamp(block.timestamp)}</span></div>
                        <div class="block-hash-group"><span class="block-label">Hash</span><span class="block-hash">${this.truncate(block.block_hash, 28)}</span></div>
                        <div class="block-hash-group"><span class="block-label">Prev</span><span class="block-hash">${this.truncate(block.previous_hash, 28)}</span></div>
                    </article>
                `;
                if (index < data.recent_blocks.length - 1) {
                    blocksHtml += `
                        <div class="block-arrow" aria-hidden="true">
                            <span class="block-arrow-line"></span>
                            <span class="block-arrow-head"></span>
                        </div>
                    `;
                }
            });
            blocksContainer.html(blocksHtml);
            $('#no-blocks-msg').addClass('d-none');
        } else {
            blocksContainer.empty();
            $('#no-blocks-msg').removeClass('d-none');
        }

        // Update Mempool
        const mempoolBody = $('#mempool-body');
        if (data.pending_transactions && data.pending_transactions.length > 0) {
            const memHtml = data.pending_transactions.map(tx => `
                <tr>
                    <td>${tx.timestamp}</td>
                    <td class="mono-hash">${tx.tx_id}</td>
                    <td class="mono-hash">${tx.address}</td>
                    <td class="text-end"><span class="status-pill">${tx.status}</span></td>
                </tr>
            `).join('');
            mempoolBody.html(memHtml);
            $('#mempool-table-container').removeClass('d-none');
            $('#mempool-empty-msg').addClass('d-none');
        } else {
            mempoolBody.empty();
            $('#mempool-table-container').addClass('d-none');
            $('#mempool-empty-msg').removeClass('d-none');
        }

        // Update UTXOs
        const utxoBody = $('#utxo-body');
        if (data.utxo_entries && data.utxo_entries.length > 0) {
            const utxoHtml = data.utxo_entries.map(utxo => `
                <tr>
                    <td class="mono-hash">${utxo.tx_hash}</td>
                    <td class="text-center">${utxo.output_index}</td>
                    <td class="mono-hash">${utxo.recipient_address}</td>
                    <td class="text-end amount-cell">${Number(utxo.amount).toFixed(8)}</td>
                </tr>
            `).join('');
            utxoBody.html(utxoHtml);
            $('#utxo-table-container').removeClass('d-none');
            $('#utxo-empty-msg').addClass('d-none');
        } else {
            utxoBody.empty();
            $('#utxo-table-container').addClass('d-none');
            $('#utxo-empty-msg').removeClass('d-none');
        }

        // Update Chart
        if (this.chart && data.price_chart) {
            this.chart.data.labels = data.price_chart.labels;
            this.chart.data.datasets[0].data = data.price_chart.values;
            this.chart.update('none'); // silent update
        }
    },

    formatTimestamp(ts) {
        if (!ts) return '';
        // If it's a number (unix timestamp), just return it or format it
        return ts; 
    },

    truncate(str, len) {
        if (!str) return '';
        if (str.length <= len) return str;
        return str.substring(0, len) + '...';
    }
};

document.addEventListener('DOMContentLoaded', function () {
    const networkSelect = document.getElementById('network-select');
    const networkForm = document.getElementById('network-form');

    if (networkSelect && networkForm) {
        networkSelect.addEventListener('change', function () {
            networkForm.submit();
        });
    }
});

