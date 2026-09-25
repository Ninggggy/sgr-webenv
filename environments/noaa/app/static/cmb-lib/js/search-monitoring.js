var monitoringProducts = {};

// enter key relocates to first item in list
$(document).keyup(function(e){
    if (
        e.which == 13 &&
        $('#ui-id-1').css('display') != 'none'
    ) {
        window.location = $('#ui-id-1 li:first-of-type a').attr('href');
        return false;
    }
});

$(function(){
    // automatically clear value on focus
    $('#search-monitoring').focus(function(){ this.value = ''; });

    $.ajax({
        url: '/monitoring-content/lib/reference/products.json',
        dataType: 'json'
    }).done(function(response){
        monitoringProducts = Object.values(response.products).filter(function(product) {
            return product.hideSearch !== true;
        });
        monitoringSearch();
    });
});

function monitoringSearch(){
    if ($('#search-monitoring').length > 0) {
        $('#search-monitoring').autocomplete({
            minLength: 0,
            source: searchMonitoringProducts,
            focus: function(event, ui) {
                $('#search-monitoring').val(ui.item.name);
                return false;
            },
            select: function(event, ui) {
                $('#search-monitoring').val(ui.item.name);
                window.location = ui.item['approotpath'];

                return false;
            }
        }).autocomplete('instance')._renderItem = function(ul, item) {
            return $('<li>')
                .append(
                    '<div>' +
                        '<a href="' + item["approotpath"] + '">' +
                            '<div class="monitoring-product-name">' +
                                item.name.replace('El Nino', 'El Ni&ntilde;o') +
                            '</div>' +
                            '<div class="monitoring-product-description">' +
                                item.description.replace('El Nino', 'El Ni&ntilde;o') +
                            '</div>' +
                        '</a>' +
                    '</div>'
                )
                .appendTo(ul);
        };
    }
    $('.ui-front').css('z-index', '1001');
}

function searchMonitoringProducts(request, response){
    if (request.term === '') {
        response([]);
        return;
    }

    function hasMatch(search){
        return search.toLowerCase().indexOf(request.term.toLowerCase()) !== -1;
    }

    var matches = [];
    $.each(monitoringProducts, function(ndx, monitoringProduct){
        if (
            hasMatch(monitoringProduct.name) ||
            hasMatch(monitoringProduct.description) ||
            hasMatch(monitoringProduct.keywords) ||
            hasMatch(monitoringProduct['docrootpath']) ||
            hasMatch(monitoringProduct['approotpath'])
        ) {
            matches.push(monitoringProduct);
        }
    });
    response(matches);
}