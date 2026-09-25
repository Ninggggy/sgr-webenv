import { cag, base, scope, section } from '../globals.js';
import { fillSurfaces } from '../config/global-form-config.js';
import { plotHaywood } from '../shared/haywood/plot-haywood.js';
import Util from '../utils/util.js';

const getVal = Util.form.getVal;
const { updateUrl } = Util.config;

export function initGlobalHaywood() {
    const { parameter, region, surface, month, lat, lon } = cag.variables;

    fillSurfaces();

    const monthElem = document.querySelector('#month');
    const selectedMonth = monthElem.querySelector(`option[value="${month}"]`) ? month : 1;
    monthElem.value = selectedMonth;

    document.getElementById('lat').value = lat;
    document.getElementById('lon').value = lon;
    // submit click handled in js/config/global-form-config.js

    cag.variables.url = getGlobalHaywoodUrl(parameter, region, surface, month, lat, lon);
    plotHaywood(cag);
}


export function getGlobalHaywoodUrl(region, parameter, surface, month, lat, lon) {
    const rgnUrl = region === 'coords' ? `${lat},${lon}` : region;
    return `${base}/${scope}/${section}/${parameter}/${rgnUrl}/${surface}/${month}`;
    //return `${base}/${scope}/${section}/${rgnUrl}/${parameter}/${surface}/${month}`;
}

export function updateGlobalHaywoodData() {
    if (!cag.variables.formChanged) {
        updateUrl();
        return false;
    }

    Object.assign(cag.variables, {
        parameter:   getVal('parameter'),
        month:       Number(getVal('month')),
        region:      getVal('region'),
        lat:         Number(getVal('lat')),
        lon:         Number(getVal('lon')),
        surface:     getVal('surface'),
        formState:   $('#select-form').serialize(),
        formChanged: false
    });

    const { parameter, month, region, lat, lon, surface } = cag.variables;

    cag.variables.url = getGlobalHaywoodUrl(parameter, region, surface, month, lat, lon);

    const pageState = { parameter, month, region, lat, lon, surface };
    window.history.pushState(pageState, null, cag.variables.url + window.location.hash);

    // cache
    const cacheUrl = `${base}/${scope}/${section}/cache/?` + cag.variables.formState;
    fetch(cacheUrl, { credentials: "include" })
        .then(res => {
            if (!res.ok) throw new Error(`cache request failed ${cacheUrl}`);
        });

    plotHaywood(cag);

    return false;
}
