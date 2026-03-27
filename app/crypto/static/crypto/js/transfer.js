const TransferPage = {
    config: {
        walletInfoUrl: '',
        transferUrl: '',
        isAuthenticated: false
    },

    init(config) {
        this.config = { ...this.config, ...config };

        this.elements = {
            form: document.getElementById('transfer-form'),
            csrfToken: document.querySelector('[name=csrfmiddlewaretoken]'),
            coinType: document.getElementById('coin-type'),
            receiverHash: document.getElementById('receiver-hash'),
            sendAmount: document.getElementById('send-amount'),
            submitBtn: document.getElementById('btn-submit-transfer'),
            messageBox: document.getElementById('transfer-message'),
            senderHash: document.getElementById('sender-hash'),
            senderBalance: document.getElementById('sender-balance'),
            receiverStatus: document.getElementById('receiver-status'),
            receiverHashDisplay: document.getElementById('receiver-hash-display'),
            receiverExpectedAmount: document.getElementById('receiver-expected-amount')
        };

        if (!this.elements.form) {
            return;
        }

        this.setupEventListeners();
    },

    setMessage(message, isError = false) {
        const { messageBox } = this.elements;
        if (!messageBox) {
            return;
        }

        messageBox.textContent = message;
        messageBox.classList.remove('msg-success', 'msg-error');
        messageBox.classList.add(isError ? 'msg-error' : 'msg-success');
        messageBox.style.display = 'block';

        window.clearTimeout(this.messageTimer);
        this.messageTimer = window.setTimeout(() => {
            messageBox.style.display = 'none';
        }, 5000);
    },

    updateStatusLabel(text, isValid) {
        const el = this.elements.receiverStatus;
        if (!el) {
            return;
        }
        el.textContent = text;
        el.classList.remove('status-valid', 'status-pending');
        el.classList.add(isValid ? 'status-valid' : 'status-pending');
    },

    updateReceiverHashDisplay(value) {
        const output = value || '---';
        const el = this.elements.receiverHashDisplay;
        if (el) {
            el.textContent = output;
        }
    },

    updateExpectedReceived() {
        const amount = parseFloat(this.elements.sendAmount?.value || '0') || 0;
        const coinType = this.elements.coinType?.value || '';
        const value = `${amount.toFixed(4)}${coinType ? ` ${coinType}` : ''}`;

        const el = this.elements.receiverExpectedAmount;
        if (el) {
            el.textContent = value;
        }
    },

    async refreshWalletInfo() {
        if (!this.config.isAuthenticated) {
            return;
        }

        const symbol = this.elements.coinType?.value;
        if (!symbol) {
            if (this.elements.senderHash) {
                this.elements.senderHash.textContent = 'Select a network to load wallet address';
            }
            if (this.elements.senderBalance) {
                this.elements.senderBalance.textContent = '--';
            }
            return;
        }

        if (this.elements.senderHash) {
            this.elements.senderHash.textContent = 'Fetching...';
        }
        if (this.elements.senderBalance) {
            this.elements.senderBalance.textContent = '...';
        }

        try {
            const response = await fetch(`${this.config.walletInfoUrl}?network=${encodeURIComponent(symbol)}`);
            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || 'Failed to load wallet info');
            }

            if (this.elements.senderHash) {
                this.elements.senderHash.textContent = data.address;
            }
            if (this.elements.senderBalance) {
                const balance = Number.parseFloat(data.balance);
                this.elements.senderBalance.textContent = Number.isNaN(balance)
                    ? '--'
                    : `${balance.toFixed(8)} ${symbol}`;
            }
        } catch (error) {
            if (this.elements.senderHash) {
                this.elements.senderHash.textContent = 'Error loading wallet';
            }
            if (this.elements.senderBalance) {
                this.elements.senderBalance.textContent = '--';
            }
            this.setMessage(error.message || 'Failed to load wallet info', true);
        }
    },

    async submitTransfer() {
        if (!this.config.isAuthenticated) {
            this.setMessage('Please log in to submit transfers.', true);
            return;
        }

        const network = this.elements.coinType?.value || '';
        const recipientAddress = (this.elements.receiverHash?.value || '').trim();
        const amount = this.elements.sendAmount?.value || '';

        if (!network || !recipientAddress || !amount || parseFloat(amount) <= 0) {
            this.setMessage('Please fill out all fields with valid values.', true);
            return;
        }

        const submitBtn = this.elements.submitBtn;
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Sending...';
        }

        try {
            const response = await fetch(this.config.transferUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.elements.csrfToken?.value || ''
                },
                body: JSON.stringify({
                    network,
                    recipient_address: recipientAddress,
                    amount
                })
            });

            const data = await response.json();
            if (!response.ok || data.error) {
                throw new Error(data.error || 'Transfer failed');
            }

            this.setMessage('Transfer submitted successfully.');
            if (this.elements.sendAmount) {
                this.elements.sendAmount.value = '';
            }
            if (this.elements.receiverHash) {
                this.elements.receiverHash.value = '';
            }
            this.updateReceiverHashDisplay('');
            this.updateStatusLabel('Pending Address...', false);
            this.updateExpectedReceived();
            await this.refreshWalletInfo();

            window.setTimeout(() => {
                window.location.reload();
            }, 900);
        } catch (error) {
            this.setMessage(error.message || 'An unexpected error occurred.', true);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Send Coins';
            }
        }
    },

    setupEventListeners() {
        this.elements.receiverHash?.addEventListener('input', (event) => {
            const value = event.target.value.trim();
            this.updateReceiverHashDisplay(value);

            if (value.length > 5) {
                this.updateStatusLabel('Address Identified', true);
            } else {
                this.updateStatusLabel('Pending Address...', false);
            }
        });

        this.elements.sendAmount?.addEventListener('input', () => {
            this.updateExpectedReceived();
        });

        this.elements.coinType?.addEventListener('change', async () => {
            this.updateExpectedReceived();
            await this.refreshWalletInfo();
        });

        this.elements.form.addEventListener('submit', async (event) => {
            event.preventDefault();
            await this.submitTransfer();
        });

        this.updateExpectedReceived();
        this.updateStatusLabel('Pending Address...', false);
    }
};
