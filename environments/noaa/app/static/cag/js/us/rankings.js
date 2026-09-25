import { cag, base, scope, section, monthNames } from '../globals.js';
import { initYearRange } from '../shared/year-ranges.js';
import { fillUsLocations } from '../config/fill-us-locations.js';
import { initRankingsTable, updateRankingsTable } from '../shared/rankings/rankings-table.js';
import Util from '../utils/util.js';

const { alaska: isAlaska, hawaii: isHawaii } = Util.location.is;
const { divisional: isDivisional, county: isCounty, city: isCity } = Util.scope.is;
const { getVal } = Util.form;
const { updateUrl } = Util.config;

const { parameters, locations } = cag.constants;

export function initUsRankings() {
    const { year, month, locationId } = cag.variables;

    cag.variables.date = `${year}${String(month).padStart(2, "0")}`;
    cag.variables.url  = getUsRankingsUrl(true);

    initYearRange(locationId);
    fillMonths();

    initRankingsTable();

    document.getElementById('state').addEventListener('change', fillUsLocations);
    document.getElementById('year').addEventListener('change', fillMonths);
    document.getElementById('location').addEventListener('change', fillMonths);

    document.getElementById('submit').addEventListener('click', e => {
        e.preventDefault();
        updateUsRankingsData();
    });
}

function fillMonths() {
    const { month, begYear, begMonth, endYear, endMonth } = cag.variables;

    const $monthElem    = $("#month");
    const selectedYear  = $("#year").val();
    const selectedMonth = $("#month").val() ?? month;
    const thisBegMonth  = (selectedYear == begYear ? begMonth : 1);
    const thisEndMonth  = (selectedYear == endYear ? endMonth : 12);

    let opts = [];
    for (let mon = thisBegMonth; mon <= thisEndMonth; mon++) {
        opts.push(`<option value="${mon}">${monthNames[mon-1]}</option>`);
    }
    $monthElem.empty().append(opts.join(""));

    const selected = $monthElem.find(`option[value="${selectedMonth}"]`).length > 0 ? selectedMonth : 1;
    $monthElem.val(selected);
}

export function getUsRankingsUrl(withDate) {
    const { locationId, parameter, date } = cag.variables;
    return `${base}/${scope}/${section}/${locationId}/${parameter}${withDate ? `/${date}` : ''}`;
}

export function updateUsRankingsData() {
    if (!cag.variables.formChanged) {
        updateUrl();
        return false;
    }

    Object.assign(cag.variables, {
        parameter:   getVal('parameter'),
        year:        Number(getVal('year')),
        month:       Number(getVal('month')),
        state:       getVal('state'),
        locationId:  getVal('location'),
        formState:   $('#select-form').serialize(),
        formChanged: false
    });

    cag.variables.date = cag.variables.year + String(cag.variables.month).padStart(2, "0");

    const begDates = cag.constants.begDates;
    const { parameter, year, month, date, locationId } = cag.variables;

    // Update Beginning Date
    if (isAlaska(scope, section, locationId)) {
        cag.variables.begDate = begDates.alaska;
    } else if (isHawaii(scope, section, locationId)) {
        cag.variables.begDate = begDates.hawaii;
    } else if (isCity(scope)) {
        cag.variables.begDate = begDates[locationId];
    } else {
        cag.variables.begDate = begDates.national;
    }

    Object.assign(cag.variables, {
        begYear: String(cag.variables.begDate).substring(0, 4),
        date:    `${cag.variables.year}${String(cag.variables.month).padStart(2, "0")}`,
    });

    cag.variables.url = getUsRankingsUrl(true);

    updateRankingsTable(scope);

    const pageState = { parameter, year, month, date, locationId };

    window.history.pushState(
        pageState,
        null,
        cag.variables.url + window.location.hash
    );

    // cache
    const cacheUrl = `${base}/${scope}/${section}/cache/?` + cag.variables.formState;
    fetch(cacheUrl, { credentials: "include" })
        .then(res => {
            if (!res.ok) throw new Error(`cache request failed ${cacheUrl}`);
        });

    return false;
}

export function setUsRankingsTitle(){
    const { usStates, locations } = cag.constants;
    const { year, month } = cag.variables;

    const dateObj = new Date(year, month, 0);
    const dateStr = monthNames[dateObj.getMonth()] + ' ' + dateObj.getFullYear();
    const paramTitle = parameters[cag.variables.parameter]['title'];
    const locationId = cag.variables.locationId;

    let locTitle = '';

    if (isDivisional(scope)) {
        locTitle = usStates[locations[locationId].stateId].name + ', Climate Division ' + parseInt(String(locationId).slice(-2));
    } else {
        locTitle = locations[locationId]['name'].replace(' Climate Region', '');
        if (isCounty(scope) || isCity(scope)) {
            locTitle += ', ' + usStates[locations[locationId].stateId].name;
        }
    }

    const title = `<h3>${locTitle}</h3><h4>${dateStr} ${paramTitle} Rankings</h4>`;

    $('#rankingsTitle').html(title);
}