import { cag, base, scope, section } from '../globals.js';
import { initYearRange } from '../shared/year-ranges.js';
import {
    initTimeSeries,
    getQueryString,
    plotTimeSeriesData,
    begYearChange,
    endYearChange,
    begTrendYearChange,
    endTrendYearChange,
    basePeriodDisplayCheck
} from '../shared/time-series/time-series-core.js';
import Util from "../utils/util.js";
import FormUtil from '../utils/form-utils.js';
import ConfigUtil from '../utils/config-utils.js';

const { getVal, isChecked, isEnabled, getRadioVal } = FormUtil;
const { updateUrl } = ConfigUtil;
const { mobile: isMobile } = Util.is;

export function initGlobalTimeSeries() {
    const { parameters } = cag.constants;
    const { parameter, region } = cag.variables;
    cag.variables.url = getGlobalTimeSeriesUrl();
    cag.variables.qStr = getQueryString();

    initTimeSeries();
    document.getElementById('lat').value = parseFloat(cag.variables?.lat) || 0;
    document.getElementById('lon').value = parseFloat(cag.variables?.lon) || 0;

    initYearRange(region, parameter);

    plotTimeSeriesData();

    disablePlotDepartures();

    document.getElementById('parameter').addEventListener('change', setYearRanges);
    document.getElementById('region').addEventListener('change', setYearRanges);

    // submit click handled in js/config/global-form-config.js
}

function setYearRanges() {
    const rgn = document.getElementById('region').value;
    const param = document.getElementById('parameter').value;

    initYearRange(rgn, param);
    begYearChange();
    endYearChange();
    begTrendYearChange();
    endTrendYearChange();
    disablePlotDepartures();
}

export function updateGlobalTimeSeriesData() {
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
        region:         getVal('region'),
        lat:            Number(getVal('lat')),
        lon:            Number(getVal('lon')),
        surface:        getVal('surface'),
        basePeriod:     isChecked('base_prd'),
        begBaseYear:    Number(getVal('begbaseyear')),
        endBaseYear:    Number(getVal('endbaseyear')),
        plotDepartures: isChecked('plotDepartures'),
        trend:          isEnabled('trend-options') && isChecked('trend'),
        trend_base:     getRadioVal('trend_base'),
        begtrendyear:   getVal('begtrendyear'),
        endtrendyear:   getVal('endtrendyear'),
        filter:         getVal('filter'),
        formState:      $('#select-form').serialize(),
        formChanged:    false
    });

    cag.variables.url  = getGlobalTimeSeriesUrl();
    cag.variables.qStr = getQueryString();

    const {
        parameter, timescale, month, begyear, endyear, region, lat, lon, surface,
        basePeriod, begBaseYear, endBaseYear, plotDepartures,
        trend, trend_base, begtrendyear, endtrendyear, filter
    } = cag.variables;

    const pageState = {
        parameter, timescale, month, begyear, endyear, region, lat, lon, surface,
        basePeriod, begBaseYear, endBaseYear, plotDepartures,
        trend, trend_base, begtrendyear, endtrendyear, filter
    };

    plotTimeSeriesData();

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

function getGlobalTimeSeriesUrl() {
    const { parameter, region, lat, lon, surface, timescale, month, begyear, endyear } = cag.variables;
    const { parameters, globalRegions, surfaces } = cag.constants;

    const param = parameters[parameter] ? parameter : Object.keys(parameters)[0];
    const rgn = region === 'coords'
        ? `${parseFloat(lat)},${parseFloat(lon)}`
        : globalRegions[region]
            ? region
            : Object.keys(globalRegions)[0];
    const sfc = surfaces[surface] ? surface : Object.keys(surfaces)[0];
    const ts = (timescale === 'ytd' || (parseInt(timescale) > 0 && parseInt(timescale) < 100)) ? timescale : 1;
    const mn = month >= 0 && month <= 12 ? month : 1;
    const by = begyear >= parameters[parameter].minYear && begyear <= parameters[parameter].maxYear
        ? begyear
        : parameters[parameter].minYear;
    const ey = endyear >= by && endyear <= parameters[parameter].maxYear
        ? endyear
        : parameters[parameter].maxYear;

    return `${base}/${scope}/${section}/${rgn}/${sfc}/${param}/${ts}/${mn}/${by}-${ey}`;
}

function disablePlotDepartures(){
    const plotDeptElem = document.querySelector('#plotDepartures');
    if (plotDeptElem) {
        const isDisabled = document.querySelector('#parameter')?.value === 'tavg';
        plotDeptElem.disabled = isDisabled;
        plotDeptElem.closest('.checkbox-label')?.classList.toggle('disabled', isDisabled);
    }

    basePeriodDisplayCheck();
}