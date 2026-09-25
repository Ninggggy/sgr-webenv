export function addMapTitleControl(map, position) {
    const mapTitle = L.control({ position });
    mapTitle.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'info title');
        div.innerHTML = '<div id="mapTitle"></div>';
        div.setAttribute('style', 'text-shadow: 1px 1px #fff;');
        return div;
    };
    mapTitle.addTo(map);
}

export function addMapDateControl(map, position) {
    const mapDate = L.control({ position });
    mapDate.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'info title');
        div.innerHTML = '<div id="mapDate"></div>';
        div.setAttribute('style', 'text-shadow: 1px 1px #fff;');
        return div;
    };
    mapDate.addTo(map);
}

export function addGrayBoxControl(map, position) {
    const grayBox = L.control({ position });
    grayBox.onAdd = function () {
        const div = L.DomUtil.create('div', 'grayBox hidden');

        div.innerHTML = "Record<br>&gt;10% Ties";

        return div;
    };
    grayBox.addTo(map);
}

export function addLogoControl(map, position) {
    const logo = L.control({position});
    logo.onAdd = function(map){
        const div = L.DomUtil.create("div", "logo");
        div.innerHTML = '<div id="logo">' +
                '<img alt="NOAA Logo" width="67" height="67" src="/monitoring-content/lib/images/noaa-logo-67x67.png">' +
            '</div>';
        return div;
    };
    logo.addTo(map);
}

export function addLedgendControl(map, position) {
    const legend = L.control({position});
    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = '<div id="legend"></div>';
        div.setAttribute('style', 'text-shadow: 1px 1px #fff;');
        return div;
    };
    legend.addTo(map);
}

export function addPrintControl(map, position) {
    L.easyPrint({
        title: '',
        position,
        sizeModes: ['A4Landscape', 'A4Portrait', 'Current'],
        defaultSizeTitles: {
            A4Landscape: 'Export as PNG',
            A4Portrait: 'A4 Portrait',
            Current: 'Current Size'
        },
        exportOnly: true,
        filename: 'map',
        hidden: false,
        hideControlContainer: false,
        hideClasses: [
            'reset-bounds',
            'leaflet-control-zoom',
            'leaflet-control-attribution',
            'leaflet-control-easyPrint',
            'hoverInstructions'
        ]
    }).addTo(map);

    map.on('easyPrint-start', function(e) {
        const container = e.target._container;

        const title = container.querySelector('#mapTitle');
        if (title) title.style.whiteSpace = 'nowrap';

        const hoverReturns = container.querySelectorAll('.hoverReturn');
        hoverReturns.forEach(el => {
            el.style.gap = '4%';
        });
    });

    map.on('easyPrint-finished', function(e) {
        const container = e.target._container;
        
        const title = container.querySelector('#mapTitle');
        if (title) title.style.whiteSpace = '';

        const hoverReturns = container.querySelectorAll('.hoverReturn');
        hoverReturns.forEach(el => {
            el.style.gap = '1%';
        });
    });
}