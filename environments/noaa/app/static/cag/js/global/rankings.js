import { cag, base, scope, section, monthNames } from '../globals.js';
import { fillSurfaces } from '../config/global-form-config.js';
import { initYearRange } from '../shared/year-ranges.js';
import { initRankingsTable, updateRankingsTable } from '../shared/rankings/rankings-table.js';
import Util from '../utils/util.js';

const getVal = Util.form.getVal;
const updateUrl = Util.config.updateUrl;

export function initGlobalRankings() {
    const parameters = cag.constants.parameters;
    const { year, month, parameter } = cag.variables;
    cag.variables.date    = year + String(month).padStart(2, '0');
    cag.variables.begDate = parameters[parameter].minDate;
    cag.variables.endDate = parameters[parameter].maxDate;
    cag.variables.begYear = String(cag.variables.begDate).substring(0, 4);
    cag.variables.endYear = String(cag.variables.endDate).substring(0, 4);

    cag.variables.url = getGlobalRankingsUrl(true);

    initRankingsTable();
    fillSurfaces();
    initYearRange(cag.variables.region, cag.variables.parameter);
    fillMonths();
    document.getElementById('lat').value = cag.variables.lat;
    document.getElementById('lon').value = cag.variables.lon;

    document.getElementById('year').addEventListener('change', fillMonths);
    document.getElementById('parameter').addEventListener('change', setYearRanges);
    document.getElementById('region').addEventListener('change', setYearRanges);
    // submit click handled in js/config/global-form-config.js
}

function setYearRanges() {
    const rgn = document.getElementById('region').value;
    const param = document.getElementById('parameter').value;

    initYearRange(rgn, param);
    fillMonths();
}

function fillMonths() {
    const $monthElem        = $("#month");
    const selectedYear      = parseInt($("#year").val() ?? cag.variables.year, 10);
    const selectedMonth     = parseInt($monthElem.val() ?? cag.variables.month, 10);
    const selectedParameter = $("#parameter").val() ?? cag.variables.parameter;
    const parameterData     = cag.constants.parameters[selectedParameter];
    const selectedBegDate   = String(parameterData.minDate);
    const selectedEndDate   = String(parameterData.maxDate);
    const selectedBegYear   = parseInt(selectedBegDate.substring(0, 4), 10);
    const selectedEndYear   = parseInt(selectedEndDate.substring(0, 4), 10);
    const selectedBegMonth  = parseInt(selectedBegDate.slice(-2), 10);
    const selectedEndMonth  = parseInt(selectedEndDate.slice(-2), 10);

    const begMonth = (selectedYear === selectedBegYear) ? selectedBegMonth : 1;
    const endMonth = (selectedYear === selectedEndYear) ? selectedEndMonth : 12;

    const opts = [];
    for (let mon = begMonth; mon <= endMonth; mon++) {
        opts.push(`<option value="${mon}">${monthNames[mon - 1]}</option>`);
    }
    $monthElem.empty().append(opts.join(""));

    const isValidSelection = $monthElem.find(`option[value="${selectedMonth}"]`).length > 0;
    $monthElem.val(isValidSelection ? selectedMonth : begMonth);
}

export function getGlobalRankingsUrl(withDate){
    const { region, lat, lon, parameter, surface, date } = cag.variables;
    const coordsOrRegion = region === 'coords'
        ? (parseFloat(lat) + ',' + parseFloat(lon))
        : encodeURIComponent(region);
    return `${base}/global/${section}/${coordsOrRegion}/${parameter}/${surface}${withDate ? `/${date}` : ''}`;
}

export function updateGlobalRankingsData(){
    if (!cag.variables.formChanged) {
        updateUrl();
        return false;
    }

    Object.assign(cag.variables, {
        parameter:   getVal('parameter'),
        year:        Number(getVal('year')),
        month:       Number(getVal('month')),
        region:      getVal('region'),
        lat:         Number(getVal('lat')),
        lon:         Number(getVal('lon')),
        surface:     getVal('surface'),
        formState:   $('#select-form').serialize(),
        formChanged: false
    });

    const parameters = cag.constants.parameters;
    const parameter = cag.variables.parameter;

    Object.assign(cag.variables, {
        date:    cag.variables.year + String(cag.variables.month).padStart(2, "0"),
        url:     getGlobalRankingsUrl(true),
        begYear: String(parameters[parameter].minDate).substring(0, 4),
        endYear: String(parameters[parameter].maxDate).substring(0, 4)
    });

    const { year, month, date, region, lat, lon, surface } = cag.variables;

    const pageState = { year, month, date, region, lat, lon, surface };
    window.history.pushState(pageState, null, cag.variables.url + window.location.hash);

    // cache
    const cacheUrl = `${base}/${scope}/${section}/cache/?` + cag.variables.formState;
    fetch(cacheUrl, { credentials: "include" })
        .then(res => {
            if (!res.ok) throw new Error(`cache request failed ${cacheUrl}`);
        });

    updateRankingsTable('global');

    return false;
}

export function setGlobalRankingsTitle() {
    const parameters = cag.constants.parameters;
    const { parameter, year, month, region, surface, lat, lon } = cag.variables;
    const dateObj    = new Date(year, month, 0);
    const dateStr    = `${monthNames[dateObj.getMonth()]} ${dateObj.getFullYear()}`;
    const paramTitle = parameters[parameter].title + (parameter === 'tavg' ? ' Departures' : '');
    let title        = '';

    if (region === 'coords') {
        const formatCoordinate = (coord, pos, neg) => `${Math.abs(coord)}&deg;${coord < 0 ? pos : neg}`;
        title = `${formatCoordinate(lat, 'S', 'N')}, ${formatCoordinate(lon, 'W', 'E')}`;
    } else {
        title = `${cag.constants.globalRegions[region].title}${
            ['globe', 'nhem', 'shem'].includes(region)
                ? ` ${cag.constants.surfaces[surface]}`
                : ''}`;
    }

    $('#rankingsTitle').html(`
        <h3>${title}</h3>
        <h4>${dateStr} ${paramTitle} Rankings</h4>
    `);
}