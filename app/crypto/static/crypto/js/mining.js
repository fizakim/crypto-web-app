$(document).ready(function () {
    let isMining = false;
    let currentBlockTemplate = null;
    let currentNonce = 0;
    let blocksMinedSession = 0;

    let btnStart = $('#btn-start-mining');
    let networkSelect = $('#network-select');
    let difficultyDisplay = $('#mining-difficulty');
    let liveNonce = $('#live-nonce');
    let hashOutput = $('#hash-output');
    let miningStatus = $('#mining-status');
    let blocksMinedDisplay = $('#blocks-mined');
    let lastNonceDisplay = $('#last-nonce-mined');
    let lastHashDisplay = $('#last-hash-mined');

    btnStart.on('click', function () {
        if (isMining) {
            stopMining();
            return;
        }

        let network = networkSelect.val();
        if (!network) {
            alert('Please select a cryptocurrency network.');
            return;
        }

        isMining = true;
        btnStart.text('STOP MINING');
        btnStart.prop('disabled', false);
        blocksMinedSession = 0;
        currentBlockTemplate = null;
        if (blocksMinedDisplay.length) blocksMinedDisplay.text(blocksMinedSession);
        if (lastNonceDisplay.length) lastNonceDisplay.text('--');
        if (lastHashDisplay.length) lastHashDisplay.text('--');
        
        fetchTemplateAndMine();
    });

    function fetchTemplateAndMine() {
        if (!isMining) return;
        
        let network = networkSelect.val();
        if (!currentBlockTemplate) {
            miningStatus.text('Connecting...');
        }
        
        $.ajax({
            url: '/crypto/api/mine/template/',
            data: { network: network },
            method: 'GET',
            success: function (data) {
                if (!isMining) return;
                currentBlockTemplate = data;
                startMiningLoop();
            },
            error: function (xhr) {
                let data = xhr.responseJSON || {};
                alert('Error: ' + data.error);
                if (data.error === 'Login required') {
                    window.location.href = '/users/login/';
                }
                stopMining();
            }
        });
    }

    function startMiningLoop() {
        miningStatus.text('Mining...');
        difficultyDisplay.text(currentBlockTemplate.difficulty);
        currentNonce = currentBlockTemplate.nonce || 0;
        setTimeout(mineStep, 0);
    }

    function stopMining() {
        isMining = false;
        btnStart.text('START MINING');
        btnStart.prop('disabled', false);
        miningStatus.text('Stopped');
    }

    function mineStep() {
        if (!isMining) return;

        let batchSize = 100;
        let index = currentBlockTemplate.index;
        let timestamp = currentBlockTemplate.timestamp;
        let previous_hash = currentBlockTemplate.previous_hash;
        let difficulty = currentBlockTemplate.difficulty;
        let txHashes = "";
        for (let j = 0; j < currentBlockTemplate.transactions.length; j++) {
            txHashes += currentBlockTemplate.transactions[j].tx_hash;
        }

        // Calculate target
        let target = BigInt("0x" + "f".repeat(64)) / BigInt(difficulty);
        console.log(`Mining ${currentBlockTemplate.index} with difficulty ${difficulty}. Target: 0x${target.toString(16)}`);

        for (let i = 0; i < batchSize; i++) {
            if (!isMining) break;

            let header = String(index) + String(timestamp) + previous_hash + String(currentNonce) + String(difficulty) + txHashes;
            let hashHex = CryptoJS.SHA256(header).toString();

            if (i % 10 === 0) {
                liveNonce.text(currentNonce);
                hashOutput.text(hashHex);
            }

            if (BigInt("0x" + hashHex) <= target) {
                liveNonce.text(currentNonce);
                hashOutput.text(hashHex);
                if (lastNonceDisplay.length) lastNonceDisplay.text(currentNonce);
                if (lastHashDisplay.length) lastHashDisplay.text(hashHex);
                
                currentBlockTemplate.nonce = currentNonce;
                
                // Submit block and wait
                submitBlock(currentBlockTemplate).then(() => {
                    if (isMining) {
                        currentBlockTemplate = null; // Reset template
                        fetchTemplateAndMine();
                    }
                }).catch((err) => {
                    console.error("Stopping miner due to submission failure:", err);
                });
                return;
            }

            currentNonce++;
        }

        if (isMining) {
            setTimeout(mineStep, 0);
        }
    }

    function submitBlock(blockData) {
        return new Promise((resolve, reject) => {
            let network = networkSelect.val();
            let csrftoken = getCookie('csrftoken');

            $.ajax({
                url: '/crypto/api/mine/submit/',
                method: 'POST',
                contentType: 'application/json',
                headers: {'X-CSRFToken': csrftoken},
                data: JSON.stringify({
                    network: network,
                    block: blockData
                }),
                success: function (result) {
                    if (result.status === 'success') {
                        console.log(`Successfully mined block ${blockData.index}`);
                        blocksMinedSession++;
                        if (blocksMinedDisplay.length) blocksMinedDisplay.text(blocksMinedSession);
                        resolve(result);
                    } else {
                        console.error(`Block ${blockData.index} rejected:`, result.error || 'Unknown error');
                        alert(`Block ${blockData.index} was rejected by the server: ${result.error}`);
                        reject(result.error);
                    }
                },
                error: function (xhr) {
                    let data = xhr.responseJSON || {};
                    console.error('Network error during block submission:', data.error || 'Server error');
                    alert('Mining Error: ' + (data.error || 'Server rejected the block.'));
                    stopMining();
                    reject(data.error || 'Network error');
                }
            });
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    miningStatus.text('Ready to mine');
});
