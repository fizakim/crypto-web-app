const Exchange = {
    // some default settings
    config: {
        symbol: '',
        apiUrls: {
            orderBook: '',
            placeOrder: '',
            cancelOrder: ''
        },
        csrfToken: ''
    },

    init(config) {
        // merge the passed config into our defaults
        Object.assign(this.config, config);
        
        if (!this.config.symbol) {
            console.error("No symbol provided to Exchange.init!");
            return;
        }

        this.updateOrderBook();
        // refresh every 3 seconds so the user sees updates
        setInterval(() => this.updateOrderBook(), 3000);
        
        if (this.config.apiUrls.userData) {
            // also refresh user data occasionally to reflect matches
            setInterval(() => this.updateUserData(), 5000);
        }

        this.setupEventListeners();
    },

    formatCurrency(value, decimals = 2) {
        return `\u00A3${Number(value).toFixed(decimals)}`;
    },

    formatCrypto(value, decimals = 8) {
        return Number(value).toFixed(decimals);
    },

    // helper to make the table rows for the order book
    makeRows(rows, rowClass) {
        return rows.map((entry) => {
            var total = entry.price * entry.amount;
            return `
                <tr class="${rowClass}">
                    <td>${this.formatCurrency(entry.price, 8)}</td>
                    <td>${this.formatCrypto(entry.amount)}</td>
                    <td class="text-end">${this.formatCurrency(total, 2)}</td>
                </tr>
            `;
        }).join('');
    },

    updateOrderBook() {
        $.ajax({
            url: `${this.config.apiUrls.orderBook}?network=${this.config.symbol}`,
            method: 'GET',
            success: (data) => this.renderOrderBook(data)
        });
    },

    updateUserData() {
        if (!this.config.apiUrls.userData) return;

        $.ajax({
            url: `${this.config.apiUrls.userData}?network=${this.config.symbol}`,
            method: 'GET',
            success: (data) => this.renderUserData(data)
        });
    },

    renderUserData(data) {
        $('#fiat-balance').text(this.formatCurrency(data.fiat_balance, 2));
        $('#crypto-balance').text(this.formatCrypto(data.crypto_balance));

        const body = $('#open-orders-body');
        const section = $('#open-orders-section');
        const emptyMsg = $('#no-orders-msg');

        if (data.open_orders && data.open_orders.length > 0) {
            const html = data.open_orders.map(order => `
                <tr>
                    <td class="${order.order_type === 'bid' ? 'bid-row' : 'ask-row'} fw-semibold">${order.order_type.toUpperCase()}</td>
                    <td>${this.formatCurrency(order.price, 8)}</td>
                    <td>${this.formatCrypto(order.amount)}</td>
                    <td>${this.formatCrypto(order.filled_amount)}</td>
                    <td>${order.created_at}</td>
                    <td class="text-end">
                        <button type="button" class="btn btn-sm btn-outline-danger btn-cancel"
                            onclick="Exchange.cancelOrder(${order.id})">Cancel</button>
                    </td>
                </tr>
            `).join('');
            body.html(html);
            section.removeClass('d-none');
            emptyMsg.addClass('d-none');
        } else {
            body.empty();
            section.addClass('d-none');
            emptyMsg.removeClass('d-none');
        }
    },

    renderOrderBook(data) {
        if (data.current_price) {
            $('#market-price').text(this.formatCurrency(data.current_price, 2));
        }

        // slice and reverse for asks so they show correctly
        const asks = Array.isArray(data.asks) ? data.asks.slice().reverse() : [];
        const bids = Array.isArray(data.bids) ? data.bids : [];

        if (asks.length === 0) {
            $('#asks-body').html('<tr><td colspan="3" class="empty-note text-center">No asks</td></tr>');
        } else {
            $('#asks-body').html(this.makeRows(asks, 'ask-row'));
        }

        if (bids.length === 0) {
            $('#bids-body').html('<tr><td colspan="3" class="empty-note text-center">No bids</td></tr>');
        } else {
            $('#bids-body').html(this.makeRows(bids, 'bid-row'));
        }

        if (asks.length > 0 && bids.length > 0) {
            const lowestAsk = asks[asks.length - 1].price;
            const highestBid = bids[0].price;
            $('#spread').text(`Spread: ${this.formatCurrency(lowestAsk - highestBid, 8)}`);
        } else {
            $('#spread').text('Spread: --');
        }
    },

    setOrderType(type) {
        $('.type-btn').removeClass('active');
        $(`.type-btn[data-type="${type}"]`).addClass('active');
        $('#order-type').val(type);

        const submitBtn = $('#submit-btn');
        if (type === 'bid') {
            submitBtn.text('Place Bid Order').removeClass('is-ask').addClass('is-bid');
        } else {
            submitBtn.text('Place Ask Order').removeClass('is-bid').addClass('is-ask');
        }
    },

    showMessage(message, isError = false) {
        const box = $('#message-box');
        box.text(message);
        box.removeClass('msg-error msg-success');
        box.addClass(isError ? 'msg-error' : 'msg-success');
        box.show();
        // hide it after 5 seconds
        setTimeout(() => box.fadeOut(), 5000);
    },

    setupEventListeners() {
        $('.type-btn').on('click', (event) => {
            this.setOrderType($(event.currentTarget).data('type'));
        });

        // calculate total when user types
        $('#price, #amount').on('input', () => {
            const price = parseFloat($('#price').val()) || 0;
            const amount = parseFloat($('#amount').val()) || 0;
            $('#total-val').text(this.formatCurrency(price * amount, 2));
        });

        $('#place-order-form').on('submit', (event) => {
            event.preventDefault();

            const btn = $('#submit-btn');
            btn.prop('disabled', true); // stop double clicks

            const payload = {
                network: this.config.symbol,
                order_type: $('#order-type').val(),
                price: $('#price').val(),
                amount: $('#amount').val()
            };

            $.ajax({
                url: this.config.apiUrls.placeOrder,
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.config.csrfToken
                },
                contentType: 'application/json',
                data: JSON.stringify(payload),
                success: (response) => {
                    btn.prop('disabled', false);
                    if (response.status === 'success') {
                        const fillSuffix = response.order_status === 'filled' ? ' (Fully filled!)' : '';
                        this.showMessage(`Order placed successfully${fillSuffix}`);
                        
                        // clean up the form
                        $('#price').val('');
                        $('#amount').val('');
                        $('#total-val').text(this.formatCurrency(0, 2));
                        
                        this.updateOrderBook();
                        this.updateUserData();
                    } else {
                        this.showMessage(response.error || 'Failed to place order', true);
                    }
                },
                error: (xhr) => {
                    btn.prop('disabled', false);
                    let errorMessage = 'Failed to place order';
                    try {
                        errorMessage = JSON.parse(xhr.responseText).error || errorMessage;
                    } catch (error) {
                        // ignore
                    }
                    this.showMessage(errorMessage, true);
                }
            });
        });
    },

    cancelOrder(orderId) {
        if (!confirm('Are you sure you want to cancel this order?')) {
            return;
        }

        $.ajax({
            url: `${this.config.apiUrls.cancelOrder}${orderId}/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': this.config.csrfToken
            },
            success: (response) => {
                if (response.status === 'success') {
                    this.showMessage('Order cancelled successfully');
                    this.updateOrderBook();
                    this.updateUserData();
                } else {
                    alert(`Failed to cancel order: ${response.error}`);
                }
            },
            error: (xhr) => {
                alert(`Error cancelling order. ${xhr.responseText}`);
            }
        });
    }
};
