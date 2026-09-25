import { cag, scope, basePeriods, monthNames } from "../../globals.js";
import { setGlobalRankingsTitle, updateGlobalRankingsData, getGlobalRankingsUrl } from "../../global/rankings.js";
import { setUsRankingsTitle, updateUsRankingsData, getUsRankingsUrl } from "../../us/rankings.js";
import { RankingsDao } from '../dao/RankingsDao.js';
import { setDesignation } from "../designations.js";
import Util from "../../utils/util.js";

const isGlobal = Util.scope.is.global;
const {
    temp:      isTemp,
    precip:    isPrecip,
    palmer:    isPalmer,
    degreeDay: isDegreeDay
} = Util.parameter.is;
const configDownload = Util.config.configDownload;
const isGlobalTanom = (scope, param) => isGlobal(scope) && param === 'tavg';

const rankingsDao = new RankingsDao();

export function initRankingsTable() {
    updateRankingsTable(scope);
    $(window).scroll(prevNextDisplay);
}

/* Update Table */
/****************/
export async function updateRankingsTable(scope) {
    $('#rankings-table tbody').empty();
    $('#loader-overlay1').remove();
    $('#display').prepend(`
        <div id="loader-overlay1" class="loader-overlay">
            <img class="noaa-loader" alt="loader" src="/monitoring-content/lib/images/noaa-loader.gif">
        </div>
    `);

    // set cag.variables.basePeriod
    getBasePeriod(scope);

    const stats = await rankingsDao.getRankingsData(cag.constants, cag.variables);

    configDownload(cag.variables.url);

    fillPrevNext();

    if (isGlobal(scope)) {
        setGlobalRankingsTitle();
    } else {
        setUsRankingsTitle();
    }

    setTable(stats);
}

function failedLoad() {
    $('#loader-overlay1')
        .html('Data failed to load. Please try again.')
        .addClass('red-txt pad white-bg');
}

function setTable(stats) {
    const parameters  = cag.constants.parameters;
    const { parameter, begYear, endYear, year, month } = cag.variables;
    const tbody       = document.createDocumentFragment();
    const lowestText  = parameters[parameter].lowest;
    const highestText = parameters[parameter].highest;
    const units       = parameters[parameter].unitsAbbr;
    const units2      = parameters[parameter].units2Abbr;
    const precision   = parameters[parameter].precision;
    const ranksUrl    = isGlobal(scope) ? getGlobalRankingsUrl(false) : getUsRankingsUrl(false);
    const basePeriod  = getBasePeriod(scope);
    const thead       = getTableHeadRow(scope, parameter, basePeriod, lowestText, highestText, begYear, endYear);

    let valid = false;

    $('#designations, #designations > *, #insufficient-variability-record').addClass('hidden');
    $('#rankings-table').removeClass('warm-cool cool-warm wet-dry');
    document.querySelector('#rankings-table').classList.add(
        isPrecip(parameter) || isPalmer(parameter) ? 'wet-dry' : (parameter === 'hdd' ? 'cool-warm' : 'warm-cool')
    );

    $('.lowest-text').html(lowestText);
    $('.highest-text').html(highestText);
    $('.anom-base-period').html(basePeriod);
    $('.beg-year').html(begYear);
    $('.end-year').html(endYear);

    const periods = [];
    $.each(stats, function(tsNdx, tsStats) {
        const timescale = parseInt(tsNdx.replace('-month', ''));

        if (!Number.isInteger(timescale)) {
            return;
        }

        const periodTitle = getPeriodTitle(year, month, timescale);
        if (!periodTitle.hasChildNodes()) {
            return;
        }

        periods.push(timescale);
        let numYears = Util.numYears(cag.variables.begDate, cag.variables.endDate, month, timescale);
        let insufficientVariability = Util.is.insufficientVariability(tsStats.ties.length, numYears);

        if (tsStats.ties.length > 0) {
            $('#designations').removeClass('hidden');
            if (insufficientVariability) {
                $('#insufficient-variability-designation').removeClass('hidden');
                if (tsStats.lowRank == 1) {
                    $('#insufficient-variability-record').removeClass('hidden');
                }
            } else {
                $('#tie-designation').removeClass('hidden');
            }
        }

        const value            = tsStats[isGlobalTanom(scope, parameter) ? 'departure' : 'value'];
        const mean             = tsStats.mean;
        const percentile       = insufficientVariability && tsStats.lowRank == 1 ? 'insufficient-variability' : tsStats.percentile;
        const recordLowText    = getRecordText(tsStats.recordLows, ranksUrl, month);
        const recordHighText   = getRecordText(tsStats.recordHighs, ranksUrl, month);
        const lowestSinceText  = getSinceText(value, lowestText, tsStats.since.lowest, month, ranksUrl);
        const highestSinceText = getSinceText(value, highestText, tsStats.since.highest, month, ranksUrl);
        const tiesText         = getTiesText(tsStats.ties, ranksUrl);
        const rowspan          = (tiesText && tiesText.textContent.trim() !== '' ? 3 : 2);
        const conversion       = getConversion(scope, parameter, value, precision, false);
        const tsUrl            = ranksUrl.replace('rankings', 'time-series') +
            `/${timescale}/${month}/${begYear < year ? `${begYear}-` : ''}${year}` +
            '?base_prd=true&begbaseyear=' + basePeriod.replace('-', '&endbaseyear=', basePeriod);

        const missingValue = (value === null || isNaN(value));

        if (!missingValue) {
            valid = true;
        }

        const primaryRow = document.createElement('tr');
        const secondaryRow = document.createElement('tr');

        tbody.appendChild(primaryRow);
        tbody.appendChild(secondaryRow);

        primaryRow.className   = `period-row p${timescale} ${percentile}`;
        secondaryRow.className = `period-row p${timescale} ${percentile}`;

        const periodTh = document.createElement('th');
        primaryRow.appendChild(periodTh);
        periodTh.rowSpan = rowspan;
        periodTh.className = `period ${percentile}`;
        periodTh.headers = 'period';
        periodTh.scope = 'rowgroup';
        const periodA = document.createElement('a');
        periodTh.appendChild(periodA);
        periodA.title = `${timescale}-Month Time Series`;
        periodA.href = tsUrl;
        periodA.appendChild(periodTitle);
        const periodDiv = document.createElement('div');
        periodTh.appendChild(periodDiv);
        const periodText = document.createTextNode(`${timescale}-Month`);
        periodDiv.appendChild(periodText);
        periodDiv.className = 'month-period bold';

        const valueTd = document.createElement('td');
        primaryRow.appendChild(valueTd);
        valueTd.rowSpan = 2;
        valueTd.className = 'value';
        valueTd.headers = 'period';
        const valueText = document.createTextNode(missingValue ? '--' : value.toFixed(precision) + units);
        valueTd.appendChild(valueText);
        if (conversion) {
            const conversionDiv = document.createElement('div');
            valueTd.appendChild(conversionDiv);
            const conversionText = document.createTextNode(`(${conversion}${units2})`);
            conversionDiv.appendChild(conversionText);
        }

        // Mean & Departure
        if (scope !== 'global' || parameter !== 'tavg') {
            const meanConv = getConversion(scope, parameter, mean, precision, false);

            const meanTd = document.createElement('td');
            primaryRow.appendChild(meanTd);
            meanTd.rowSpan = 2;
            meanTd.className = 'mean';
            meanTd.headers = 'mean';
            const meanText = document.createTextNode(mean === null || isNaN(mean) ? '--' : mean.toFixed(precision) + units);
            meanTd.appendChild(meanText);
            if (meanConv && !isNaN(meanConv)) {
                const meanConvDiv = document.createElement('div');
                meanTd.appendChild(meanConvDiv);
                const meanConvText = document.createTextNode(`(${meanConv}${units2})`);
                meanConvDiv.appendChild(meanConvText);
            }

            const anomTd = document.createElement('td');
            primaryRow.appendChild(anomTd);
            anomTd.rowSpan = 2;
            anomTd.className = 'departure';
            anomTd.headers = 'departure';
            const anomText = document.createTextNode(missingValue ? '--' : tsStats['departure'].toFixed(precision) + units);
            anomTd.appendChild(anomText);

            if (!missingValue) {
                const anomConv = getConversion(scope, parameter, tsStats['departure'], precision, true);
                if (anomConv) {
                    const anomConvDiv = document.createElement('div');
                    anomTd.appendChild(anomConvDiv);
                    const anomConvText = document.createTextNode(`(${anomConv}${units2})`);
                    anomConvDiv.appendChild(anomConvText);
                }
            }
        }

        // Rank
        const loRankTd = document.createElement('td');
        primaryRow.appendChild(loRankTd);
        const hiRankTd = document.createElement('td');
        secondaryRow.appendChild(hiRankTd);

        loRankTd.headers = 'rank';

        loRankTd.className = 'rank nowrap';
        hiRankTd.className = 'rank nowrap';

        const des = setDesignation(tsStats.ties.length, insufficientVariability);

        const loRankText = missingValue
            ? '--'
            : addOrdinalSuffix(tsStats.lowRank) + ' ' + lowestText + des;
        loRankTd.innerHTML = loRankText;

        const hiRankText = missingValue
            ? '--'
            : addOrdinalSuffix(tsStats.highRank) + ' ' + highestText + des;
        hiRankTd.innerHTML = hiRankText;

        // Since
        const loSinceTd = document.createElement('td');
        primaryRow.appendChild(loSinceTd);
        const hiSinceTd = document.createElement('td');
        secondaryRow.appendChild(hiSinceTd);

        loSinceTd.headers = 'since';

        loSinceTd.className = 'since';
        hiSinceTd.className = 'since';

        loSinceTd.appendChild(lowestSinceText);
        hiSinceTd.appendChild(highestSinceText);

        // Record
        const loRecordTd = document.createElement('td');
        primaryRow.appendChild(loRecordTd);
        const hiRecordTd = document.createElement('td');
        secondaryRow.appendChild(hiRecordTd);

        loRecordTd.headers = 'record';

        loRecordTd.className = 'record';
        hiRecordTd.className = 'record';

        loRecordTd.appendChild(recordLowText);
        hiRecordTd.appendChild(recordHighText);

        if (tiesText && tiesText.textContent.trim() !== '') {
            const tiesRow = document.createElement('tr');
            tiesRow.className = `period-row p${timescale} ${percentile}`;

            const tiesTd = document.createElement('td');
            tiesTd.className = 'ties italic';
            //tiesTd.colspan = 6;
            tiesTd.setAttribute("colspan", "6");

            tiesTd.appendChild(tiesText);
            tiesRow.appendChild(tiesTd);

            tbody.appendChild(tiesRow);
        }
    });

    if (valid) {
        $('#rankings-table thead').html(thead);
        $('#rankings-table tbody').html(tbody);
        fillPeriodSelection(periods);
        prevNextDisplay();
        $('#loader-overlay1').remove();
    } else {
        console.warn('Missing data');
        failedLoad();
    }
}

function getBasePeriod(scope) {
    if (isGlobal(scope)) {
        const { parameter, region } = cag.variables;

        const basePeriodKey = parameter === 'pcp' ? 'pcp'
            : region === 'coords' ? 'coords'
            : ['globe', 'nhem', 'shem'].includes(region) ? 'globe'
            : 'default';

        const basePeriodMapping = {
            pcp:     basePeriods.global.pcp,
            coords:  basePeriods.global.gridded,
            globe:   basePeriods.global.globe,
            default: basePeriods.global.region
        };

        cag.variables.basePeriod = Object.values(basePeriodMapping[basePeriodKey]).join('-');
        return cag.variables.basePeriod;
    }

    const locationId = String(cag.variables.locationId);

    const akMatch = (
        (scope === 'statewide' && locationId == 50) ||
        (scope === 'divisional' && String(locationId).slice(0, -2) == 50) ||
        (scope === 'county' && locationId.startsWith('AK'))
    );

    const hiMatch = (
        (scope === 'statewide' && locationId == 51) ||
        (scope === 'divisional' && String(locationId).slice(0, -2) == 51) ||
        (scope === 'county' && locationId.startsWith('HI'))
    );

    if (akMatch) {
        cag.variables.basePeriod = Object.values(basePeriods.national.alaska).join('-');
    } else if (hiMatch) {
        cag.variables.basePeriod = Object.values(basePeriods.national.hawaii).join('-');
    } else if (scope === 'city') {
        cag.variables.basePeriod = Object.values(basePeriods.national.city).join('-');
    } else {
        cag.variables.basePeriod = Object.values(basePeriods.national.conus).join('-');
    }

    return cag.variables.basePeriod;
}

function getTableHeadRow(scope, parameter, basePeriod, lowestText, highestText, begYear, endYear) {
    const headRow  = document.createElement('tr');

    const periodTh = document.createElement('th');
    const anomTh   = document.createElement('th');
    const rankTh   = document.createElement('th');
    const sinceTh  = document.createElement('th');
    const recordTh = document.createElement('th');

    const periodText = document.createTextNode('Period');
    const anomText   = document.createTextNode('Departure from Average');
    const rankText   = document.createTextNode('Rank');
    const recordText = document.createTextNode('Record');

    const highestLowestDiv  = document.createElement('div');
    const highestLowestText = document.createTextNode(`${lowestText}/${highestText}`);
    const sinceText         = document.createTextNode('Since');

    const basePrdDiv  = document.createElement('div');
    const basePrdText = document.createTextNode(basePeriod);

    const porDiv  = document.createElement('div');
    const porText = document.createTextNode(`(${begYear}-${endYear})`);

    periodTh.id = 'period';
    anomTh.id   = 'departure';
    rankTh.id   = 'rank';
    sinceTh.id  = 'since';
    recordTh.id = 'record';

    anomTh.className   = 'departure';
    sinceTh.className  = 'since';
    recordTh.className = 'record';

    periodTh.appendChild(periodText);
    anomTh.appendChild(anomText);

    rankTh.appendChild(rankText);
    rankTh.appendChild(porDiv);
    porDiv.appendChild(porText);
    porDiv.className = 'bold';

    recordTh.appendChild(recordText);

    highestLowestDiv.appendChild(highestLowestText);
    sinceTh.appendChild(highestLowestDiv);
    sinceTh.appendChild(sinceText);
    highestLowestDiv.className = 'bold';

    basePrdDiv.className = 'bold';

    headRow.appendChild(periodTh);
    if (isGlobalTanom(scope, parameter)) {
        anomTh.appendChild(basePrdDiv);

        basePrdText.textContent = `(${basePrdText.textContent})`;
        basePrdDiv.appendChild(basePrdText);
    } else {
        const valueTh = document.createElement('th');
        const meanTh  = document.createElement('th');

        valueTh.id = 'value';
        meanTh.id  = 'mean';

        meanTh.className = 'mean';

        const valueText = document.createTextNode('Value');
        const meanText = document.createTextNode('Average');

        valueTh.appendChild(valueText);

        meanTh.appendChild(basePrdDiv);
        meanTh.appendChild(meanText);

        headRow.appendChild(valueTh);
        headRow.appendChild(meanTh);

        basePrdDiv.appendChild(basePrdText);
    }

    headRow.appendChild(anomTh);
    headRow.appendChild(rankTh);
    headRow.appendChild(sinceTh);
    headRow.appendChild(recordTh);

    return headRow;
}

function getPeriodTitle(year, month, timescale) {
    const monthName   = monthNames[month - 1];
    const periodTitle = document.createDocumentFragment();

    if (timescale === 1) {
        const monthNameText = document.createTextNode(`${monthName} ${year}`);
        periodTitle.appendChild(monthNameText);
    } else {
        let begDateObj = new Date(year, month - (timescale - 1), 0);
        const begTimeMonth = begDateObj.getMonth() + 1;
        const begTimeYear = begDateObj.getFullYear();
        const begTimeYyyyMm = parseInt(begTimeYear + String(begTimeMonth).padStart(2, '0'));

        if (begTimeYyyyMm < cag.variables.begDate) {
            return periodTitle;
        }

        const begMonthText = document.createTextNode(monthNames[begTimeMonth - 1].substring(0, 3));
        periodTitle.appendChild(begMonthText);

        if (begTimeYear < year) {
            const begYearText = document.createTextNode(' ' + begTimeYear);
            periodTitle.appendChild(begYearText);
        }

        const dashWbr = document.createElement('wbr');
        periodTitle.appendChild(document.createTextNode('–'));
        periodTitle.appendChild(dashWbr);

        const endMonthYearText = document.createTextNode(monthName.substring(0, 3) + ' ' + year);
        periodTitle.appendChild(endMonthYearText);
    }

    return periodTitle;
}

function getRecordText(records, ranksUrl, month) {
    let recordText = document.createTextNode('--');

    if (Array.isArray(records) && records.length > 0) {
        if (records.length > 15) {
            const numerousText = document.createElement('em');
            numerousText.appendChild(document.createTextNode(`${records.length - 1} ties`));
            recordText = numerousText;
        } else {
            const recordFragment = document.createDocumentFragment();
            $.each(records, function(ndx, recordYear) {
                if (ndx > 0) {
                    recordFragment.appendChild(document.createTextNode(', '));
                }
                if (recordYear === year) {
                    recordFragment.appendChild(document.createTextNode(recordYear));
                } else {
                    const recordA = document.createElement('a');
                    recordA.title = recordYear + ' Rankings';
                    recordA.href = `${ranksUrl}/${recordYear}${String(month).padStart(2, '0')}`;
                    const recordAText = document.createTextNode(recordYear);
                    recordA.appendChild(recordAText);
                    recordFragment.appendChild(recordA);
                }
            });
            recordText = recordFragment;
        }
    }

    return recordText;
}

function getSinceText(value, highestLowest, sinceYear, month, ranksUrl) {
    if (value === null || isNaN(value)) {
        return document.createTextNode('--');
    } else if (sinceYear && sinceYear != year) {
        const sinceDiv = document.createElement('div');

        const sinceTextDiv = document.createElement('div');
        const sinceText = document.createTextNode(highestLowest + ' ' + (sinceYear && sinceYear != year ? 'since:' : 'to Date'));
        sinceTextDiv.appendChild(sinceText);
        sinceDiv.appendChild(sinceTextDiv);

        const sinceADiv = document.createElement('div');
        const sinceA = document.createElement('a');
        sinceA.title = sinceYear + ' Rankings';
        sinceA.href = `${ranksUrl}/${sinceYear}${String(month).padStart(2, '0')}`;
        const sinceAText = document.createTextNode(sinceYear);
        sinceA.appendChild(sinceAText);
        sinceADiv.appendChild(sinceA);
        sinceDiv.appendChild(sinceADiv);

        return sinceDiv;
    } else {
        return document.createTextNode(highestLowest + ' to Date');
    }
}

function getTiesText(ties, ranksUrl) {
    if (Array.isArray(ties)) {
        if (ties.length > 15) {
            const numerousEm = document.createElement('em');
            numerousEm.textContent = `${ties.length} ties`;
            return numerousEm;
        } else if (ties.length > 0) {
            const tiesFragment = document.createDocumentFragment();

            const tiesTextNode = document.createTextNode('Ties: ');
            tiesFragment.appendChild(tiesTextNode);
            $.each(ties, function (ndx, tieYear) {
                if (ndx > 0) {
                    tiesFragment.appendChild(document.createTextNode(', '));
                }

                const tiesA = document.createElement('a');
                tiesA.title = tieYear + ' Rankings';
                tiesA.href = `${ranksUrl}/${tieYear}${String(month).padStart(2, '0')}`;
                tiesA.textContent = tieYear;

                tiesFragment.appendChild(tiesA);
            });

            return tiesFragment;
        }
    }

    return document.createTextNode('');
}


function getConversion(scope, parameter, value, precision, anomaly) {
    if (value === null || isNaN(value)) {
        return '';
    }

    let conv = '';

    // remove non-float characters
    value = String(value).replace(/[^-.\d]/g, '');

    if (isGlobal(scope)) {
        if (parameter === 'tavg') {
            // °C to °F anomaly
            conv = (value * 1.8);
        } else if (parameter === 'pcp') {
            // mm to inches
            conv = (value / 25.4);
        }
    } else {
        if ((isTemp(parameter) && anomaly)) {
            // °F to °C anomaly
            conv = (value / 1.8);
        } else if (isTemp(parameter) && !anomaly) {
            // °F to °C
            conv = ((value - 32) / 1.8);
        } else if (parameter === 'pcp') {
            // inches to mm
            conv = (value * 25.4);
        } else {
            return '';
        }
    }

    return Util.format.number(conv, precision);
}

function addOrdinalSuffix(num) {
    if (num % 100 >= 11 && num % 100 <= 13) {
        return `${num}th`;
    } else {
        switch (num % 10) {
            case 1:
                return `${num}st`;
            case 2:
                return `${num}nd`;
            case 3:
                return `${num}rd`;
            default:
                return `${num}th`;
        }
    }
}
/****************/
/* Update Table */

/* Prev/Next */
/*************/
function fillPrevNext() {
    const { year, month } = cag.variables;
    const pnUrl = isGlobal(scope) ? getGlobalRankingsUrl(false) : getUsRankingsUrl(false);

    const prevDateObj = new Date(year, month-1, 0);
    const nextDateObj = new Date(year, parseInt(month) + 1, 0);

    const prevYear  = prevDateObj.getFullYear();
    const prevMonth = parseInt(prevDateObj.getMonth()) + 1;
    const prevDate  = prevYear + ('0' + prevMonth).slice(-2);

    const nextYear  = nextDateObj.getFullYear();
    const nextMonth = parseInt(nextDateObj.getMonth()) + 1;
    const nextDate  = nextYear + ('0' + nextMonth).slice(-2);

    const prevDateStr = monthNames[prevDateObj.getMonth()] + ' ' + prevDateObj.getFullYear();
    const nextDateStr = monthNames[nextDateObj.getMonth()] + ' ' + nextDateObj.getFullYear();

    const prevContainer = document.getElementById('prev');
    const nextContainer = document.getElementById('next');

    if (prevDate >= cag.variables.begDate) {
        const prevTitle = prevDateStr + ' Rankings';
        const prevHref = `${pnUrl}/${prevDate}`;
        const prevIconClass = 'fas fa-chevron-circle-left';
        const prevLink = createArrowLink(prevTitle, prevHref, prevYear, prevMonth, prevIconClass);

        prevContainer.innerHTML = '';
        prevContainer.appendChild(prevLink);
        prevContainer.style.display = 'block';

        prevLink.addEventListener('click', prevNextClick);
    } else {
        prevContainer.style.display = 'none';
    }

    if (nextDate <= cag.variables.endDate) {
        const nextTitle = nextDateStr + ' Rankings';
        const nextHref = `${pnUrl}/${nextDate}`;
        const nextIconClass = 'fas fa-chevron-circle-right';
        const nextLink = createArrowLink(nextTitle, nextHref, nextYear, nextMonth, nextIconClass);

        nextContainer.innerHTML = '';
        nextContainer.appendChild(nextLink);
        nextContainer.style.display = 'block';

        nextLink.addEventListener('click', prevNextClick);
    } else {
        nextContainer.style.display = 'none';
    }
}

function createArrowLink(title, href, year, month, iconClass) {
    const link = document.createElement('a');
    link.title = title;
    link.href = href;
    link.setAttribute('data-toggle', 'tooltip');
    link.setAttribute('data-year', year);
    link.setAttribute('data-month', month);

    const icon = document.createElement('i');
    icon.className = iconClass;
    icon.setAttribute('aria-hidden', 'true');

    link.appendChild(icon);
    return link;
}

function prevNextClick(event) {
    event.preventDefault();

    const year = this.dataset.year;
    const month = this.dataset.month;

    const yearSelect = document.getElementById('year');
    const monthSelect = document.getElementById('month');

    if (yearSelect) {
        yearSelect.value = year;
        yearSelect.dispatchEvent(new Event('change')); // Trigger change event
    }

    if (monthSelect) {
        monthSelect.value = month;
    }

    cag.variables.formChanged = true;

    if (isGlobal(scope)) {
        updateGlobalRankingsData();
    } else {
        updateUsRankingsData();
    }

    return false;
}

function prevNextDisplay() {
    const rankingsTable = document.querySelector('#rankings-table tbody');
    if (!rankingsTable) return;

    const elementRect = rankingsTable.getBoundingClientRect();
    const elementTop = elementRect.top + window.scrollY;
    const scrollTop = window.scrollY;
    const windowHeight = window.innerHeight;

    const arrowNavs = document.querySelectorAll('.arrowNav');
    if (elementTop + 60 <= scrollTop + windowHeight) {
        arrowNavs.forEach(el => el.style.display = 'block');
    } else {
        arrowNavs.forEach(el => el.style.display = 'none');
    }
}
/*************/
/* Prev/Next */

/* Period Selection */
/********************/
function fillPeriodSelection(periods) {
    const periodView = document.createDocumentFragment();

    if (periods.length > 1) {
        const viewPeriodDiv = document.createElement('div');
        const viewPeriodText = document.createTextNode('View Period (Months):');
        viewPeriodDiv.appendChild(viewPeriodText);
        periodView.appendChild(viewPeriodDiv);

        const periodSelectDiv = document.createElement('div');
        periodSelectDiv.id = 'period-select';
        periodView.appendChild(periodSelectDiv);

        const viewAllDiv = document.createElement('div');
        viewAllDiv.id = 'view-all';
        const viewAllLink = document.createElement('a');
        viewAllLink.href = '#all';
        viewAllLink.setAttribute('data-period', 'all');
        viewAllLink.title = 'View all periods';
        const viewAllText = document.createTextNode('All');
        viewAllLink.appendChild(viewAllText);
        viewAllDiv.appendChild(viewAllLink);
        periodSelectDiv.appendChild(viewAllDiv);

        periods.forEach(function(period) {
            const viewPeriodDiv = document.createElement('div');
            viewPeriodDiv.id = 'view-' + period;
            const periodLink = document.createElement('a');
            periodLink.href = '#' + period;
            periodLink.setAttribute('data-period', period);
            periodLink.title = `View ${period}-Month Period`;
            const periodText = document.createTextNode(period);
            periodLink.appendChild(periodText);
            viewPeriodDiv.appendChild(periodLink);
            periodSelectDiv.appendChild(viewPeriodDiv);
        });
    }

    const periodViewContainer = document.getElementById('period-view');
    periodViewContainer.innerHTML = '';
    periodViewContainer.appendChild(periodView);

    viewPeriod(periods, getPeriodFromHash());

    $('#period-select a').click(function() {
        periodViewChange(periods, $(this).data('period'));
        return false;
    });
}

function getPeriodFromHash() {
    const hash = window.location.hash.slice(1);
    return /^\d+$/.test(hash) ? parseInt(hash, 10) : 'all';
}

function periodViewChange(periods, period) {
    period = ($.inArray(period, periods) > -1 ? period : 'all');

    window.history.replaceState(
        {},
        document.title,
        window.location.href.slice(0, -window.location.hash.length) +
        (period === 'all' ? '' : '#' + period)
    );

    viewPeriod(periods, period);

    return false;
}

function viewPeriod(periods, selectedPeriod) {
    $('#period-select a').removeClass('selected');

    if (periods.includes(selectedPeriod)) {
        $(`#period-select #view-${selectedPeriod} a`).addClass('selected');
        $('.period-row').hide();
        $('.p' + selectedPeriod).show();
    } else {
        $('#period-select #view-all a').addClass('selected');
        $('.period-row').show();
    }
}
/********************/
/* Period Selection */
