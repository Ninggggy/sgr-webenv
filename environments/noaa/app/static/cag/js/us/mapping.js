import { getMapTitle } from '../shared/mapping/map-title.js';
import { initYearRange } from '../shared/year-ranges.js';
import { buildReturnOptions } from '../shared/mapping/return-types.js';
import { hexBlender } from '../shared/color-blender.js';
import {
    base,
    cag,
    scopes,
    scope,
    section,
    basePeriods,
    monthNames
} from '../globals.js';
import { MappingDao } from '../shared/dao/MappingDao.js';
import { configMapData } from '../utils/us-map-data-formatter.js';
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
import Util from '../utils/util.js';

const {
    national:   isNational,
    regional:   isRegional,
    statewide:  isStatewide,
    divisional: isDivisional,
    county:     isCounty,
    city:       isCity,
    substate:   isSubstate
} = Util.scope.is;

const locWithContext = Util.location.withContext(scope, section);
const {
    louisiana: isLouisiana,
    maryland: isMaryland,
    alaska: isAlaska,
    hawaii: isHawaii,
    puertoRico: isPuertoRico,
    dc: isDc,
    conus: isConus,
    conusState: isConusState, // lower 48
    agBelt: isAgBelt,
    miscRegion: isMiscRegion,
    climateRegion: isClimateRegion,
    nwsRegion: isNwsRegion,
    riverBasin: isRiverBasin
} = locWithContext.is;

const { updateUrl, disableTimescales, configDownload } = Util.config;

const {
    coldToHot: isColdToHot,
    degreeDay: isDegreeDay,
    temp: isTemp,
    precip: isPcp,
    palmer: isPalmer,
} = Util.parameter.is;

const getVal = Util.form.getVal;

const intTimescale = (ts, mn) => parseInt(ts === 'ytd' ? mn : ts, 10);

const getMinKey = id => {
    if (typeof id === 'string' && id.length === 11 && cag.constants.minDates[id]) {
        return id;
    }

    return ({ 50: 'alaska', 51: 'hawaii' }[id] || 'national');
};

const getMinDate = id => cag.constants.minDates[getMinKey(id)];

const getMinYear = id => Number(String(getMinDate(id)).slice(0, 4));

const { insufficientVariability: isInsufficientVariability } = Util.is;

const dao = new MappingDao();

let prevLocation  = cag.variables.locationId;
let prevParameter = cag.variables.parameter;
let prevDate      = cag.variables.date;
let prevTimescale = cag.variables.timescale;
let prevReturn    = cag.variables.returnType;
let numYears;
let lowest;
let highest;
// mapping variables
let resetZoom = true, mapExists = false, usMap, info;
let textLayer, valueLayer, colorLayer, boundariesLayer;
let valueBins, valueColors;
let values = {}, initValues = {};
let state;

let locationsMeta, usStates, parameters, locations;
export async function initUsMapping() {
    locationsMeta = cag.constants.locationsMeta;
    usStates      = cag.constants.usStates;
    parameters    = cag.constants.parameters;
    locations     = cag.constants.locations;

    const { locationId, parameter } = cag.variables;

    await buildReturnOptions(cag.constants.returns, cag.variables.returnType, scope, parameter);

    const { minYear, maxYear } = locations[locationId];

    // Hide EasyPrint control if using Microsoft Edge
    if (/Edge/.test(navigator.userAgent)) {
        const easyPrintControl = document.querySelector('.leaflet-control-easyPrint');
        if (easyPrintControl) {
            easyPrintControl.style.display = 'none';
        }
    }

    // Hide "rank" option for city scope
    if (isCity(scope)) {
        const rankOption = document.querySelector('.return-selection[value="rank"]');
        if (rankOption && rankOption.parentElement) {
            rankOption.parentElement.style.display = 'none';
        }
    }

    // Set the correct return selection based on returnType
    const selectedReturn = document.querySelector(`.return-selection[value="${cag.variables.returnType}"]`);
    if (selectedReturn) {
        selectedReturn.checked = true;
    }

    initYearRange(locationId);
    fillUsMappingMonths();

    fillTimescales();

    numYears = getNumYears(cag.variables.locationId);

    cag.variables.url = getUsMappingUrl();
    getMap(true, true, true, true, true, true);

    document.getElementById('year').addEventListener('change', fillUsMappingMonths);
    document.getElementById('location').addEventListener('change', fillUsMappingMonths);
    document.getElementById('parameter').addEventListener('change', disableTimescales);

    document.getElementById('return').addEventListener('change', e => {
        if (e.target.name === 'return') {
            cag.variables.formChanged = true;
            updateUsMappingData();
        }
    });

    document.getElementById('show-text').addEventListener('change', () => {
        if (isCity(scope)) {
            addCityLayers();
        } else {
            drawValues();
        }
    });

    document.getElementById('submit').addEventListener('click', (event) => {
        event.preventDefault();
        updateUsMappingData();
    });
}

function fillTimescales() {
    const tsEl = document.getElementById('timescale');

    const opts = cag.constants.timescales.map((ts) => {
        const name = ts === 'ytd' ? 'Year-to-Date' : `${parseInt(ts, 10)}-Month`;
        return `<option value="${ts}">${name}</option>`;
    });

    tsEl.innerHTML = opts.join('');

    const ts = cag.variables.timescale;
    const selected = tsEl.querySelector(`option[value="${ts}"]`) ? ts : 1;
    tsEl.value = selected;

    disableTimescales();
}

function fillUsMappingMonths() {
    const monthElem = document.getElementById('month');
    const selectedYear  = document.getElementById('year').value;
    const selectedLocationId  = document.getElementById('location').value;
    const begYear = getMinYear(selectedLocationId);
    const selectedMonth = monthElem.value || cag.variables.month;

    const minDate = getMinDate(selectedLocationId);
    const minMonth = parseInt(String(minDate).substring(4, 6));

    const begMonth = (selectedYear == begYear ? minMonth : 1);
    const endMonth = (selectedYear == cag.constants.maxYear ? cag.constants.maxMonth : 12);

    const opts = [];
    for (let mon = begMonth; mon <= endMonth; mon++) {
        opts.push(`<option value="${mon}">${monthNames[mon - 1]}</option>`);
    }

    monthElem.innerHTML = opts.join('');

    const selected = monthElem?.querySelector(`option[value="${selectedMonth}"]`)
        ? selectedMonth
        : endMonth;
    monthElem.value = selected;
}

function getNumYears(id) {
    const { timescale, month } = cag.variables;

    cag.variables.minYear = getMinYear(id);
    cag.variables.minDate = getMinDate(id);

    numYears = Util.numYears(
        cag.variables.minDate,
        cag.constants.maxDate,
        month,
        intTimescale(timescale, month)
    );

    return numYears;
}

function updateUsMappingData() {
    if (!cag.variables.formChanged) {
        updateUrl();
        return false;
    }

    const rt = getSelectedReturnType();
    //const rt = document.querySelector('#return input[name="return"]:checked');
    const form = document.querySelector('#select-form');
    const formData = new FormData(form);
    const serialized = new URLSearchParams(formData).toString();
    Object.assign(cag.variables, {
        locationId: getVal('location'),
        parameter:  getVal('parameter'),
        year:       Number(getVal('year')),
        month:      Number(getVal('month')),
        timescale:  getVal('timescale'),
        returnType: rt ? rt.value : 'value',
        formState:   serialized,
        formChanged: false
    });

    const { locationId, parameter, year, month, timescale, returnType } = cag.variables;

    cag.variables.date = `${year}${String(month).padStart(2, '0')}`;
    numYears = getNumYears(locationId);

    const locationChange  = (locationId != prevLocation);
    const parameterChange = (parameter  != prevParameter);
    const dateChange      = (cag.variables.date != prevDate);
    const timescaleChange = (timescale  != prevTimescale);
    const usReturnChange  = (returnType != prevReturn);

    const getNewMap = (locationChange || parameterChange || dateChange || timescaleChange);

    prevLocation  = locationId;
    prevParameter = parameter;
    prevDate      = cag.variables.date;
    prevTimescale = timescale;
    prevReturn    = returnType;

    pushState(cag.variables);

    // cache
    const cacheUrl = `${base}/${scope}/${section}/cache/?` + cag.variables.formState;
    fetch(cacheUrl, { credentials: "include" })
        .then(res => {
            if (!res.ok) throw new Error(`cache request failed ${cacheUrl}`);
        });

    if (getNewMap || usReturnChange) {
        getMap(getNewMap, locationChange, parameterChange, dateChange, usReturnChange);
    }
}

function pushState({
    scope,
    locationId,
    parameter,
    year,
    month,
    timescale,
    returnType
}) {
    const pageState = { scope, locationId, parameter, year, month, timescale, returnType };

    cag.variables.url = getUsMappingUrl();

    window.history.pushState(pageState, null, cag.variables.url);
}

function getSelectedReturnType() {
    return document.querySelector('#return input[name="return"]:checked:enabled')
        ?? document.querySelector('#return input[value="value"]');
}

function getUsMappingUrl() {
    const { locationId, parameter, date, timescale, returnType } = cag.variables;
    return `${base}/${scope}/${section}/${locationId}/${parameter}/${date}/${timescale}/${returnType}`;
}

async function getMap(getNewMap, locationChange, parameterChange, dateChange, usReturnChange) {
    if (getNewMap) {
        document.querySelector('#return [value="pctavg"]').disabled = !isPcp(cag.variables.parameter);
        if (cag.variables.returnType === 'pctavg' && !isPcp(cag.variables.parameter)) {
            cag.variables.returnType = 'value';
            document.querySelector('#return [value="value"]').checked = true;
            pushState(cag.variables);
        }

        const { locationId, parameter, date, timescale, year, month, returnType } = cag.variables;

        const dataDownloadUrl = `${base}/${scope}/${section}/${locationId}-${parameter}-${date}-${timescale}`;

        configDownload(dataDownloadUrl);

        if (locationChange) {
            setUsBasePeriod();

            // hide text labels option for nationwide (only 1 value) and divisional/county (too many values)
            const showTextDiv = document.querySelector('#show-text-div');
            if ((isDivisional(scope) || isCounty(scope)) && isConus(locationId)) {
                showTextDiv.classList.add('hidden');
            } else {
                showTextDiv.classList.remove('hidden');
            }
        }

        if (parameterChange) {
            setLowestHighestText();
        }

        if (dateChange) {
            getUsMappingPrevNext(timescale, year, month, locationId, parameter, returnType);
        }

        let mapDataLoaderOverlay = document.getElementById('map-data-loader-overlay');
        if (!mapDataLoaderOverlay) {
            const dynamicContent = document.getElementById('dynamic-content');
            dynamicContent?.insertAdjacentHTML('afterbegin', loaderOverlay('map-data-loader-overlay'));
            mapDataLoaderOverlay = document.getElementById('map-data-loader-overlay');
        }

        const data = await dao.getMappingData(scope, cag.variables);
        const locs = scope === 'city' ? cag.constants.usCities : locationsMeta;
        values = await configMapData(scope, data, locs, usStates, Util.getPrecision(locationId, parameter));

        if (!values || Object.keys(values).length === 0) {
            console.warn('US Mapping values empty');
            document.getElementById("data-table").textContent="No data: the complete selected window is outside the available record or contains a missing month.";
            if(usMap){usMap.remove();usMap=null;mapExists=false;}
            document.getElementById("map-canvas").textContent="No data for this window.";
            if (mapDataLoaderOverlay) {
                mapDataLoaderOverlay.innerHTML = `
                    <div class="error-msg red-txt bold bigPadTop">
                        No complete data for this window. Please,
                        <a href="${getUsMappingUrl()}">try again.</a>
                    </div>`;
            }
            return;
        }

        drawMapValues(locationChange);
        createUsMappingDataTable();

        mapDataLoaderOverlay?.remove();
    } else if (usReturnChange) {
        drawMapValues(locationChange);
    }
}

async function setInitValues() {
    const { parameter, date, timescale, locationId } = cag.variables;
    const key = `${parameter}-${date}-${timescale}`;

    if (!(key in initValues)) {
        initValues[key] = {};
    }

    if (
        (isConus(locationId) || isSubstate(scope)) &&
        !isCity(scope) && !(locationId in initValues[key])
    ) {
        let initValueLoaderOverlay = document.getElementById('init-value-loader-overlay');
        if (!initValueLoaderOverlay) {
            document.getElementById('dynamic-content')
                ?.insertAdjacentHTML('afterbegin', loaderOverlay('init-value-loader-overlay'));
            initValueLoaderOverlay = document.getElementById('init-value-loader-overlay');
        }

        try {
            const initScope = isConus(locationId) ? 'national' : 'statewide';
            const initData = await dao.getMappingData(initScope, cag.variables);
            const initKeyValues = await configMapData(initScope, initData, locations, usStates, parameters[parameter].precision);
            initValues[key] = {
                ...initValues[key],
                ...initKeyValues
            };
        } catch (err) {
            console.error('Failed to fetch init values:', err)
        } finally {
            initValueLoaderOverlay?.remove();
        }
    } else if (!(locationId in initValues[key])) {
        initValues[key] = {
            ...initValues[key],
            ...values
        };
    }

    const hoverInfo = document.getElementById('hoverInfo');
    if (hoverInfo) {
        hoverInfo.innerHTML = getDefaultHighlightInfo();
    }
}

async function drawMapValues(locationChange) {
    setInitValues();

    if (locationChange || !mapExists) {
        createNewMap();
        resetZoom = true;
    } else {
        resetZoom = false;
    }

    const { returnType, parameter, locationId, month } = cag.variables;
    const timescale = cag.variables.timescale === 'ytd' ? month : Number(cag.variables.timescale);

    const { bins, colors } = await loadLegendConfig(returnType, parameter, locationId, timescale, month, numYears);

    valueBins = bins;
    valueColors = colors;

    if (isCity(scope)) {
        drawCityValues();
    } else {
        drawValues();
    }

    if (cag.variables.returnType === 'rank' & !isCity(scope)) {
        getRankLegend(valueBins, valueColors);
    } else {
        getBinnedLegend();
    }

    document.getElementById('mapTitle').innerHTML = getMapTitle(
        scope,
        scopes,
        cag.variables.parameter,
        cag.variables.returnType,
        setUsBasePeriod(),
        numYears
    );
    document.getElementById('mapDate').innerHTML = getMapDateDisplay(true);
}

function setUsBasePeriod() {
    const locationId = cag.variables.locationId;
    const key =
        isCity(scope) ? 'city' :
        isAlaska(locationId) ? 'alaska' :
        isHawaii(locationId) ? 'hawaii' :
        'conus';

    const { begyear, endyear } = basePeriods.national[key];
    return `${begyear}-${endyear}`;
}

const getLocationIdKey = (properties) => {
    // Ag Belt IDs (2XX/3XX) combined into single properties.ID (5XX) map polygon
    const loc = cag.variables.locationId;
    return isRegional(scope) && isAgBelt(loc) ? loc : properties.ID;
}

function createNewMap() {
    const usMapOptions = {
        zoomDelta          : 0.25,
        zoomSnap           : 0,
        zoomControl        : false,
        keyboard           : false,
        dragging           : false,
        zoomControl        : false,
        boxZoom            : false,
        doubleClickZoom    : false,
        scrollWheelZoom    : false,
        tap                : false,
        touchZoom          : false,
        attributionControl : false,
        maxBoundsViscosity : 0.5
    }

    if (mapExists) {
        usMap.remove();
    }

    usMap = L.map('map-canvas', usMapOptions);
    mapExists = true;

    // text markers
    textLayer = L.layerGroup().addTo(usMap);

    addHoverInfoControl(usMap, 'bottomleft');
    addLedgendControl(usMap, 'bottomleft');
    addLogoControl(usMap, 'bottomright');
    addMapTitleControl(usMap, 'topleft');
    addMapDateControl(usMap, 'topright');
    addGrayBoxControl(usMap, 'bottomleft');
    addPrintControl(usMap, 'bottomright');
}

function addHoverInfoControl(map, position) {
    // control that shows info on hover
    info = L.control({position});
    info.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'info values hoverValues');
        div.innerHTML = `<div id="hoverInfo">${getDefaultHighlightInfo()}</div>`;

        this.update();
        return div;
    };

    // update info on hover
    info.update = function(properties) {
        let content = '';

        if (properties) {
            let locationName = '';
            let id;

            if (isCity(scope)) {
                id = properties.ghcnId;
                locationName = properties.name === null
                    ? '--'
                    : `${properties.name}, ${properties.stateAbbr}`;
            } else {
                id = getLocationIdKey(properties);
                locationName = !values[id] || values[id].name === null
                    ? '--'
                    : values[id].name;
            }

            // Append state abbreviation for counties if applicable
            if (isCounty(scope) && ('STAB' in properties) &&
                (isConus(cag.variables.locationId) || properties.STAB === 'DC') // always include DC (since it's included in MD)
            ) {
                locationName += `, ${properties.STAB}`;
            }

            const highlightData = (isCity(scope) ? properties : values[id]);
            content = `<div id="hoverLocationName">${locationName}</div>${getHighlightValuesText(highlightData, id)}`;
        } else {
            content = getDefaultHighlightInfo();
        }

        const infoEl = document.getElementById('hoverInfo');
        if (infoEl) infoEl.innerHTML = content;
    };
    info.addTo(map);
}

function loaderOverlay(loaderOverlayId) {
    return `
        <div class="loader-overlay" id="${loaderOverlayId}">
            <div class="noaa-loader center">
                <img alt="loader" src="/monitoring-content/lib/images/noaa-loader.gif">
            </div>
        </div>
    `;
}

function getDefaultHighlightInfo() {
    const { locationId, parameter, date, timescale } = cag.variables;
    const locationSelect = document.getElementById('location');

    const getLocationText = (id) => {
        const option = locationSelect?.querySelector(`option[value="${id}"]`);
        return option ? option.textContent.trim() : '';
    };

    if (!isCity(scope) && Object.keys(values).length < 2) {
        const locationName = isStatewide(scope) ? 'Contiguous U.S.' : getLocationText(locationId);
        const mappingLocation = isAgBelt(locationId) ? '5' + String(locationId).slice(-2) : locationId;
        const valueData = values[mappingLocation] || {};

        return `
            <div id="hoverLocationName">${locationName}</div>
            ${getHighlightValuesText(valueData, mappingLocation)}
        `;
    } else {
        let hoverInstructions = 'Hover over a ';

        if (isCity(scope)) {
            hoverInstructions += 'City';
        } else if (isCounty(scope)) {
            hoverInstructions += 'County';
        } else if (isDivisional(scope)) {
            hoverInstructions += 'Climate Division';
        } else if (isStatewide(scope)) {
            hoverInstructions += 'State';
        } else {
            const getRegionName = isRegional(scope) && 
                (isClimateRegion(locationId) || isNwsRegion(locationId) || isRiverBasin(locationId));

            hoverInstructions += getRegionName ? getLocationText(locationId).slice(0, -1) : 'Region';
        }

        const displayName = (isNational(scope)) ? 'Contiguous U.S.' : getLocationText(locationId);

        const instructionsHTML = (
            (isStatewide(scope) && !isConus(locationId)) ||
            (isRegional(scope) && !isClimateRegion(locationId) && !isNwsRegion(locationId) && !isRiverBasin(locationId))
        )
            ? ''
            : ` <span class="hoverInstructions">(${hoverInstructions})</span>`;

        const key = `${parameter}-${date}-${timescale}`;
        const mapData = (initValues[key] && initValues[key][locationId]) || {};

        return `
            <div id="hoverLocationName">${displayName}${instructionsHTML}</div>
            ${getHighlightValuesText(mapData, locationId)}
        `;
    }
}

function getHighlightValuesText(highlightValues, mappingLocation) {
    let highlightValuesText = `<div id="highlightValues">`;

    // parameter option text (used in inner loop)
    const id = highlightValues?.ghcnId ? highlightValues.ghcnId : cag.variables.locationId;
    numYears = getNumYears(id);
    const parameterSelect = document.getElementById('parameter');
    const parameterOption = parameterSelect?.querySelector(`option[value="${cag.variables.parameter}"]`);
    const parameterText   = parameterOption ? parameterOption.textContent.trim() : '';
    const paramAbbr       = getParameterAbbr(parameterText);
    const ties            = parseInt(highlightValues?.ties, 10) || 0;
    const isInsufficient  = isInsufficientVariability(ties, numYears);
    const enabledReturns  = document.querySelectorAll('#return input[name="return"]:enabled');

    enabledReturns.forEach(input => {
        const thisReturnType = input.id;

        // skip city ranks
        //if (scope === 'city' && highlightValues.ghcnId && thisReturnType === 'rank') return;
        // skip non-pcp pctavg
        //if (thisReturnType === 'pctavg' && cag.variables.parameter !== 'pcp') return;

        // Use a conditional to prevent errors in case highlightValues is falsy
        const returnDisplay = highlightValues
            ? getValueDisplay(highlightValues[thisReturnType], thisReturnType, mappingLocation)
            : '';

        const isCurrent = (thisReturnType === cag.variables.returnType) ? ' currentReturnType' : '';

        // Get label text based on the return type.
        let titleText = '';
        if (thisReturnType === 'value') {
            titleText = `<span class="paramAbbr">${paramAbbr}</span>` +
                `<span class="parameter">${parameterText}</span>`;
        } else {
            const label = document.querySelector(`#return label[for="${thisReturnType}"]`);
            titleText = label ? label.textContent.trim() : '';
        }

        // Wrap the rank display if needed.
        const displayValue = thisReturnType === 'rank'
            ? getRankDisplay(returnDisplay) + setDesignation(ties, isInsufficient, scope)
            : returnDisplay;

        highlightValuesText += `<div class="hoverReturn${isCurrent}" id="hover${thisReturnType}">` +
                `<strong class="hoverReturnTitle nowrap">${titleText}:</strong>` +
                `<span class="hoverReturnValue">${displayValue}</span>` +
            `</div>`;
    });

    highlightValuesText += `</div>`;
    return highlightValuesText;
}

function setLowestHighestText() {
    const parameter = cag.variables.parameter;
    if (isColdToHot(parameter)) {
        lowest  = 'Coldest';
        highest = 'Warmest';
    } else if (isPalmer(parameter)) {
        lowest  = 'Driest';
        highest = 'Wettest';
    } else {
        lowest  = 'Lowest';
        highest = 'Highest';
    }
}

function getParameterAbbr(parameterName) {
    const parameter = cag.variables.parameter;
    if (['cdd', 'hdd'].includes(parameter)) {
        return parameter.toUpperCase();
    } else if (parameterName.match(/\(/)) {
        return parameterName.split('(')[1].split(')')[0];
    } else if (parameter === 'zndx') {
        return 'Z-Index';
    } else if (isDegreeDay(parameter)) {
        return parameter.toUpperCase();
    } else if (isPcp(parameter)) {
        return 'Precip';
    } else if (isTemp(parameter)) {
        return 'Temp';
    }

    return parameterName;
}

async function drawValues() {
    document.querySelectorAll('.grayBox').forEach(el => el.classList.add('hidden'));

    let loaderOverlayEl = document.getElementById('map-values-loader-overlay');
    if (!loaderOverlayEl) {
        const dynamicContent = document.getElementById('dynamic-content');
        dynamicContent.insertAdjacentHTML(
            'afterbegin',
            loaderOverlay('map-values-loader-overlay')
        );
        loaderOverlayEl = document.getElementById('map-values-loader-overlay');
    }

    try {
        const primaryFile = getPrimaryBoundaries();
        const primaryBoundariesJson = await fetchJson(primaryFile, {
            fallback: null,
            context: 'primary boundaries'
        });

        if (!primaryBoundariesJson) {
            throw new Error('Primary boundaries failed to load');
        }

        // Update Primary Color Layer
        if (colorLayer && usMap.hasLayer(colorLayer)) {
            usMap.removeLayer(colorLayer);
        }

        colorLayer = L.geoJson(primaryBoundariesJson, {
            style: colorsStyle,
            smoothFactor: 0.5
        }).addTo(usMap);

        // Clear existing secondary boundaries
        if (boundariesLayer && usMap.hasLayer(boundariesLayer)) {
            usMap.removeLayer(boundariesLayer);
        }

        // Secondary boundaries
        const secondaryFile = getSecondaryBoundaries();
        if (secondaryFile) {
            const secondaryJson = await fetchJson(secondaryFile, {
                fallback: null,
                context: 'secondary boundaries'
            });

            if (secondaryJson) {
                boundariesLayer = L.geoJson(secondaryJson, {
                    style: boundariesStyle
                }).addTo(usMap);
            }
        }

        if (loaderOverlayEl) loaderOverlayEl.remove();

        addValueLayer(primaryBoundariesJson);
        setMapBounds();

    } catch (error) {
        console.error(error);

        if (loaderOverlayEl) {
            loaderOverlayEl.innerHTML = `
                <div class="error-msg red-txt bold bigPadTop">
                    Values did not load. Please,
                    <a onclick="location.reload();" href="${getUsMappingUrl()}">
                        try again.
                    </a>
                </div>
            `;
        }
    }
}

function addValueLayer(boundaries) {
    if (valueLayer && usMap.hasLayer(valueLayer)) {
        usMap.removeLayer(valueLayer);
    }

    textLayer.clearLayers();

    valueLayer = L.geoJson(boundaries, {
        style: valuesStyle,
        smoothFactor: 0.5,
        onEachFeature: onEachFeature
    }).addTo(usMap);
}

function getPrimaryBoundaries() {
    const locationId = cag.variables.locationId;
    const basePath = `/monitoring-content/lib/geojson/${isCity(scope) ? 'statewide' : scope}/`;
    let src = basePath;

    const getOptionText = (id) => {
        const option = document.querySelector(`#location option[value="${id}"]`);
        return option ? option.textContent.trim() : '';
    };

    const locationFileName = (id) => {
        return getOptionText(id)
            .replace(/\s+/g, '-')
            .toLowerCase();
    };

    if (
        isConus(locationId) ||
        (isCity(scope) && (isConusState(locationId) || isDc(locationId)))
    ) {
        src += 'conus';
    } else if (isClimateRegion(locationId)) {
        src += 'climate-regions';
    } else if (isNwsRegion(locationId)) {
        src += 'nws-regions';
    } else if (isRiverBasin(locationId)) {
        src += 'river-basins';
    } else if (isAgBelt(locationId)) {
        // Ag Belts (remove parentheses and extra spaces)
        const rawText = getOptionText(locationId);
        src += rawText
            .replace(/ *\([^)]*\) */g, '')
            .replace(/\s+/g, '-')
            .toLowerCase();
    } else if (isMiscRegion(locationId)) {
        // Miscellaneous Regions
        src += locationFileName(locationId);
    } else if (
        isConusState(locationId) ||
        isAlaska(locationId) ||
        isHawaii(locationId) ||
        isPuertoRico(locationId)
    ) {
        // Single State
        src += locationFileName(locationId);
    } else {
        src += locationId;
    }

    return `${escapeHtml(src)}.geojson`;
}

function getSecondaryBoundaries() {
    const locationId = cag.variables.locationId;
    let src = '/monitoring-content/lib/geojson';

    if (
        (isRegional(scope)) ||
        (isCounty(scope)) ||
        (isDivisional(scope)) ||
        (isConusState(locationId) && !isCity(scope))
    ) {
        // add CONUS state boundaries
        return src + '/statewide/conus.geojson';
    } else if (isDc(locationId)) {
        // DC
        return src + '/statewide/district-of-columbia.geojson';
    } else if (isRegional(scope) && locationId > 0) {
        // Ag Belts: add CONUS divisional boundaries
        return src + '/divisional/conus.geojson';
    } else {
        return '';
    }
}

async function drawCityValues() {
    if (boundariesLayer && usMap.hasLayer(boundariesLayer)) {
        usMap.removeLayer(boundariesLayer);
    }

    const primaryFile = getPrimaryBoundaries();

    if (!primaryFile) {
        addCityLayers();
        setMapBounds();
        return;
    }

    let loaderOverlayEl = document.getElementById('city-map-loader-overlay');
    if (!loaderOverlayEl) {
        const dynamicContent = document.getElementById('dynamic-content');
        if (dynamicContent) {
            dynamicContent.insertAdjacentHTML(
                'afterbegin',
                loaderOverlay('city-map-loader-overlay')
            );
            loaderOverlayEl = document.getElementById('city-map-loader-overlay');
        }
    }

    try {
        const primaryJson = await fetchJson(primaryFile, {
            fallback: null,
            context: 'primary city boundaries'
        });

        if (!primaryJson) {
            throw new Error('Primary boundaries failed');
        }

        if (boundariesLayer && usMap.hasLayer(boundariesLayer)) {
            usMap.removeLayer(boundariesLayer);
        }

        const newGroup = L.layerGroup();

        // Secondary = non-fatal
        const secondaryFile = getSecondaryBoundaries();
        if (secondaryFile) {
            const secondaryJson = await fetchJson(secondaryFile, {
                fallback: null,
                context: 'secondary city boundaries'
            });

            if (secondaryJson) {
                L.geoJson(secondaryJson, {
                    style: boundariesStyle
                }).addTo(newGroup);
            }
        }

        // Primary LAST
        L.geoJson(primaryJson, {
            style: boundariesStyle
        }).addTo(newGroup);

        newGroup.addTo(usMap);
        boundariesLayer = newGroup;

    } catch (error) {
        console.error("City map boundaries error:", error);
    } finally {
        if (loaderOverlayEl) loaderOverlayEl.remove();

        addCityLayers();
        setMapBounds();
    }
}

function setMapBounds() {
    state = (isRegional(scope) ? '110' : cag.variables.locationId);

    let mapPadding = {};
    if (state == 50) {
        // AK
        mapPadding = {
            paddingTopLeft:     [0,  60], // L, T
            paddingBottomRight: [0, 150]  // R, B
        };
    } else if (state == 49) {
        // DC
        mapPadding = {
            paddingTopLeft:     [750,  60], // L, T
            paddingBottomRight: [  0, 100]  // R, B
        };
    } else {
        mapPadding = {
            paddingTopLeft:     [45,  60], // L, T
            paddingBottomRight: [45, 125]  // R, B
        };
    }

    const states = cag.constants.states;
    if (resetZoom) {
        usMap.fitBounds(states[state].bounds, mapPadding);
    }

    const resetMapBounds = document.getElementById('reset-map-bounds');
    if (resetMapBounds) {
        resetMapBounds.onclick = null; // unbind
        resetMapBounds.addEventListener('click', () => {
            usMap.fitBounds(states[state].bounds, mapPadding);
        });
    }
}

function addCityLayers() {
    // filter cities
    let cityValues = {
        'type' : 'FeatureCollection',
        'features' : []
    };

    values.features.forEach((cityAttr, i) => {
        if (cag.constants.idsByLocation[cag.variables.locationId].includes(cityAttr.ghcnId)) {
            cityValues.features.push(cityAttr);
        }
    });

    if (valueLayer && usMap.hasLayer(valueLayer)) {
        usMap.removeLayer(valueLayer);
    }

    valueLayer = L.geoJSON(cityValues, {
        style: function (feature) { return feature.properties && feature.properties.style; },
        onEachFeature: onEachCityFeature,
        pointToLayer: function (feature, latlng) {
            return L.circleMarker(latlng, {
                radius: 5,
                fillColor: getUsMappingColor(feature.properties[cag.variables.returnType]),
                color: '#000000',
                weight: 0.5,
                opacity: 1,
                fillOpacity: 1
            });
        }
    }).addTo(usMap);

    textLayer.clearLayers();
    if (document.getElementById('show-text').checked) {
        L.geoJSON(cityValues, {
            style: function (feature) { return feature.properties && feature.properties.style; },
            onEachFeature: onEachCityFeature,
            pointToLayer: function (feature, latlng) {
                return L.marker(latlng, {
                    icon: L.divIcon({
                        html: getValueDisplay(
                            feature.properties[cag.variables.returnType],
                            cag.variables.returnType,
                            feature.ghcnId
                        ),
                        className: 'textLabels cityTextLabels',
                    })
                });
            }
        }).addTo(textLayer);
    }
}

function colorsStyle(feature) {
    const id = getLocationIdKey(feature.properties);
    const val = values[id] ? values[id][cag.variables.returnType] : null;
    const valid = val !== null && !isNaN(val);

    const numerousRecords = cag.variables.returnType === 'rank' &&
        Util.ranks.tiesNumerousRecords(val, values[id]?.ties, numYears);

    if (numerousRecords) {
        document.querySelectorAll('.grayBox').forEach(el => el.classList.remove('hidden'));
    }

    return {
        weight: 0,
        opacity: 0,
        color: 'transparent',
        dashArray: '0',
        fillOpacity: 1,
        fillColor: valid
            ? getUsMappingColor(val, numerousRecords)
            : '#878787'
    };
}

function valuesStyle(feature) {
    return {
        weight: (isDivisional(scope) || (isCounty(scope) && isConus(cag.variables.locationId)) ? 0.15 : 0.3),
        opacity: 1,
        color: '#000000',
        dashArray: '0',
        fillOpacity: 1,
        fillColor: 'transparent'
    };
}

function boundariesStyle(feature) {
    return {
        weight: (isDivisional(scope) || isCity(scope) ? 0.25 : 0.1),
        opacity: 1,
        color: '#000000',
        fillOpacity: 0,
        fillColor: 'transparent'
    };
}

function mouseover(e) {
    highlightFeature(e);

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        e.target.bringToFront();
    }

    info.update(e.target.feature.properties);
}

function cityMouseover(e) {
    highlightCityFeature(e);

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        e.target.bringToFront();
    }

    info.update(e.target.feature.properties);
}

function highlightCityFeature(e) {
    let layer = e.target;
    layer.setStyle({
        radius: 6,
        weight: 1
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

function resetCityHighlight(e) {
    let layer = e.target;
    layer.setStyle({
        radius: 5,
        weight: 0.5
    });
    valueLayer.resetStyle(layer);
    info.update();
}

function getValueDisplay(val, thisReturnType, mappingLocation) {
    if ((!val && val != 0) || val === null || isNaN(val)) {
        return '--';
    }

    let valDisp = thisReturnType === 'pctavg'
        ? parseFloat(val).toFixed(1)
        : Util.format.number(val, getUsMappingPrecision(thisReturnType, mappingLocation));

    const units = thisReturnType === 'pctavg'
        ? '%'
        : cag.constants.parameters[cag.variables.parameter].units.replace('in', '"');
    return valDisp + (thisReturnType === 'rank' ? '' : units);
}

function onEachFeature(feature, layer) {
    // Text Labels
    if (
        document.getElementById('show-text').checked &&
        ((!isDivisional(scope) && !isCounty(scope)) || !isConus(cag.variables.locationId))
    ) {
        const id             = getLocationIdKey(feature.properties);
        if (values[id]) {
            const lat            = parseFloat(values[id].centroid.lat);
            const lon            = parseFloat(values[id].centroid.lon);
            const coords         = L.latLng(lat, lon);
            const ties           = values[id]?.ties;
            const isInsufficient = isInsufficientVariability(ties, numYears);
            let html;

            html = cag.variables.returnType === 'rank'
                ? getOrdinalSuffix(values[id][cag.variables.returnType]) + setDesignation(ties, isInsufficient, scope)
                : getValueDisplay(values[id][cag.variables.returnType], cag.variables.returnType, id);

            L.marker(coords, {
                icon: L.divIcon({
                    html,
                    className: 'textLabels' + (isStatewide(scope) ? ' location-' + id : ''),
                })
            }).addTo(textLayer);
        }
    }

    layer.on({
        mouseover: mouseover,
        mouseout:  resetHighlight,
        click:     regionClick
    });
}

function regionClick(e) {
    let clickedRegion = getLocationIdKey(e.target.feature.properties);

    if (isConus(cag.variables.locationId) && !isNational(scope)) {
        if (isCounty(scope)) {
            clickedRegion = cag.constants.stateIds[String(clickedRegion).slice(0, 2)];
        } else if (isDivisional(scope)) {
            clickedRegion = String(clickedRegion).slice(0, -2);
        }

        const locEl = document.getElementById('location');
        locEl.value = clickedRegion;
        locEl.dispatchEvent(new Event('change'));

        updateUsMappingData();
    } else {
        if (isDivisional(scope)) {
            clickedRegion = String(clickedRegion).padStart(4, '0');
        }
        const {parameter, timescale, month, minYear } = cag.variables;
        const maxYear  = cag.constants.maxYear;
        window.location.href = `${base}/${scope}/time-series/${clickedRegion}/${parameter}/${timescale}/${month}/${minYear}-${maxYear}`;
    }
}

function cityClick(feature, layer) {
    const {parameter, timescale, month, minYear } = cag.variables;
    const maxYear = cag.constants.maxYear;
    window.location.href = `${base}/${scope}/time-series/${feature.target.feature.ghcnId}/${parameter}/${timescale}/${month}/${minYear}-${maxYear}`;
}

function getUsMappingPrecision(thisReturnType, mappingLocation) {
    return thisReturnType === 'rank' || isDegreeDay(cag.variables.parameter) ? 0 : Util.getPrecision(mappingLocation, cag.variables.parameter);
}

function onEachCityFeature(feature, layer) {
    layer.on({
        mouseover: cityMouseover,
        mouseout:  resetCityHighlight,
        click:     cityClick
    });
}

function highlightFeature(e) {
    let layer = e.target;
    layer.setStyle({
        weight: 1,
        color: '#000000',
        dashArray: '0',
        fillOpacity: 1
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

function resetHighlight(e) {
    valueLayer.resetStyle(e.target);
    info.update();
}

function getBinnedLegend() {
    const { parameter, returnType } = cag.variables;
    const units = returnType === 'pctavg' ? '%' : cag.constants.parameters[parameter].units;
    const largeValues = returnType !== 'pctavg' && valueBins[valueBins.length - 1] > 100;

    const html = buildBinnedLegendHtml({
        id: parameter,
        bins: valueBins,
        colorCount: valueColors.length,
        getColor: getUsMappingColor,
        showLeftArrow: ['anomaly', 'pctavg'].includes(returnType) || (!isPcp(parameter) && !isDegreeDay(parameter)),

        formatLabel: (val, ndx, isLast) => {
            Util.format.number(val);

            const even = ndx % 2 === 0;
            if (largeValues && !even) return '';

            const fractionMap = {
                '0.25': '<span class="small">0.25</span>',
                '-0.25': '<span class="small">-0.25</span>'
            };

            val = fractionMap[val] ?? val;
            let label = val + (isLast ? units.replace('in', '"') : '');

            const isLastDd =
                (isDegreeDay(parameter)) &&
                (isLast || (largeValues && even && ndx === valueColors.length - 2));

            if (isLastDd) {
                label += '<span class="dd-units-defn"> = Fahrenheit Degree-Days</span>';
            }

            return label;
        }
    });

    document.getElementById('legend').innerHTML = html;
}

function getRankLegend(bins, colors) {
    const html = buildRankLegendHtml(colors, bins, lowest, highest);
    document.getElementById('legend').innerHTML = html;
}

function getRankDisplay(rank) {
    rank = parseInt(rank, 10);

    if (!rank) {
        return '--';
    }

    if (rank === 1) return lowest;
    if (rank === numYears) return highest;

    if (rank === numYears / 2) {
        return getOrdinalSuffix(rank);
    }

    const dispRank = getOrdinalSuffix(rank > numYears / 2 ? numYears - rank + 1 : rank);
    const hiLoest = rank > numYears / 2 ? highest : lowest;

    return `${dispRank} ${hiLoest}`;
}

function getOrdinalSuffix(integer) {
    if (isNaN(integer)) {
        return '--';
    } else if (!Number.isInteger(integer)) {
        return integer;
    }

    let ordinalSuffix;

    /* check if ends in 11, 12, or 13 */
    if (integer%100 > 10 && integer%100 < 14) {
        ordinalSuffix = 'th';
    } else {
        /* check last digit */
        switch(String(integer).slice(-1)) {
        case '1':
            ordinalSuffix = 'st';
            break;
        case '2':
            ordinalSuffix = 'nd';
            break;
        case '3':
            ordinalSuffix = 'rd';
            break;
        default:
            ordinalSuffix = 'th';
        }
    }

    return integer + ordinalSuffix;
}

function getUsMappingColor(value, numerousRecords = false) {
    if (document.querySelector('.grayBox') && numerousRecords) {
        return '#DDDDDD';
    }

    const bins = valueBins;
    const colors = valueColors;
    const hasOuterColors = colors.length === bins.length + 1;

    // Below first bin
    if (value < bins[0]) {
        return hasOuterColors
            ? colors[0]
            : hexBlender(colors[0], '#000000', 0.5);
    }

    // Walk bins from top down
    for (let ndx = bins.length - 1; ndx >= 0; ndx--) {
        if (value >= bins[ndx]) {

            // If we have one extra color,
            // shift by +1 because color[0] is "below"
            if (hasOuterColors) {
                return colors[ndx + 1];
            }

            // Legacy behavior
            if (!colors[ndx]) {
                return hexBlender(colors[colors.length - 1], '#000000', 0.5);
            }

            return colors[ndx];
        }
    }

    // Fallback (shouldn't hit)
    return colors[0];
}

// Returns HTML when responsive === true
function getMapDateDisplay(responsive = false) {
    const { year, month, returnType } = cag.variables;
    let dateDisplay = '';
    const intTs = intTimescale(cag.variables.timescale, month);
    const isMean = returnType === 'mean';
    const formatMonthName = (mName) => (responsive && !isMean)
        ? `${mName.slice(0, 3)}<span class="longname">${mName.slice(3)}</span>`
        : mName;

    if (intTs > 1) {
        if (isMean && intTs > 12) {
            dateDisplay = intTs + '-Month Period Ending in ';
        } else {
            const dateObj = new Date(year, month - 1);
            const begDate = new Date(dateObj);

            begDate.setMonth(begDate.getMonth()-(intTs-1));
            const thisBegYear = begDate.getFullYear();
            const begMonth = begDate.getMonth() + 1;
            dateDisplay = formatMonthName(monthNames[begMonth - 1]);

            if (thisBegYear < year && !isMean) {
                dateDisplay += ' ' + thisBegYear;
            }

            dateDisplay += ' - ';
        }
    }

    dateDisplay += formatMonthName(monthNames[month - 1]);

    if (!isMean) dateDisplay += ' ' + year;

    return dateDisplay;
}

function getLocationHeader(scope, locationId, locationHeaders) {
    if (isCounty(scope) && isLouisiana(locationId)) {
        return 'Parish';
    }
    if (isRegional(scope)) {
        switch (locationId) {
            case '-1':
                return 'Climate Region';
            case '-2':
                return 'NWS Region';
            case '-3':
                return 'Basin';
            default:
                // Ag Belt condition for regional scope
                if (isAgBelt(locationId)) {
                    return 'Ag Belt';
                }
                break;
        }
    }
    return locationHeaders[scope];
}

function createUsMappingDataTable() {
    const { parameter, month, locationId, timescale, minYear } = cag.variables;
    const locationHeaders = {
        'national'  : 'Location',
        'regional'  : 'Region',
        'statewide' : 'State',
        'divisional': 'Climate Division',
        'county'    : 'County',
        'city'      : 'City'
    };

    const locationHeader   = getLocationHeader(scope, locationId, locationHeaders);
    const parameterSelect = document.getElementById('parameter');
    const locationSelect  = document.getElementById('location');
    const mapDateDisplay   = getMapDateDisplay();
    const parameterLabel   = parameterSelect.querySelector(`option[value="${parameter}"]`).textContent.split(' (')[0];
    const scopeText        = (!isNational(scope) && !isRegional(scope)) ? scopes[scope] + ' ' : '';
    const locationText     = locationSelect.querySelector(`option[value="${locationId}"]`).textContent;

    document.querySelectorAll('#designations, #designations > *').forEach(el => el.classList.add('hidden'));

    const enabledReturns = Array.from(document.querySelectorAll('#return input[name="return"]:enabled'));
    enabledReturns.sort((a,b)=>["value","mean","anomaly","pctavg","rank"].indexOf(a.id)-["value","mean","anomaly","pctavg","rank"].indexOf(b.id));
    const groupedCols = isPcp(parameter) ? 3 : 2;
    const basePeriod = setUsBasePeriod();
    let row1 = "";
    let row2 = "";
    let groupHeaderAdded = false;

    const locationClass = isDivisional(scope) ? 'location sorter-digit' : 'location';
    row1 += `<th rowspan="2" class="${locationClass}">${locationHeader}</th>`;

    if (isConus(locationId) && isSubstate(scope)) {
        row1 += `<th rowspan="2" class="state">State</th>`;
    }

    enabledReturns.forEach(input => {
        const returnValue = input.id;

        // Skip Rank for City scope
        if (isCity(scope) && returnValue === 'rank') return;

        // Skip "Percent of Average" unless parameter is 'pcp'
        if (returnValue === 'pctavg' && parameter !== 'pcp') return;

        const labelElement = document.querySelector(`#return label[for="${returnValue}"]`);
        const labelTitle = (returnValue === 'mean' ? 'Period ' : '') +
            (labelElement ? labelElement.title : returnValue[0].toUpperCase() + returnValue.slice(1));

        const isGrouped = ['mean', 'anomaly', 'pctavg'].includes(returnValue);

        if (isGrouped) {
            // Add basePeriod once
            if (!groupHeaderAdded) {
                row1 += `<th colspan="${groupedCols}" class="center normal-font-weight">Period: ${basePeriod}</th>`;
                groupHeaderAdded = true;
            }

            // Add to sub-row (row 2)
            row2 += `<th class="${returnValue} sorter-digit">${labelTitle}</th>`;
        } else {
            // Standalone headers (Value, Rank)
            let cellContent = labelTitle;
            if (returnValue === 'rank') {
                cellContent += `<div class="small">${numYears} Years</div>`;
            }

            row1 += `<th rowspan="2" class="${returnValue} sorter-digit">${cellContent}</th>`;
        }
    });

    let tableHtml = `
<table id="values-table" class="shading bordered">
    <caption>${mapDateDisplay} ${locationText} ${scopeText}${parameterLabel}</caption>
    <thead>
        <tr>${row1}</tr>
        ${row2 ? `<tr>${row2}</tr>` : ''}
    </thead>
    <tbody>`;


    // city scope uses values.features.
    const dataValues = (isCity(scope) ? values.features : values);

    const idsByLocation = cag.constants.idsByLocation;

    const isCityScope = isCity(scope);
    const isDivisionalScope = isDivisional(scope);
    const isCountyScope = isCounty(scope);
    const isSubstateScope = isSubstate(scope);
    const isConusLocation = isConus(locationId);

    let showDesignations = false;
    let showTie = false;
    let showInsufficient = false;

    const rowsHtml = Object.entries(dataValues)
        .map(([valueLocation, locationValues]) => {
            const props = isCityScope
                ? locationValues.properties
                : locationValues;

            const tableLocationId = isCityScope
                ? locationValues.ghcnId
                : String(valueLocation);

            // ---- Filter Logic ----
            const checkLocation = isDivisionalScope
                ? tableLocationId.padStart(4, '0')
                : tableLocationId;

            const locationIds = idsByLocation[locationId];

            const isIncluded = locationIds
                ? locationIds.includes(checkLocation) || locationIds.includes(tableLocationId)
                : locationId === tableLocationId;

            if (!isIncluded) return '';

            // ---- Name Formatting ----
            let name = props.name
                .replace(' NWS Region', '')
                .replace(' Climate Region', '');

            if (isDivisionalScope) {
                name = `${parseInt(tableLocationId.slice(-2), 10)}. ${name}`;
            }

            if (
                isCountyScope &&
                isMaryland(locationId) &&
                tableLocationId === 'MD-511'
            ) {
                name += ', DC';
            }

            // ---- Time Series Link ----
            const tsLocation = isAgBelt(locationId) ? locationId : tableLocationId;

            const tsLink = `${base}/${scope}/time-series/${tsLocation}/${parameter}/${timescale}/${month}/${minYear}-${cag.constants.maxYear}`;

            // ---- Designation Logic ----
            const ties = parseInt(locationValues?.ties, 10) || 0;
            const isInsufficient = isInsufficientVariability(ties, numYears);

            if (!isCityScope && ties > 0) {
                showDesignations = true;

                if (isInsufficient) {
                    showInsufficient = true;
                } else {
                    showTie = true;
                }
            }

            // ---- Sort Value ----
            const sortVal = isDivisionalScope
                ? tableLocationId
                : isSubstateScope
                    ? `${props.stateName?.replace(/\s/g, '') ?? ''}${name}`
                    : name;

            // ---- Build Row ----
            let row = `
    <tr class="dataRow">
        <td class="location" data-sortval="${sortVal}">
            <a title="${name} ${parameterLabel} Time Series" href="${tsLink}">
                ${name}
            </a>
        </td>`;

            if (isConusLocation && isSubstateScope) {
                row += `
        <td class="state left">${props.stateName ?? ''}</td>`;
            }

            // ---- Value Columns ----
            enabledReturns.forEach(input => {
                const returnValue = input.id;

                // Skip: rank column for city scope
                if (isCityScope && returnValue === 'rank') return;

                const val = props[returnValue];
                const safeVal = val ?? '';

                row += `
        <td class="${returnValue}" data-sortval="${safeVal}">
            ${getValueDisplay(val, returnValue, tableLocationId)}
            ${setDesignation(ties, isInsufficient, scope, returnValue)}
        </td>`;
            });

            row += `
    </tr>`;

            return row;
        })
        .join('');

    tableHtml += rowsHtml;

    if (showDesignations) {
        document.getElementById('designations')?.classList.remove('hidden');

        if (showTie) {
            document.getElementById('tie-designation')?.classList.remove('hidden');
        }

        if (showInsufficient) {
            document.getElementById('insufficient-variability-designation')?.classList.remove('hidden');
        }
    }

    tableHtml += '</tbody></table>';

    document.getElementById('data-table').innerHTML = tableHtml;
    valuesTableSorter('#values-table', cag.constants.section);
}

const prevNextClick = makePrevNextClick(
    () => fillUsMappingMonths(),
    () => updateUsMappingData()
);

export function getUsMappingPrevNext(timescale, year, month, locationId, parameter, returnType) {
    ["prev", "next"].forEach(dir =>
        computeAndRenderPrevNext({
            direction: dir,
            clickHandler: prevNextClick,
            compute: isPrev => {
                const intTs = intTimescale(timescale, 12);
                const dateObj = new Date(year, month - 1);

                let begDateObj = new Date(dateObj);
                let endDateObj = new Date(dateObj);

                endDateObj.setMonth(endDateObj.getMonth() + (isPrev ? -1 : 1));
                const endYear = endDateObj.getFullYear();
                const endMonth = endDateObj.getMonth() + 1;
                const endDate = endYear + String(endMonth).padStart(2, "0");

                const boundary = isPrev ? cag.constants.minDate : cag.constants.maxDate;
                if ((isPrev && endDate < boundary) || (!isPrev && endDate > boundary)) {
                    return { valid: false };
                }

                begDateObj.setMonth(begDateObj.getMonth() + (isPrev ? -(intTs - 1) - 1 : 1 - (intTs - 1)));
                const begYear = begDateObj.getFullYear();
                const begMonth = begDateObj.getMonth() + 1;

                let title = "";
                if (intTs > 1) {
                    title = monthNames[begMonth - 1] + (begYear < endYear ? " " + begYear : "") + "&ndash;";
                }
                title += monthNames[endMonth - 1] + " " + endYear;

                return { valid: true, year: endYear, month: endMonth, dateStr: endDate, title };
            },
            hrefBuilder: (dateStr) =>
                `${base}/${scope}/${section}/${locationId}/${parameter}/${dateStr}/${timescale}/${returnType}`
        })
    );
}