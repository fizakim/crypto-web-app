$(document).ready(function () {
    let networkSelect = $('#network-select');
    let tableBody = $('#blocks-table-body');
    let emptyState = $('#blocks-empty-state');
    let tableContainer = $('#blocks-table-container');
    let networkNameSpan = $('#active-network-name');
    let emptyStateNetworkName = $('#empty-state-network-name');

    let form = $('.network-form');
    form.on('submit', function (e) {
        e.preventDefault();
    });

    networkSelect.on('change', function () {
        let selectedOption = $(this).find('option:selected');
        fetchBlocks($(this).val(), selectedOption.data('name'));
    });

    function truncate(str, len) {
        return str.length > len ? str.substring(0, len) + '...' : str;
    }

    function fetchBlocks(symbol, name) {
        networkNameSpan.text(name);
        emptyStateNetworkName.text(name);

        $.ajax({
            url: "/crypto/api/blocks/",
            data: { network: symbol },
            method: 'GET',
            dataType: 'json',
            success: function (data) {
                // console.log("data received");
                // console.log(data);
                let blocks = data.chain || [];

                if (blocks.length > 0) {
                    tableContainer.show();
                    emptyState.hide();

                    tableBody.empty();
                    $.each(blocks, function (index, block) {
                        let tr = $('<tr>').html(
                            "<td>" + block.index + "</td>" +
                            "<td class='hash-cell' title='" + block.block_hash + "'>" + truncate(block.block_hash, 20) + "</td>" +
                            "<td class='hash-cell' title='" + block.previous_hash + "'>" + truncate(block.previous_hash, 20) + "</td>" +
                            "<td>" + block.timestamp + "</td>" +
                            "<td>" + block.nonce + "</td>"
                        );
                        tableBody.append(tr);
                    });
                } else {
                    tableContainer.hide();
                    emptyState.show();
                }
            },
            error: function (xhr, status, error) {
                console.log('error fetching blocks:', error);
            }
        });
    }
});
