import { cag, base, scope, timescales, filters, basePeriods, monthNames } from '../../globals.js';
import { getDateDisplay } from '../date-display.js';
import { plotTimeSeries } from './plot-time-series.js';
import { RankingsService } from '../rankings/RankingsService.js';
import { setDesignation } from '../designations.js';
import { valuesTableSorter } from "../tablesorter.js";
import Util from '../../utils/util.js';

const {
    global: isGlobal,
    national: isNational,
    regional: isRegional,
    substate: isSubstate
} = Util.scope.is;
const isTemp = Util.parameter.is.temp;
const configDownload = Util.config.configDownload;
const isGlobalTavg = (scope, parameter) => isGlobal(scope) && parameter === 'tavg';
const {insufficientVariability: isInsufficientVariability } = Util.is;

export function initTimeSeries() {
    const { month, basePeriod, plotDepartures, trend, trend_base, filter } = cag.variables;

    fillTimescales();
    fillFilters(filters);

    const monthElem = document.querySelector('#month');
    const selectedMonth = monthElem.querySelector(`option[value="${month}"]`) ? month : 1;
    monthElem.value = selectedMonth;

    document.getElementById('base_prd').checked = basePeriod;
    document.getElementById('plotDepartures').checked = plotDepartures;
    document.getElementById('trend').checked = trend;
    document.querySelector(`input[name="trend_base"][value="${trend_base}"]`).checked = true;

    basePeriodDisplayCheck();
    begYearChange();
    endYearChange();
    begBaseYearChange();
    endBaseYearChange();
    begTrendYearChange();
    endTrendYearChange();
    trendDisplayCheck();

    setTrendDisableNote();
    document.querySelector('#month').addEventListener('change', disableTrend);

    document.querySelector('#base_prd').addEventListener('click', basePeriodDisplayCheck);
    document.querySelector('#trend').addEventListener('click', trendDisplayCheck);

    document.querySelector('#begyear').addEventListener('change', begYearChange);
    document.querySelector('#endyear').addEventListener('change', endYearChange);

    document.querySelector('#begbaseyear').addEventListener('change', begBaseYearChange);
    document.querySelector('#endbaseyear').addEventListener('change', endBaseYearChange);

    document.querySelector('#begtrendyear').addEventListener('change', begTrendYearChange);
    document.querySelector('#endtrendyear').addEventListener('change', endTrendYearChange);
}

export function fillTimescales() {
    const timescale = cag.variables.timescale;
    const elem = document.getElementById('timescale');
    if (!elem) return;

    const opts = timescales.map((ts) => {
        const name = ts === 'ytd' ? 'Year-to-Date' : `${parseInt(ts, 10)}-Month`;
        return `<option value="${ts}">${name}</option>`;
    });

    elem.innerHTML = opts.join('');

    const hasOption = elem.querySelector(`option[value="${timescale}"]`) !== null;
    elem.value = hasOption ? timescale : 1;
}

export function fillFilters(filters) {
    const filter = cag.variables.filter;
    const elem = document.getElementById('filter');
    if (!elem) return;

    const opts = [`<option value="none">No Filter</option>`];

    opts.push(...Object.entries(filters).map(([key, attr]) => {
        return `<option value="${key}">${attr.name}</option>`;
    }));

    elem.innerHTML = opts.join('');

    const selected = filters[filter] ? filter : 'none';

    elem.value = selected;
}

export function getQueryString() {
    const params = new URLSearchParams();
    const {
        basePeriod,
        parameter,
        begBaseYear,
        endBaseYear,
        plotDepartures,
        trend,
        trend_base,
        begtrendyear,
        endtrendyear,
        filter
    } = cag.variables;


    if (basePeriod) {
        params.append('base_prd', 'true');
        params.append('begbaseyear', parseInt(begBaseYear, 10));
        params.append('endbaseyear', parseInt(endBaseYear, 10));
        if (plotDepartures) params.append('plotDepartures', true);
    }

    if (!$('#trend').prop('disabled') && trend) {
        params.append('trend', 'true');
        params.append('trend_base', parseInt(trend_base, 10));
        params.append('begtrendyear', parseInt(begtrendyear, 10));
        params.append('endtrendyear', parseInt(endtrendyear, 10));
    }

    if (filter && filter !== 'none') {
        const cleanedFilter = filter.replace(/[^-\w]/g, '');
        params.append('filter', cleanedFilter);
    }

    const qs = params.toString();
    return qs ? `?${qs}` : '';
}

export async function plotTimeSeriesData() {
    const downloadElem = document.getElementById('download');
    const chartElem = document.getElementById('chartCanvas');
    const dataTableElem = document.getElementById('data-table');

    const { basePeriod, parameter, begBaseYear, endBaseYear } = cag.variables;

    zingchart.exec('chartCanvas', 'destroy');

    if (downloadElem) downloadElem.style.display = 'none';

    if (dataTableElem) {
        dataTableElem.innerHTML = `
            <div class="center pad">
                <img alt="loader" src="/monitoring-content/lib/images/noaa-loader.gif">
            </div>
        `;
    }

    const timeSeriesData = await plotTimeSeries(cag);

    if (!timeSeriesData) {
        if (chartElem) {
            chartElem.innerHTML = '<div class="red-txt pad">Data failed to load. Please try again.</div>';
        }
        if (dataTableElem) {
            dataTableElem.innerHTML = '';
        }
    } else {
        if (chartElem) {
            chartElem.innerHTML = '';
        }

        const basePrdQstr = basePeriod
            ? `?base_prd=true&begbaseyear=${parseInt(begBaseYear, 10)}&endbaseyear=${parseInt(endBaseYear, 10)}`
            : '';

        configDownload(cag.variables.url, basePrdQstr);

        await createTimeSeriesDataTable(
            timeSeriesData.title,
            timeSeriesData.subtitle,
            timeSeriesData.dates,
            timeSeriesData.values,
            timeSeriesData.mean,
            timeSeriesData.meanText
        );

        if (downloadElem) {
            downloadElem.style.display = '';
        }
    }
}

export async function createTimeSeriesDataTable(title, subtitle, dates, values, mean, meanText) {
    document.querySelectorAll('#designations, #designations > *')
        .forEach(el => el.classList.add('hidden'));

    const dataTableElem = document.getElementById('data-table');
    if (!dataTableElem) return;

    const parameters = cag.constants.parameters;
    const { parameter, timescale, month, basePeriod, begBaseYear, endBaseYear } = cag.variables;

    const rankingsService = new RankingsService();
    const ranks        = Object.values(await rankingsService.getRanks(values));
    const nationalTemp = (isNational(scope) && isTemp(parameter));
    const precision    = parseInt(nationalTemp ? 2 : parameters[parameter]['precision']);
    const units        = parameters[parameter]['units'];
    const rankYears    = values.length ? values.filter(value => value !== null).length : 0;
    const dateHeader   = timescale == 12 && month == 12
        ? 'Year'
        : (timescale == 1 || (timescale === 'ytd' && month == 1) || month == 0)
            ? 'Date'
            : 'Period';
    const paramTitle = ['pdsi', 'phdi', 'pmdi', 'zndx'].includes(parameter)
        ? parameters[parameter]['shortTitle']
        : parameters[parameter]['title'];

    const table = document.createElement('table');
    table.id = 'values-table';
    table.className = 'bordered shading';

    const caption = document.createElement('caption');

    const titleDiv = document.createElement('div');
    titleDiv.id = 'values-table-title';
    titleDiv.textContent = title;

    const subtitleDiv = document.createElement('div');
    subtitleDiv.id = 'values-table-subtitle';
    subtitleDiv.textContent = subtitle;

    caption.appendChild(titleDiv).appendChild(subtitleDiv);
    table.appendChild(caption);

    const thead = document.createElement('thead');
    const headerRow1 = document.createElement('tr');
    const headerRow2 = document.createElement('tr');

    // Determine necessity of second row (complex header)
    // Scenarios 3, 4, and 5 require 2 rows.
    const isDoubleRow = basePeriod && (month == 0 || parameter === 'pcp');

    /**
     * Helper to set rowspan/colspan only if needed
     */
    const setSpan = (el, row, col) => {
        if (row > 1) el.setAttribute('rowspan', row);
        if (col > 1) el.setAttribute('colspan', col);
    };

    // DATE HEADER
    const dateHeaderCell = document.createElement('th');
    dateHeaderCell.textContent = dateHeader;
    if (isDoubleRow) setSpan(dateHeaderCell, 2, 1);
    headerRow1.appendChild(dateHeaderCell);

    const hideRawValueColumn = isGlobalTavg(scope, parameter) && basePeriod;

    // PARAMETER HEADER (Precip or Temp)
    if (!hideRawValueColumn) {
        const paramHeaderCell = document.createElement('th');
        paramHeaderCell.textContent = paramTitle;
        if (isDoubleRow) setSpan(paramHeaderCell, 2, 1);
        headerRow1.appendChild(paramHeaderCell);
    }

    // BASE PERIOD LOGIC
    if (basePeriod) {
        const anomText = `Departure` + (parameter === 'pcp' ? ' from Average' : '');
        const pctAvgText = 'Percent of Average';

        if (isDoubleRow) {
            // Scenarios 3, 4, and 5: Double Row
            const groupHeaderCell = document.createElement('th');
            groupHeaderCell.classList = 'center normal-font-weight';

            if (month > 0 && parameter === 'pcp') {
                // Scenario 3: PCP Month > 0
                setSpan(groupHeaderCell, 1, 2);
                // e.g., 1901-2000 Average: 2.51"
                groupHeaderCell.innerHTML = meanText;

                headerRow2.innerHTML = `<th>${anomText}</th><th>${pctAvgText}</th>`;
            }
            else if (month == 0) {
                // Scenario 4 & 5: Monthly Mean tables
                const colSpanCount = (parameter === 'pcp') ? 3 : 2;
                setSpan(groupHeaderCell, 1, colSpanCount);
                groupHeaderCell.textContent = `Period: ${parseInt(begBaseYear)}-${parseInt(endBaseYear)}`;

                let row2Html = `<th>Period Average</th><th>${anomText}</th>`;
                if (parameter === 'pcp') row2Html += `<th>${pctAvgText}</th>`;
                headerRow2.innerHTML = row2Html;
            }

            headerRow1.appendChild(groupHeaderCell);
        } else {
            // Scenario 2: Single row with Anomaly + Mean Text
            const anomalyHeaderCell = document.createElement('th');
            anomalyHeaderCell.innerHTML = isGlobalTavg(scope, parameter) ? 'Average Temperature Departure' : `${anomText}<div class="small">${meanText}</div>`;
            headerRow1.appendChild(anomalyHeaderCell);
        }
    }

    // RANK HEADER
    const rankHeaderCell = document.createElement('th');
    rankHeaderCell.innerHTML = `Rank<div class="small">(out of ${rankYears})</div>`;
    if (isDoubleRow) setSpan(rankHeaderCell, 2, 1);
    headerRow1.appendChild(rankHeaderCell);

    thead.appendChild(headerRow1);
    if (isDoubleRow) {
        thead.appendChild(headerRow2);
    }
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    tbody.setAttribute('role', 'rowgroup');
    let begin = false;

    // for getTies
    const valuesObj = Object.fromEntries(
        dates.map((date, i) => [date, values[i]])
    );

    for (let ndx = 0; ndx < dates.length; ndx++) {
        const dateLabel = dates[ndx];

        let value = parseFloat(values[ndx]);
        // Convert negative zero to positive zero
        if (Object.is(value, -0)) {
            value = 0;
        }

        if (value !== null) {
            begin = true;
        } else if (!begin) {
            return;
        }

        let year, valMonth;
        if (month > 0) {
            year = parseInt(dateLabel);
            valMonth = parseInt(month);
        } else {
            year = parseInt(dateLabel.slice(-4));
            valMonth = [
                'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
            ].indexOf(dateLabel.slice(0, 3)) + 1;
        }

        const date = year + String(valMonth).padStart(2, '0');
        const dateDisplay = getDateDisplay(date, valMonth, timescale);

        const dateDisplayLink = document.createElement('a');
        dateDisplayLink.title = `Link to Map of ${dateDisplay.textContent} ${paramTitle}`;
        dateDisplayLink.href = getMappingLink(date);
        dateDisplayLink.appendChild(dateDisplay);

        const row = document.createElement('tr');
        if (values.filter(v => v == value).length > 1) {
            row.className = 'tie';
        }

        const dateCell = document.createElement('td');
        dateCell.className = 'left';
        dateCell.dataset.sortval = parseInt(date);
        dateCell.appendChild(dateDisplayLink);
        row.appendChild(dateCell);

        const tieDateSearch = month > 0
                ? String(year)
                : monthNames[valMonth - 1].substring(0, 3) + ' ' + year;
        const ties = await rankingsService.getTies(valuesObj, tieDateSearch);
        delete ties[tieDateSearch];
        const isInsufficient = isInsufficientVariability(ties.length, rankYears);
        if (ties.length > 0) {
            document.getElementById('designations').classList.remove('hidden');
            const designationId = `${isInsufficient ? 'insufficient-variability' : 'tie'}-designation`;
            const designationEl = document.getElementById(designationId);
            if (designationEl) {
                designationEl.classList.remove('hidden');
            }
        }

        if (value === null || isNaN(value)) {
            for (let i = 0; i < (basePeriod ? (month == 0 ? 4 : 3) : 2); i++) {
                const emptyCell = document.createElement('td');
                emptyCell.dataset.sortval = '';
                emptyCell.textContent = '--';
                row.appendChild(emptyCell);
            }
        } else {
            const dispValue = value.toFixed(precision);

            const valueCell = document.createElement('td');
            valueCell.dataset.sortval = value;
            valueCell.textContent = `${dispValue}${units}`;
            
            if (!hideRawValueColumn) {
                row.appendChild(valueCell);
            }

            if (basePeriod) {
                let meanVal = month == 0 ? mean[parseInt(String(date).slice(-2))] : mean[month];

                if (month == 0) {
                    const meanValDisp = meanVal.toFixed(precision);
                    const meanCell = document.createElement('td');
                    meanCell.textContent = `${meanValDisp}${units}`;
                    row.appendChild(meanCell);
                }

                const anomalyCell = document.createElement('td');
                const anomVal = (value - meanVal).toFixed(precision);
                anomalyCell.textContent = `${anomVal}${units}`;
                row.appendChild(anomalyCell);

                if (parameter === 'pcp') {
                    const pctavgCell = document.createElement('td');
                    const pctAvg = (value * 100/meanVal).toFixed(1);
                    pctavgCell.textContent = `${pctAvg}%`;
                    row.appendChild(pctavgCell);
                }
            }

            const rank = parseInt(ranks[ndx], 10);
            const rankHref = getRankingsLink(valMonth, date);
            const rankCell = document.createElement('td');
            rankCell.className = 'rank'
            rankCell.dataset.sortval = rank;
            const rankLink = document.createElement('a');
            rankLink.title = `Link to ${dateDisplay.textContent} ${title} Rankings`;
            rankLink.href = rankHref;
            rankLink.textContent = rank;
            rankCell.appendChild(rankLink);
            rankCell.insertAdjacentHTML('beforeend', setDesignation(ties.length, isInsufficient));
            row.appendChild(rankCell);
        }

        tbody.appendChild(row);
    }

    table.appendChild(tbody);

    dataTableElem.replaceChildren(table)
    valuesTableSorter('#values-table', cag.constants.section);
}

function getMappingLink(date) {
    const mappingBase = `${base}/${encodeURIComponent(scope)}/mapping`;
    const parameter = cag.variables.parameter;
    const timescale = cag.variables.timescale;

    if (isGlobal(scope)) {
        const mappingType = parameter === 'tavg' ? 'anomaly' : 'value';
        return `${mappingBase}/${encodeURIComponent(parameter)}/${parseInt(date, 10)}/${encodeURIComponent(mappingType)}`;
    } else {
        let mapLocation = cag.variables.locationId;
        if (isRegional(scope)) {
            const regionId = $(`#location [value="${mapLocation}"]`).parent().data('regionid');
            if (regionId) {
                mapLocation = regionId;
            }
        } else if (isSubstate(scope)) {
            mapLocation = cag.variables.state;
        }

        const loc = encodeURIComponent(mapLocation);
        const param = encodeURIComponent(parameter);
        const ts = encodeURIComponent(timescale);
        return `${mappingBase}/${loc}/${param}/${parseInt(date, 10)}/${encodeURIComponent(ts)}`;
    }
}

export function getRankingsLink(valMonth, date) {
    const { timescale, parameter } = cag.variables;
    const rankingsBase = `${base}/${encodeURIComponent(scope)}/rankings`;
    const timescaleFragment = timescale === 'ytd' ? valMonth : parseInt(timescale, 10);

    if (isGlobal(scope)) {
        const { region, lat, lon, surface } = cag.variables;
        const latOrCoords = region === 'coords'
            ? (parseFloat(lat) + ',' + parseFloat(lon))
            : encodeURIComponent(region);
        return `${rankingsBase}/${latOrCoords}/${encodeURIComponent(parameter)}/${encodeURIComponent(surface)}/${date}#${timescaleFragment}`;
    } else {
        const locationId = cag.variables.locationId;
        return `${rankingsBase}/${encodeURIComponent(locationId)}/${encodeURIComponent(parameter)}/${date}#${timescaleFragment}`;
    }
}

export function basePeriodDisplayCheck() {
    const basePrdCheckbox = document.getElementById('base_prd');
    const begBaseYear     = document.getElementById('begbaseyear');
    const endBaseYear     = document.getElementById('endbaseyear');
    const plotDept        = document.getElementById('plotDepartures');

    if (basePrdCheckbox && begBaseYear && endBaseYear) {
        const isDisabled = !basePrdCheckbox.checked;

        begBaseYear.disabled = isDisabled;
        endBaseYear.disabled = isDisabled;

        if (plotDept) {
            const isGlobalTavgAnom = isGlobalTavg(scope, document.querySelector('#parameter')?.value);
            plotDept.disabled = isDisabled || isGlobalTavgAnom;
            plotDept.closest('.checkbox-label')?.classList.toggle('disabled', plotDept.disabled);
        }
    }

    const baseSlider = document.getElementById('base-period-slider');
    if (baseSlider && basePrdCheckbox) {
        const handles = baseSlider.querySelectorAll('.noUi-handle');
        
        if (basePrdCheckbox.checked) {
            baseSlider.removeAttribute('disabled');
            handles.forEach(handle => handle.setAttribute('tabindex', '0'));
        } else {
            baseSlider.setAttribute('disabled', true);
            handles.forEach(handle => handle.setAttribute('tabindex', '-1'));
        }
    }
}

export function trendDisplayCheck() {
    const trendCheckbox = document.getElementById('trend');
    const targets = [
        document.getElementById('trend_base_decade'),
        document.getElementById('trend_base_century'),
        document.getElementById('begtrendyear'),
        document.getElementById('endtrendyear')
    ];

    if (trendCheckbox) {
        const isDisabled = !trendCheckbox.checked;

        targets.forEach(el => {
            if (el) el.disabled = isDisabled;
        });
    }

    const trendSlider = document.getElementById('trend-period-slider');
    if (trendSlider && trendCheckbox) {
        const handles = trendSlider.querySelectorAll('.noUi-handle');

        if (trendCheckbox.checked) {
            trendSlider.removeAttribute('disabled');
            handles.forEach(handle => handle.setAttribute('tabindex', '0'));
        } else {
            trendSlider.setAttribute('disabled', true);
            handles.forEach(handle => handle.setAttribute('tabindex', '-1'));
        }
    }
}

function setTrendDisableNote() {
    const trendInfoPopup = document.getElementById('trend-info-popup');
    const trendNoteLink = document.getElementById('trend-note-link');
    if (!trendInfoPopup || !trendNoteLink) return;

    if (Util.is.mobile) {
        // Ensure the close button exists only once
        if (!trendInfoPopup.querySelector('.btn-close')) {
            trendInfoPopup.insertAdjacentHTML(
                'beforeend',
                '<button type="button" class="btn-close small absolute" aria-label="Close"></button>'
            );
        }

        // Toggle popup on click for mobile devices
        trendNoteLink.onclick = () => {
            const isCurrentlyHidden = trendInfoPopup.style.display === 'none' || getComputedStyle(trendInfoPopup).display === 'none';

            trendInfoPopup.style.display = isCurrentlyHidden ? 'block' : 'none';
            trendInfoPopup.setAttribute('aria-hidden', (!isCurrentlyHidden).toString());
        };

    } else {
        // For non-mobile devices, show/hide popup on hover
        trendNoteLink.onclick = null;

        trendNoteLink.onmouseenter = () => {
            trendInfoPopup.style.display = 'block';
            trendInfoPopup.setAttribute('aria-hidden', 'false');
        };

        trendNoteLink.onmouseleave = () => {
            trendInfoPopup.style.display = 'none';
            trendInfoPopup.setAttribute('aria-hidden', 'true');
        };
    }

    disableTrend();
}

export const disableTrend = () => {
    const trendOptions = document.getElementById('trend-options');
    const month = document.getElementById('month');

    // Disable trend options if month value is '0' and update display accordingly
    if (trendOptions && month) {
        trendOptions.disabled = month.value === '0';
    }
    trendDisplayCheck();
};

const syncYears = (sourceId, targetId, condition) => {
    const source = document.getElementById(sourceId);
    const target = document.getElementById(targetId);
    if (!source || !target) return;

    const sourceVal = parseInt(source.value, 10);
    const targetVal = parseInt(target.value, 10);

    if (condition(sourceVal, targetVal)) {
        target.value = source.value;
    }
};

export function begYearChange() {
    syncYears('begyear', 'endyear', (beg, end) => beg > end);
}

export function endYearChange() {
    syncYears('endyear', 'begyear', (end, beg) => end < beg);
}

export function begBaseYearChange() {
    syncYears('begbaseyear', 'endbaseyear', (beg, end) => beg > end);
}

export function endBaseYearChange() {
    syncYears('endbaseyear', 'begbaseyear', (end, beg) => end < beg);
}

export function begTrendYearChange() {
    syncYears('begtrendyear', 'endtrendyear', (beg, end) => beg > end);
}

export function endTrendYearChange() {
    syncYears('endtrendyear', 'begtrendyear', (end, beg) => end < beg);
}