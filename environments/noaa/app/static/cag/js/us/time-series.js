import { cag, base, scope, section } from '../globals.js';
import { initYearRange } from '../shared/year-ranges.js';
import { fillUsLocations } from '../config/fill-us-locations.js';
import {
    initTimeSeries,
    getQueryString,
    plotTimeSeriesData
} from '../shared/time-series/time-series-core.js';
import Util from "../utils/util.js";

const { updateUrl, disableTimescales } = Util.config;
const { getVal, isChecked, isEnabled, getRadioVal } = Util.form;

export function initUsTimeSeries() {
    cag.variables.url = getUsTimeSeriesUrl();
    cag.variables.qStr = getQueryString();

    const locations  = cag.constants.locations;
    const locationId = cag.variables.locationId;

    initTimeSeries();
    const { minYear, maxYear } = locations[locationId];
    initYearRange(locationId);
    disableTimescales();

    plotTimeSeriesData();

    document.getElementById('state').addEventListener('change', fillUsLocations);
    document.getElementById('parameter').addEventListener('change', disableTimescales);

    document.getElementById('submit').addEventListener('click', (event) => {
        event.preventDefault();
        updateUsTimeSeriesData();
    });
}

function updateUsTimeSeriesData(){
    if (!cag.variables.formChanged) {
        updateUrl();
        return false;
    }

    Object.assign(cag.variables, {
        parameter:      getVal('parameter'),
        timescale:      getVal('timescale'),
        month:          Number(getVal('month')),
        begyear:        Number(getVal('begyear')),
        endyear:        Number(getVal('endyear')),
        state:          getVal('state'),
        locationId:     getVal('location'),
        basePeriod:     isChecked('base_prd'),
        begBaseYear:    Number(getVal('begbaseyear')),
        endBaseYear:    Number(getVal('endbaseyear')),
        plotDepartures: isChecked('plotDepartures'),
        trend:          isEnabled('trend-options') && isChecked('trend'),
        trend_base:     getRadioVal('trend_base'),
        begtrendyear:   Number(getVal('begtrendyear')),
        endtrendyear:   Number(getVal('endtrendyear')),
        filter:         getVal('filter'),
        formState:      $('#select-form').serialize(),
        formChanged:    false
    });

    cag.variables.url  = getUsTimeSeriesUrl();
    cag.variables.qStr = getQueryString();

    plotTimeSeriesData();

    const {
        parameter, timescale, month, begyear, endyear, state, locationId,
        basePeriod, begBaseYear, endBaseYear, plotDepartures,
        trend, trend_base, begtrendyear, endtrendyear, filter
    } = cag.variables;

    const pageState = {
        parameter, timescale, month, begyear, endyear, state,
        locationId, basePeriod, begBaseYear, endBaseYear, trend,
        trend_base, begtrendyear, endtrendyear, filter
    };

    window.history.pushState(
        pageState,
        null,
        `${cag.variables.url}${cag.variables.qStr}${window.location.hash}`
    );

    // cache
    const cacheUrl = `${base}/${scope}/${section}/cache/?${cag.variables.formState}`;
    fetch(cacheUrl, { credentials: "include" })
        .then(res => {
            if (!res.ok) throw new Error(`cache request failed ${cacheUrl}`);
        });

    return false;
}

function getUsTimeSeriesUrl() {
    const {locationId, parameter, timescale, month, begyear, endyear } = cag.variables;
    return `${base}/${scope}/${section}/${locationId}/${parameter}/${timescale}/${month}/${begyear}-${endyear}`;
}
