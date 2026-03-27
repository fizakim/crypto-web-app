
document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    document.getElementById('receiver-hash').addEventListener('input', function (e) {
        const val = e.target.value;
        document.getElementById('receiver-hash-display').innerText = val ? val : '---';
        if (val.length > 5) {
            document.getElementById('receiver-status').innerText = 'Validating...';
            setTimeout(() => {
                document.getElementById('receiver-status').innerText = 'Address Identified';
                document.getElementById('receiver-status').style.color = '#4ade80';
            }, 500);
        } else {
            document.getElementById('receiver-status').innerText = 'Pending Address...';
            document.getElementById('receiver-status').style.color = '#ffffff';
        }
    });

    document.getElementById('send-amount').addEventListener('input', function (e) {
        const amount = parseFloat(e.target.value) || 0;
        const coinType = document.getElementById('coin-type').value || '';
        document.getElementById('receiver-expected-amount').innerText = amount.toFixed(4) + ' ' + coinType;
    });

    document.getElementById('coin-type').addEventListener('change', function (e) {
        const amount = parseFloat(document.getElementById('send-amount').value) || 0;
        const coinType = e.target.value;
        document.getElementById('receiver-expected-amount').innerText = amount.toFixed(4) + ' ' + coinType;

        if (coinType) {
            document.getElementById('sender-hash').innerText = 'Fetching...';
            document.getElementById('sender-balance').innerText = '...';

            fetch(`/crypto/api/wallet/info/?network=${coinType}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        document.getElementById('sender-hash').innerText = 'Error';
                        document.getElementById('sender-balance').innerText = '---';
                    } else {
                        document.getElementById('sender-hash').innerText = data.address;
                        document.getElementById('sender-balance').innerText = parseFloat(data.balance).toFixed(8);
                    }
                })
                .catch(err => {
                    console.error('Error fetching wallet info:', err);
                });
        }
    });

    document.getElementById('btn-submit-transfer').addEventListener('click', function(e) {
        e.preventDefault();
        
        const network = document.getElementById('coin-type').value;
        const recipient_address = document.getElementById('receiver-hash').value.trim();
        const amount = document.getElementById('send-amount').value;

        if (!network || !recipient_address || !amount || parseFloat(amount) <= 0) {
            alert('Please fill out all fields with valid information.');
            return;
        }

        this.disabled = true;
        this.innerText = 'Sending...';

        fetch('/crypto/api/transfer/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                network: network,
                recipient_address: recipient_address,
                amount: amount
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert('Transfer submitted successfully!');
                document.getElementById('send-amount').value = '';
                document.getElementById('receiver-hash').value = '';
                document.getElementById('receiver-hash-display').innerText = '---';
                document.getElementById('receiver-expected-amount').innerText = '0.00';
                
                // Refresh balance
                document.getElementById('coin-type').dispatchEvent(new Event('change'));
            }
        })
        .catch(err => {
            alert('An unexpected error occurred submitting the transfer.');
            console.error(err);
        })
        .finally(() => {
            this.disabled = false;
            this.innerText = 'Send Coins';
        });
    });
});
