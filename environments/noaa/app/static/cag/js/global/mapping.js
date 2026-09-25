import { cag, base, scope, section, monthNames } from '../globals.js';
import { initYearRange } from '../shared/year-ranges.js';
import { buildReturnOptions } from '../shared/mapping/return-types.js';
import { getMapTitle } from '../shared/mapping/map-title.js';
import { MappingDao } from '../shared/dao/MappingDao.js';
import {
    addLedgendControl,
    addLogoControl,
    addMapTitleControl,
    addMapDateControl,
    addGrayBoxControl,
    addPrintControl
} from '../shared/mapping/leafletControls.js';
import { buildBinnedLegendHtml, buildRankLegendHtml, loadLegendConfig } from '../shared/mapping/legend.js';
import { setDesignation } from '../shared/designations.js';
import { computeAndRenderPrevNext, makePrevNextClick } from '../shared/mapping/prev-next-utils.js';
import { valuesTableSorter } from "../shared/tablesorter.js";
import { fetchJson } from '../utils/fetch.js'
import Util from '../utils/util.js'

let activeLegend = { bins: [], colors: [] };
const values      = {};
const numYears    = {};
const rankBins    = {};
const parameters  = cag.constants.parameters;
const basePeriods = cag.constants.basePeriods.global;

const dao = new MappingDao();

const updateUrl = Util.config.updateUrl;
const getVal    = Util.form.getVal;
const isRank    = returnType => returnType === 'rank';
const isMean    = returnType => returnType === 'mean';
const isAnom    = returnType => returnType === 'anomaly';
const isTavg    = param => param === 'tavg';
const isPcp     = Util.parameter.is.precip;

const {insufficientVariability: isInsufficientVariability } = Util.is;

let basePeriod = Object.values(basePeriods[isTavg(cag.variables.parameter) ? 'gridded' : 'pcp']).join('-');
let gridCenter;

let globalMap, grid, colorLayer, valueLayer,
    countries, countryBorders, graticules, graticulesLayer,
    worldExtent, worldExtentLayer;

export async function initGlobalMapping() {
    const { year, month, parameter, returnType } = cag.variables;

    await buildReturnOptions(cag.constants.returns, cag.variables.returnType, scope, parameter);
    configGlobalMapping();

    initYearRange('gridded', parameter);
    fillGlobalMappingMonths();

    document.querySelector(`.return-selection[value="${returnType}"]`).checked = true;

    getGlobalMappingPrevNext(parameter, year, month, returnType);

    cag.variables.url = getGlobalMappingUrl();

    drawMap();

    document.getElementById('year').addEventListener('change', fillGlobalMappingMonths);

    document.getElementById('parameter').addEventListener('change', ({ target }) => {
        initYearRange('gridded', target.value);
        fillGlobalMappingMonths();
    });

    document.getElementById('submit').addEventListener('click', (event) => {
        event.preventDefault();
        globalMappingFormSubmit();
    });

    document.getElementById('return').addEventListener('change', e => {
        if (e.target.name === 'return') {
            globalReturnChange();
        }
    });
}

function globalMappingFormSubmit(){
    if (!cag.variables.formChanged) {
        updateUrl();
        return false;
    }

    const newMap = document.getElementById('parameter').value !== cag.variables.parameter;

    Object.assign(cag.variables, {
        parameter:   getVal('parameter'),
        year:        Number(getVal('year')),
        month:       Number(getVal('month')),
        returnType:  getSelectedReturnType(),
        formState:   $('#select-form').serialize(),
        formChanged: false
    });

    const { parameter, year, month, returnType } = cag.variables;

    getGlobalMappingPrevNext(parameter, year, month, returnType);

    if (newMap) {
        drawMap();
    } else {
        plotValues();
    }

    pushState(cag.variables);

    // cache
    const cacheUrl = `${base}/${scope}/${section}/cache/?` + cag.variables.formState;
    fetch(cacheUrl, { credentials: "include" })
        .then(res => {
            if (!res.ok) throw new Error(`cache request failed ${cacheUrl}`);
        });
}

function globalReturnChange(){
    cag.variables.formChanged = true;

    cag.variables.returnType = document.querySelector('#return input[name="return"]:checked').value;

    $('#prev a, #next a')
        .data('return', cag.variables.returnType)
        .each(function() {
            const p = $(this).data('parameter');
            const d = $(this).data('date');
            const r = $(this).data('return');

            const href = `${base}/${scope}/mapping/${p}/${d}/${r}`;

            $(this).attr('href', href);
        });

    setMapDateTitle();
    plotMapValuesLayer();
    getGlobalMappingPrevNext(
        cag.variables.parameter,
        cag.variables.year,
        cag.variables.month,
        cag.variables.returnType
    );
    pushState(cag.variables);
}

function getSelectedReturnType() {
    const el = document.querySelector('#return input[name="return"]:checked:enabled');
    
    return el?.value ?? (isTavg(cag.variables.parameter) ? 'anomaly' : 'value');
}

function getGlobalMappingUrl() {
    const { parameter, year, month, returnType } = cag.variables;
    const date = year + (month < 13 ? String(month).padStart(2, '0') : '');
    return `${base}/${scope}/${section}/${parameter}/${date}/${returnType}`;
}

function pushState({
    parameter,
    year,
    month,
    returnType
}) {

    const pageState = { parameter, year, month, returnType };

    cag.variables.url = getGlobalMappingUrl();

    window.history.pushState(pageState, null, cag.variables.url);
}

/**
 * Map
 * Robinson Projection if screen >= 992px
 */
function robinsonProjection() {
    if ($('body').width() >= 992) {
        // topojson stuff
        L.TopoJSON = L.GeoJSON.extend({
            addData: function(jsonData) {
                if (jsonData.type === 'Topology') {
                    for (key in jsonData.objects) {
                        geojson = topojson.feature(jsonData, jsonData.objects[key]);
                        L.GeoJSON.prototype.addData.call(this, geojson);
                    }
                } else {
                    L.GeoJSON.prototype.addData.call(this, jsonData);
                }
            }
        });
        // Copyright (c) 2013 Ryan Clark

        const topoLayer = new L.TopoJSON();

        // D3 Projection
        const proj = d3.geoRobinson().scale(.5);
        const MapProjection = {
            project: function(latLng) {
                const point = proj([latLng.lng, latLng.lat]);
                return point ?
                    new L.Point(point[0], point[1]) :
                        new L.Point(0, 0);
            },
            unproject: function(point) {
                const latLng = proj.invert([point.x, point.y]);
                return new L.LatLng(latLng[1], latLng[0]);
            }
        }
        const MapCRS = L.extend({}, L.CRS, {
            projection: MapProjection,
            transformation: new L.Transformation(1, 0, 1, 0),
            infinite: true
        });

        return MapCRS;
    }
    return false;
}

function configGlobalMapping() {
    const globalMapOptions = {
        center             : [0, 0],
        zoom               : 0,
        zoomDelta          : 0.25,
        zoomSnap           : 0,
        dragging           : false,
        zoomControl        : false,
        boxZoom            : false,
        doubleClickZoom    : false,
        scrollWheelZoom    : false,
        tap                : false,
        touchZoom          : false,
        zoomControl        : false,
        attributionControl : false
    };

    const mapCRS = robinsonProjection();
    if (mapCRS) {
        globalMapOptions.crs = mapCRS;
    }

    globalMap = L.map('map-canvas', globalMapOptions);

    addLedgendControl(globalMap, 'bottomright');
    addLogoControl(globalMap, 'bottomleft');
    addMapTitleControl(globalMap, 'topleft');
    addMapDateControl(globalMap, 'topright');
    addGrayBoxControl(globalMap, 'bottomright');
    addPrintControl(globalMap, 'bottomright');

    /**
     * easyPrint CSS Hack
     * move elements that easyPrint does not handle well.
     */
    $('.easyPrintHolder a').click(function(){
        $('.leaflet-bottom').css('margin-bottom', '12px');
        $('.leaflet-top.leaflet-right').css('margin-right', '12px');
    });
    /**********************/
    /* easyPrint CSS Hack */
}

async function drawMap() {
    resetZoom();

    // Show loader overlay
    const overlayHtml = `
        <div id="geojson-loader-overlay" class="loader-overlay">
            <img class="noaa-loader" src="/monitoring-content/lib/images/noaa-loader.gif">
        </div>
    `;

    const dataLoaderOverlay = document.querySelector('#data-loader-overlay');
    if (!dataLoaderOverlay) {
        document.querySelector('#dynamic-content').insertAdjacentHTML('afterbegin', overlayHtml);
    } else {
        const geojsonOverlay = document.querySelector('#geojson-loader-overlay');
        if (geojsonOverlay) {
            geojsonOverlay.outerHTML = overlayHtml;
        }
    }

    const gridSize = isTavg(cag.variables.parameter) ? '5x5' : '2.5x2.5';
    const geoJson = '/monitoring-content/lib/geojson';
    [grid, countries, graticules, worldExtent] = await Promise.all([
        fetchJson(`${geoJson}/global/global-${gridSize}-grid.geojson`, { context: 'Global Mapping Grid', fallback: null }),
        fetchJson(`${geoJson}/global/world-countries.geojson`, { context: 'Global Mapping Countries', fallback: null }),
        fetchJson(`${geoJson}/global/ne_50m_graticules_20.geojson`, { context: 'Global Mapping Graticules', fallback: null }),
        fetchJson(`${geoJson}/global/ne_50m_wgs84_bounding_box.geojson`, { context: 'Global Mapping Bounding Box', fallback: null })
    ]);
    if (grid && countries && graticules && worldExtent) {
        plotValues();
        document.querySelector('#geojson-loader-overlay')?.remove();
    } else {
        document.querySelector('#geojson-loader-overlay').innerHTML = `
        <div class="error-msg red-txt bold bigPadTop">
            Map boundaries did not load. Please, <a onclick="location.reload();" href="#">try again.</a>
        </div>`;
    }
}

function setGlobalBasePeriod() {
    const key = isTavg(cag.variables.parameter) ? 'gridded' : 'pcp';
    basePeriod = Object.values(basePeriods[key]).join('-');
}

function setNumYears() {
    Object.entries(parameters).forEach(([param, attr]) => {
        const { minDate, maxDate } = attr;

        const maxMonth = +String(maxDate).slice(4, 6);
        const nmon = cag.variables.month == 13 ? 12 : cag.variables.month;

        const years = Util.numYears(minDate, maxDate, maxMonth, nmon);
        numYears[param] = years;

        rankBins[param] = Util.ranks.thresholds(years);
    });
}

function countryBordersStyle(feature) {
    return {
        weight:      .5,
        opacity:     1,
        color:       'gray',
        fillOpacity: 0
    };
}

function graticuleStyle(feature) {
    return {
        weight:     .33,
        opacity:    1,
        color:      'gray',
        fillOpacity: 0
    };
}

function worldExtentStyle(feature) {
    return {
        weight:      .5,
        opacity:     1,
        color:       '#000',
        fillOpacity: 1,
        fillColor:   '#ffffff'
    };
}

function colorLayerStyle(feature) {
    return {
        weight:      0,
        opacity:     0,
        color:       'transparent',
        fillOpacity: 1,
        fillColor:   getGlobalMappingColor(
            values
            [cag.variables.parameter]
            [cag.variables.returnType]
            [feature.properties.top]
            [feature.properties.right]
            [feature.properties.bottom]
            [feature.properties.left],
            values
            [cag.variables.parameter]
            ['ties']
            [feature.properties.top]
            [feature.properties.right]
            [feature.properties.bottom]
            [feature.properties.left]
        )
    };
}

function valueLayerStyle(feature) {
    return {
        weight:      0,
        opacity:     0,
        color:       'transparent',
        fillOpacity: 0
    };
}

function gridPopup(e) {
    highlightFeature(e);

    const { lat, lng } = e.latlng;
    const [centerLat, centerLng] = getCenterCoords(lat, lng);

    const latDir = lat < 0 ? 'S' : 'N';
    const lngDir = lng < 0 ? 'W' : 'E';
    const displayLat = `${Math.abs(centerLat)}&deg;${latDir}`;
    const displayLng = `${Math.abs(centerLng)}&deg;${lngDir}`;

    let content = `<div class="center bold">${displayLat}, ${displayLng}</div>`;

    // Collect enabled return types and labels
    const returns = {};
    $('#return input[name="return"]:not(:disabled)').each(function () {
        const id = this.id;
        returns[this.value] = $(`label[for="${id}"]`).text();
    });

    const { top, right, bottom, left } = e.target.feature.properties;
    const param          = cag.variables.parameter;
    const ties           = values[param].ties[top][right][bottom][left];
    const isInsufficient = isInsufficientVariability(ties, numYears[param]);

    Object.entries(returns).forEach(([returnValue, returnText]) => {
        const value = values[param][returnValue][top][right][bottom][left];
        const dispVal = getDisplayValue(value, returnValue);

        const des = setDesignation(ties, isInsufficient, 'global', returnValue);

        content += `
            <div class="mapTooltipValues small">
                <div>${returnText}:</div>
                <div>${dispVal}${des}</div>
            </div>`;
    });

    valueLayer
        .bindTooltip(content, {
            sticky: true,
            className: 'mapTooltip'
        })
        .addTo(globalMap);
}

function getDisplayValue(value, returnValue) {
    const param = cag.variables.parameter;

    if ((!value && value != 0) || value === null || isNaN(value)) {
        return '--';
    } else {
        const roundedValue = isRank(returnValue)
            ? Math.floor(value)
            : returnValue === 'pctavg'
                ? parseFloat(value).toFixed(1)
                : parseFloat(value).toFixed(parameters[param].precision);
        const sym = (isAnom(returnValue) && value > 0 ? '+' : '');
        const units = returnValue === 'pctavg' ? '%' : parameters[param].units;

        return (roundedValue === 0
                ? (returnValue === 'pctavg' ? '0.0' : '0.00')
                : sym + roundedValue) + (isRank(returnValue) ? '' : units);
    }
}

function highlightFeature(e) {
    const layer = e.target;

    layer.setStyle({
        weight:      1,
        opacity:     1,
        color:       'black',
        fillOpacity: 0
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

function resetHighlight(e) {
    valueLayer.resetStyle(e.target);
}

function resetZoom(){
    globalMap.fitBounds(
        [[-90, -180], [90, 180]],
        {
            paddingTopLeft: [0, window.innerWidth >= 1199 ? 35 : 50],
            paddingBottomRight: [0, 40]
        }
    );
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: gridPopup,
        mouseout:  resetHighlight,
        click:     goToGridTimeSeries
    });
}

async function plotValues() {
    setNumYears();
    setGlobalBasePeriod();

    $(`
        #return [value="value"],
        #return [value="value"] + label,
        #return [value="mean"],
        #return [value="mean"] + label,
        #return [value="pctavg"],
        #return [value="pctavg"] + label
    `).prop('disabled', (isTavg(cag.variables.parameter) ? true : false));

    gridCenter = parameters[cag.variables.parameter].gridCenter;

    /**
     * If previously plotted map was exported as PNG with easyPrint,
     * this undoes the CSS hack which moves the elements
     * which easyPrint does not handle well.
     */
    $('.leaflet-bottom').css('margin-bottom', '0');
    $('.leaflet-top.leaflet-right').css('margin-right', '0');
    /*******************************************************/

    const selectedReturnType = getSelectedReturnType();
    if (cag.variables.returnType != selectedReturnType) {
        cag.variables.returnType = selectedReturnType;
        document.querySelector(`#return [value="${cag.variables.returnType}"]`).checked = true;
        pushState(cag.variables);
    }

    setMapDateTitle();

    $('#reset-zoom').click(resetZoom);

    $('#designations, #designations > *').addClass('hidden');

    const { year, month, parameter } = cag.variables;
    const date = year + String(month).padStart(2, '0');
    const dataUrl = `${base}/${scope}/${section}/${parameter}/${month == 13 ? year : date}`;

    const loaderGif = '/monitoring-content/lib/images/noaa-loader.gif';

    if ($('#data-loader-overlay').length === 0) {
        const loaderOverlay = document.createElement('div');
        loaderOverlay.id = 'data-loader-overlay';
        loaderOverlay.className = 'loader-overlay';

        const loaderImg = document.createElement('img');
        loaderImg.className = 'noaa-loader';
        loaderImg.src = loaderGif;

        loaderOverlay.appendChild(loaderImg);
        $('#dynamic-content').prepend(loaderOverlay);
    } else {
        const loaderOverlay = document.getElementById('data-loader-overlay');
        loaderOverlay.className = 'loader-overlay white-bg';

        const newLoaderImg = document.createElement('img');
        newLoaderImg.className = 'noaa-loader';
        newLoaderImg.src = loaderGif;

        loaderOverlay.innerHTML = '';
        loaderOverlay.appendChild(newLoaderImg);
    }

    const data = await dao.getMappingData('global', cag.variables);

    if (data.length === 0) {
        displayNoData();
        return false;
    }

    Util.config.configDownload(dataUrl);

    const enabledReturns = document.querySelectorAll('#return input[name="return"]:enabled');

    const tbody = document.createElement('tbody');

    $.each(data, function(gridPoint, gridAttributes){
        const lat    = parseFloat(gridAttributes.coordinates.latitude);
        // set lon to +/-180 (instead of 0-360)
        const lon360 = parseFloat(gridAttributes.coordinates.longitude);
        const lon    = (lon360 > 180 ? lon360 - 360 : lon360);
        const top    = lat + gridCenter;
        const right  = lon + gridCenter;
        const bottom = lat - gridCenter;
        const left   = lon - gridCenter;

        const row = document.createElement('tr');
        const ties = parseInt(gridAttributes.ties) || 0;
        const isInsufficient = isInsufficientVariability(ties, numYears[parameter]);

        if (ties > 0) {
            $('#designations').removeClass('hidden');
            $('#' + (isInsufficient ? 'insufficient-variability' : 'tie') + '-designation').removeClass('hidden');
        }

        values[parameter] ??= {};
        values[parameter].ties ??= {};
        values[parameter].ties[top] ??= {};
        values[parameter].ties[top][right] ??= {};
        values[parameter].ties[top][right][bottom] ??= {};
        values[parameter].ties[top][right][bottom][left] = ties;

        const latCell = document.createElement('td');
        latCell.setAttribute('data-sortval', lat);
        const latText = Math.abs(lat) + '&deg;' + (lat >= 0 ? 'N' : 'S');
        latCell.innerHTML = latText;
        row.appendChild(latCell);

        const lonCell = document.createElement('td');
        lonCell.setAttribute('data-sortval', lon360);
        const lonText = Math.abs(lon) + '&deg;' + (lon >= 0 ? 'E' : 'W');
        lonCell.innerHTML = lonText;
        row.appendChild(lonCell);

        // loop through return types
        enabledReturns.forEach(input => {
            const returnKey = input.id;
            const value = gridAttributes[returnKey];

            values[parameter] ??= {};
            values[parameter][returnKey] ??= {};
            values[parameter][returnKey][top] ??= {};
            values[parameter][returnKey][top][right] ??= {};
            values[parameter][returnKey][top][right][bottom] ??= {};
            values[parameter][returnKey][top][right][bottom][left] = value;

            const dataCell = document.createElement('td');
            dataCell.className = returnKey;
            if (value === null) {
                dataCell.setAttribute('data-sortval', '');
                dataCell.textContent = '--';
            } else {
                const val = isRank(returnKey) ? Math.floor(value) : parseFloat(value);
                const displayValue = getDisplayValue(val, returnKey);

                dataCell.setAttribute('data-sortval', val);
                dataCell.innerHTML = displayValue +
                    (returnKey === 'rank' ? setDesignation(ties, isInsufficient) : '');
            }
            row.appendChild(dataCell);
        });

        tbody.appendChild(row);
    });

    // world extent using values set above
    if (worldExtentLayer && globalMap.hasLayer(worldExtentLayer)) {
        globalMap.removeLayer(worldExtentLayer);
    }
    worldExtentLayer = L.geoJson(worldExtent, {
        style: worldExtentStyle,
    }).addTo(globalMap);

    plotMapValuesLayer();

    const dateDisplay = getGlobalMappingDateDisplay(year, month);
    const parameterTitle = parameters[parameter].title;
    const caption = `${dateDisplay} ${parameterTitle}`;

    const table = document.createElement('table');
    table.id = 'values-table';
    table.className = 'bordered shading';

    const captionElement = document.createElement('caption');
    captionElement.textContent = caption;
    table.appendChild(captionElement);

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const subHeaderRow = document.createElement('tr');

    let groupHeaderAdded = false;

    // Latitude & Longitude
    ['Latitude', 'Longitude'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        if (!isTavg(parameter)) th.rowSpan = 2; // No rowspan for tavg
        headerRow.appendChild(th);
    });

    enabledReturns.forEach(input => {
        const returnValue = input.id;
        const th = document.createElement('th');
        const labelElement = document.querySelector(`#return label[for="${returnValue}"]`);
        th.textContent = (returnValue === 'mean' ? 'Period ' : '') +
            (labelElement ? labelElement.title : returnValue[0].toUpperCase() + returnValue.slice(1));

        // Special Case: tavg (Flat single-row header)
        if (isTavg(parameter)) {
            if (isAnom(returnValue)) {
                const meanDiv = document.createElement('div');
                meanDiv.className = 'small';
                meanDiv.textContent = `${basePeriod} Average`;
                th.appendChild(meanDiv);
            }
            if (isRank(returnValue)) {
                const numYearsDiv = document.createElement('div');
                numYearsDiv.className = 'small';
                numYearsDiv.textContent = (numYears[parameter] || '') + ' Years';
                th.appendChild(numYearsDiv);
            }
            headerRow.appendChild(th);
        } 
        // Standard Case: Grouped multi-row header
        else {
            const isGrouped = ['mean', 'anomaly', 'pctavg'].includes(returnValue);

            if (isGrouped) {
                if (!groupHeaderAdded) {
                    const groupTh = document.createElement('th');
                    groupTh.className = 'center normal-font-weight';
                    groupTh.textContent = `Period: ${basePeriod}`;
                    groupTh.colSpan = 3;
                    headerRow.appendChild(groupTh);
                    groupHeaderAdded = true;
                }

                subHeaderRow.appendChild(th);
            } else {
                th.rowSpan = 2;
                if (isRank(returnValue)) {
                    const numYearsDiv = document.createElement('div');
                    numYearsDiv.className = 'small';
                    numYearsDiv.textContent = (numYears[parameter] || '') + ' Years';
                    th.appendChild(numYearsDiv);
                }
                headerRow.appendChild(th);
            }
        }
    });

    thead.appendChild(headerRow);

    // Only add the sub-row if we aren't in tavg mode and actually have grouped items
    if (!isTavg(parameter) && subHeaderRow.children.length > 0) {
        thead.appendChild(subHeaderRow);
    }
    table.appendChild(thead);
    table.appendChild(thead);
    table.appendChild(tbody);

    document.getElementById('data-table').replaceChildren(table);
    valuesTableSorter('#values-table', cag.constants.section);

    $('.loader-overlay').remove();
}

function setMapDateTitle() {
    const { year, month, returnType } = cag.variables;
    const mapDateTitle = isMean(returnType) ? monthNames[month - 1] : getGlobalMappingDateDisplay(year, month, true);
    $('#mapDate').html(mapDateTitle);
}

function getLegend() {
    const { parameter, returnType } = cag.variables;
    const { bins, colors } = activeLegend;

    if (returnType === 'rank') {
        const isWet = isPcp(parameter);
        const lowLabel = isWet ? 'Driest' : 'Coldest';
        const highLabel = isWet ? 'Wettest' : 'Warmest';
        
        document.getElementById('legend').innerHTML = buildRankLegendHtml(colors, bins, lowLabel, highLabel);
        document.getElementById('legend').classList.add('rank-legend');
    } else {
        const units = returnType === 'pctavg' ? '%' : ' ' + parameters[parameter].units;
        
        const html = buildBinnedLegendHtml({
            id: parameter,
            bins: bins,
            colorCount: colors.length,
            getColor: getGlobalMappingColor,
            showLeftArrow: ['anomaly', 'pctavg'].includes(returnType) || !isPcp(parameter),
            formatLabel: (val, ndx, isLast) => {
                const valDisp = val >= 1000 ? (val / 1000) + 'K' : val;
                return `${valDisp}${isLast ? units : ''}`;
            },
            showRightArrow: true
        });
        
        document.getElementById('legend').innerHTML = html;
        document.getElementById('legend').classList.remove('rank-legend');
    }
}

function displayNoData() {
    const { year, month, parameter } = cag.variables;
    $('#data-table').empty();
    const dateDisp = getGlobalMappingDateDisplay(year, month);
    const title = parameters[parameter].title;
    $('#data-loader-overlay').html(`
        <div class="error-msg red-txt bold bigPadTop">
            The ${dateDisp} Global ${title} Map is not available.
        </div>
    `);
}

function getGlobalMappingDateDisplay (year, month, responsive = false) {
    if (month < 13) {
        const name = monthNames[month - 1];
        const formattedMonth = responsive
            ? name.slice(0, 3) + '<span class="longname">' + name.slice(3) + '</span>'
            : name;
        return formattedMonth + ' ' + year;
    }
    return year.toString();
}

async function plotMapValuesLayer(){
    const { parameter, returnType, month } = cag.variables;
    
    const timescale = (month === 13) ? 12 : 1;
    
    activeLegend = await loadLegendConfig(
        returnType, 
        parameter, 
        'global', 
        timescale, 
        month, 
        numYears[parameter]
    );

    getLegend();

    /**
     * plot color layer on bottom,
     * then borders and grid lines,
     * finally rollover value layer last
     */

    // color grid
    if (colorLayer && globalMap.hasLayer(colorLayer)) {
        globalMap.removeLayer(colorLayer);
    }
    $('.grayBox').addClass('hidden');
    colorLayer = L.geoJson(grid, {
        style: colorLayerStyle
    }).addTo(globalMap);

    // borders
    if (countryBorders && globalMap.hasLayer(countryBorders)) {
        globalMap.removeLayer(countryBorders);
    }
    countryBorders = L.geoJson(countries, {
        style: countryBordersStyle,
    }).addTo(globalMap);

    // graticules
    if (graticulesLayer && globalMap.hasLayer(graticulesLayer)) {
        globalMap.removeLayer(graticulesLayer);
    }
    graticulesLayer = L.geoJson(graticules, {
        style: graticuleStyle,
    }).addTo(globalMap);

    // value grid
    if (valueLayer && globalMap.hasLayer(valueLayer)) {
        globalMap.removeLayer(valueLayer);
    }
    valueLayer = L.geoJson(grid, {
        style:         valueLayerStyle,
        onEachFeature: onEachFeature
    }).addTo(globalMap);

    const title = getMapTitle(scope, [], parameter, returnType, basePeriod, numYears[parameter]);
    $('#mapTitle').html(title);
}

function getGlobalMappingColor(value, ties = 0) {
    const { parameter, returnType } = cag.variables;

    if (returnType === 'rank') {
        if (
            document.querySelector('.grayBox') &&
            Util.ranks.tiesNumerousRecords(value, ties, numYears[parameter])
        ) {
            document.querySelectorAll('.grayBox').forEach(el => el.classList.remove('hidden'));
            return '#DDDDDD';
        }
    }

    if (value === null || isNaN(value)) return '#DDDDDD';

    const { bins, colors } = activeLegend;
    const hasOuterColors = colors.length === bins.length + 1;

    for (let i = bins.length - 1; i >= 0; i--) {
        if (value >= bins[i]) {
            return hasOuterColors ? colors[i + 1] : colors[i];
        }
    }

    // Fallback for values below the first bin
    return colors[0];
}

function goToGridTimeSeries(e) {
    const { lat, lng } = e.latlng;
    const [centerLat, centerLng] = getCenterCoords(lat, lng);
    const coords = `${centerLat},${centerLng}`;

    const { parameter, month } = cag.variables;

    const minDate = parameters[parameter].minDate;
    const maxDate = parameters[parameter].maxDate;

    const minYear = String(minDate).substring(0, 4);
    const maxYear = String(maxDate).substring(0, 4);

    const tsMon = month == 13 ? '12/12' : `1/${month}`;

    window.location.href = `${base}/${scope}/time-series/${coords}/land_ocean/${parameter}/${tsMon}/${minYear}-${maxYear}`;
}

function getCenterCoords(lat, lon) {
    if (lon > 180) {
        while (lon > 180) {
            lon -= 360;
        }
    } else if (lon < -180) {
        while (lon < -180) {
            lon += 360;
        }
    }

    // use e1/e-1 to avoid scientific notation
    const latFmt = Number(Math.round(lat + 'e1') + 'e-1').toFixed(1);
    const lonFmt = Number(Math.round(lon + 'e1') + 'e-1').toFixed(1);

    // snap to grid
    const gridSize = gridCenter * 2;
    const latSnap = Number((Math.round(latFmt/gridSize) * gridSize).toFixed(1));
    const lonSnap = Number((Math.round(lonFmt/gridSize) * gridSize).toFixed(1));

    // find center of grid
    let latCenter = (lat > latSnap ? latSnap + gridCenter : latSnap - gridCenter);
    const lonCenter = (lon > lonSnap ? lonSnap + gridCenter : lonSnap - gridCenter);

    // projection causes artifacts near poles
    const max = 90 - gridCenter;
    const min = -90 + gridCenter;
    if (latCenter > max) {
        latCenter = max
    } else if (latCenter < min) {
        latCenter = min
    }

    return [latCenter, lonCenter];
}

function fillGlobalMappingMonths() {
    const { year, month } = cag.variables;
    const $monthElem = $('#month');
    const selectedMonth = ($monthElem.val() ? $monthElem.val() : month);
    const selectedYear = ($('#year').val() ? $('#year').val() : year);
    const selectedParameter = $('#parameter').val();

    const minDate = parameters[selectedParameter].minDate;
    const maxDate = parameters[selectedParameter].maxDate;

    const minYear = String(minDate).substring(0, 4);
    const maxYear = String(maxDate).substring(0, 4);

    const minMonth = parseInt(String(minDate).substring(4, 6));
    const maxMonth = parseInt(String(maxDate).substring(4, 6));

    const firstMonth = (selectedYear == minYear ? minMonth : 1);
    const lastMonth = (selectedYear == maxYear ? maxMonth : 12);

    $monthElem.empty();
    for (let mon = firstMonth; mon <= lastMonth; mon++) {
        $monthElem.append($('<option>').val(mon).text(monthNames[mon-1]));
    }

    // Add Annual option to complete years
    if (selectedYear < maxYear || (selectedYear == maxYear && maxMonth == 12)) {
        $monthElem.append($('<option>').val(13).text('Annual'));
    }

    const selected = $monthElem.find(`option[value="${selectedMonth}"]`).length > 0 ? selectedMonth : lastMonth;
    $monthElem.val(selected);
}

const prevNextClick = makePrevNextClick(
    () => fillGlobalMappingMonths(),
    () => globalMappingFormSubmit()
);

export function getGlobalMappingPrevNext(param, yr, mn, ret) {
    ["prev", "next"].forEach(dir =>
        computeAndRenderPrevNext({
            direction: dir,
            clickHandler: prevNextClick,
            compute: isPrev => {
                const minDate = parameters[param].minDate;
                const maxDate = parameters[param].maxDate;

                let targetYear, targetMonth, dateStr, title;

                if (mn == 13) {
                    const boundYear = isPrev
                        ? String(minDate).substring(0, 4)
                        : String(maxDate).substring(0, 4) - (String(maxDate).substring(4, 6) < 12 ? 1 : 0);

                    if ((isPrev && yr > boundYear) || (!isPrev && yr < boundYear)) {
                        targetYear = parseInt(yr) + (isPrev ? -1 : 1);
                        targetMonth = 13;
                        dateStr = targetYear;
                        title = targetYear;
                        return { valid: true, year: targetYear, month: targetMonth, dateStr, title };
                    }
                    return { valid: false };
                } else {
                    const targetDateObj = new Date(yr, parseInt(mn) + (isPrev ? -1 : 1), 0);
                    targetYear = targetDateObj.getFullYear();
                    targetMonth = targetDateObj.getMonth() + 1;
                    dateStr = targetYear + String(targetMonth).padStart(2, "0");
                    title = `${monthNames[targetDateObj.getMonth()]} ${targetYear}`;

                    if ((isPrev && dateStr < minDate) || (!isPrev && dateStr > maxDate)) {
                        return { valid: false };
                    }
                    return { valid: true, year: targetYear, month: targetMonth, dateStr, title };
                }
            },
            hrefBuilder: (dateStr) => `${base}/${scope}/mapping/${param}/${dateStr}/${ret}`
        })
    );
}
