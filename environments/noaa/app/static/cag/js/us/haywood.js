import { cag, base, scope, section } from '../globals.js';
import { fillUsLocations } from '../config/fill-us-locations.js';
import { plotHaywood } from '../shared/haywood/plot-haywood.js';
import Util from "../utils/util.js";

const getVal = Util.form.getVal;
const { updateUrl } = Util.config;

export function initUsHaywood() {
    const month = cag.variables.month;
    const monthElem = document.querySelector('#month');
    const selectedMonth = monthElem.querySelector(`option[value="${month}"]`) ? month : 12;
    monthElem.value = selectedMonth;

    cag.variables.url = getUsHaywoodUrl(cag.variables.locationId, cag.variables.parameter, cag.variables.month);
    plotHaywood(cag);

    document.getElementById('state').addEventListener('change', fillUsLocations);

    document.getElementById('submit').addEventListener('click', (event) => {
        event.preventDefault();
        updateData();
    });
}

function getUsHaywoodUrl(locationId, parameter, month){
    return `${base}/${scope}/${section}/${locationId}/${parameter}/${month}`;
}

function updateData() {
    if (!cag.variables.formChanged) {
        updateUrl();
        return false;
    }

    Object.assign(cag.variables, {
        parameter:   getVal('parameter'),
        month:       Number(getVal('month')),
        state:       getVal('state'),
        locationId:  getVal('location'),
        formState:   $('#select-form').serialize(),
        formChanged: false
    });

    const { parameter, month, state, locationId } = cag.variables;

    cag.variables.url = getUsHaywoodUrl(locationId, parameter, month);

    const pageState = { parameter, month, state, locationId };
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
