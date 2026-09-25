import { cag, section } from '../globals.js';
import { updateGlobalTimeSeriesData } from '../global/time-series.js';
import { updateGlobalRankingsData } from '../global/rankings.js';
import { updateGlobalHaywoodData } from '../global/haywood.js';

const parameters = cag.constants.parameters;
const regions = cag.constants.globalRegions || {};
const surfaces = cag.constants.surfaces || {};

const latMin = -90;
const latMax =  90;
const lonMin = -180;
const lonMax =  180;
const regionElem = document.querySelector('#region');

export function initGlobalForm() {
    fillGlobalParameters();

    if (section !== 'mapping') {
        fillRegions();
        fillSurfaces();

        document.querySelector('#parameter').addEventListener('change', disableLatLon);

        document.getElementById('submit').addEventListener('click', (event) => {
            event.preventDefault();
            validateInput();
        });

        regionElem.addEventListener('change', () => {
            disableLatLon();
            disableSurface();
        });

        document.getElementById('coords').addEventListener('click', () => {
            regionElem.value = 'coords';
            disableLatLon();
            disableSurface();
        });
    }

    document.querySelectorAll('#lat, #lon').forEach(el => {
        el.addEventListener('input', ({ target }) => {
            const isValid = validCoord(target.id, target.value);
            target.classList.toggle('form-error', !isValid);
        });
    });
}

function fillGlobalParameters() {
    const $elem = $('#parameter');
    const opts = [];

    $.each(parameters, (key, attr) => {
        const param = escapeHtml(key);
        const name  = escapeHtml(attr.title);

        opts.push(`<option value="${param}">${name}</option>`);
    });

    $elem.empty().append(opts.join(''));

    const selected = $elem.find(`option[value="${cag.variables.parameter}"]`).length > 0
        ? cag.variables.parameter
        : Object.keys(parameters)[0];
    $elem.val(selected);
}

function fillRegions() {
    const opts = [];

    $.each(regions, (key, attr) => {
        const val = escapeHtml(key);
        const name = escapeHtml(attr.title);

        opts.push(`<option value="${val}">${name}</option>`);
    });

    regionElem.innerHTML = opts.join('');

    const selected = regionElem.querySelector(`option[value="${cag.variables.region}"]`)
        ? cag.variables.region
        : Object.keys(regions)[0];
    regionElem.value = selected;
    disableLatLon();
}

function disableLatLon() {
    const $latlon = $('.latlon');
    const selectedRegion = regionElem.value;

    if (selectedRegion === 'coords') {
        $latlon.prop({ disabled: false, required: true });
    } else {
        $latlon.prop({ disabled: true, required: false });
    }
}

function validateInput() {
    if (regionElem.value === 'coords') {
        const lat = $('#lat').val();
        const lon = $('#lon').val();

        if (!validCoord('lat', lat)) {
            $('#lat').focus();
            alert(`Please enter a latitude value between ${latMin} and ${latMax}.`);
            return false;
        }

        if (!validCoord('lon', lon)) {
            $('#lon').focus();
            alert(`Please enter a longitude value between ${lonMin} and ${lonMax}.`);
            return false;
        }
    }

    if (section === 'time-series'){
        updateGlobalTimeSeriesData();
    } else if (section === 'rankings'){
        updateGlobalRankingsData();
    } else if (section === 'haywood'){
        updateGlobalHaywoodData();
    }

    return false;
}

function validCoord(coord, val) {
    const { min, max } = coord === 'lat'
        ? { min: latMin, max: latMax }
        : { min: lonMin, max: lonMax };

    return /^-?\d+(\.\d+)?$/.test(val) && val >= min && val <= max;
}

export function fillSurfaces() {
    const $elem = $('#surface');

    const opts = [];
    $.each(surfaces, (key, title) => {
        const param = escapeHtml(key);
        const name = escapeHtml(title);

        opts.push(`<option value="${param}">${name}</option>`);
    });

    $elem.empty().append(opts.join(''));

    const selected = $elem.find(`option[value="${cag.variables.surface}"]`).length > 0
        ? cag.variables.surface
        : Object.keys(surfaces)[0];
    $elem.val(selected);
    disableSurface();
}

function disableSurface() {
    const $surface        = $('#surface');
    const selectedSurface = $surface.val();
    const selectedRegion  = regionElem.value;

    $surface.find('option').each(function () {
        const surfaceKey = $(this).val();
        const isDisabled = !regions[selectedRegion]?.surfaces.includes(surfaceKey);
        $(this).prop('disabled', isDisabled);
    });

    const firstEnabledOption = $surface.find('option:enabled').first();
    const fallbackOption = firstEnabledOption.length
        ? firstEnabledOption.val()
        : $surface.find('option').first().val();
    $surface.val($surface.find(`option[value="${selectedSurface}"]`).is(':enabled')
        ? selectedSurface
        : fallbackOption);
}