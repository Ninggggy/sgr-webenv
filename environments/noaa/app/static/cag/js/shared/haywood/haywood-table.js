import { cag, base, scope, basePeriods, monthNames } from "../../globals.js";
import { valuesTableSorter } from "../tablesorter.js";
import Util from "../../utils/util.js";

export function createHaywoodDataTable(title, subtitle, series) {
    const parameters = cag.constants.parameters;
    const { parameter, month } = cag.variables;
    const paramMeta = parameters[parameter];
    const globalTavgAnoms = (scope ===  'global' && parameter === 'tavg');

    const table = document.createElement('table');
    table.id = 'values-table';
    table.className = 'bordered shading';

    const caption = document.createElement('caption');
    const titleDiv = document.createElement('div');
    titleDiv.id = 'values-table-title';
    titleDiv.className = 'bold';
    titleDiv.textContent = title;
    caption.appendChild(titleDiv);

    const subtitleDiv = document.createElement('div');
    subtitleDiv.id = 'values-table-subtitle';
    if (globalTavgAnoms) {
        const regionKey = cag.variables.region === 'coords' ? 'gridded'
            : ['globe', 'nhem', 'shem'].includes(cag.variables.region) ? 'globe'
                : 'region';

        const basePeriod = Object.values(basePeriods.global[regionKey]).join('-');

        subtitle += ` (${basePeriod} average)`;
    }
    subtitleDiv.textContent = subtitle;
    caption.appendChild(subtitleDiv);

    table.appendChild(caption);

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const periodHeader = document.createElement('th');
    periodHeader.textContent = (month == 12 ? 'Year-to-Date' : 'Period');
    headerRow.appendChild(periodHeader);

    const parameterHeader = document.createElement('th');
    parameterHeader.textContent = paramMeta.title + (globalTavgAnoms ? ' Departure from Average' : '');
    headerRow.appendChild(parameterHeader);

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    series.forEach(function(seriesAttr, i) {
        if (seriesAttr.text === 'Average') {
            return;
        }

        var seriesYear = seriesAttr.text;
        var lastYear = (i == series.length - 1);

        var lastMonthNdx;
        if (lastYear) {
            seriesAttr.values.forEach(function(valueAttr, ndx) {
                if (!valueAttr[1]) {
                    return false;
                }
                lastMonthNdx = ndx;
            });
        }

        seriesAttr.values.forEach(function(valueAttr, ndx) {
            if (lastYear && valueAttr[1] === null) {
                return false;
            }

            const monthName = valueAttr[0];
            const value     = parseFloat(valueAttr[1]);
            const nmon      = monthNames.indexOf(monthName) + 1;
            const thisYear  = parseInt(month < 12 && nmon > month ? seriesYear - 1 : seriesYear);
            const date      = parseInt(thisYear + String(nmon).padStart(2, "0"));

            let begNmon = (nmon - ndx);
            let begYear = thisYear;
            let begDate = null;
            if (ndx > 0) {
                if (begNmon < 1) {
                    begNmon += 12;
                    begYear -= 1;
                }

                const begMonthName = monthNames[begNmon - 1];

                begDate = document.createElement('span');
                const monthAbbrText = document.createTextNode(begMonthName.substring(0, 3));
                begDate.appendChild(monthAbbrText);

                const longMonthSpan = document.createElement('span');
                longMonthSpan.className = 'monthlong';
                const longMonthText = document.createTextNode(begMonthName.substring(3));
                longMonthSpan.appendChild(longMonthText);

                begDate.appendChild(longMonthSpan);

                if (begYear < thisYear) {
                    const yearSpan = document.createElement('span');
                    yearSpan.textContent = ' ' + begYear;
                    begDate.appendChild(yearSpan);
                }

                begDate.appendChild(document.createTextNode('-'));
            }

            const tr = document.createElement('tr');
            tr.className = (!lastYear && nmon == month) || (lastYear && ndx == lastMonthNdx) ?
                'endMonth' : 'nonEndMonth';

            const periodTd = document.createElement('td');
            periodTd.className = 'left';
            periodTd.dataset.sortval = date;

            const rankingsLink = document.createElement('a');
            rankingsLink.href = scope === 'global'
                ? getGlobalHaywoodRankingsUrl(date, ndx + 1)
                : getUsHaywoodRankingsUrl(date, ndx + 1);

            if (begDate) {
                rankingsLink.appendChild(begDate);
            }

            const monthNameText = document.createTextNode(monthName.substring(0, 3));
            rankingsLink.appendChild(monthNameText);

            const longMonthSpan = document.createElement('span');
            longMonthSpan.className = 'monthlong';
            const longMonthText = document.createTextNode(monthName.substring(3));
            longMonthSpan.appendChild(longMonthText);

            rankingsLink.appendChild(longMonthSpan);

            const yearText = document.createTextNode(' ' + thisYear);
            rankingsLink.appendChild(yearText);

            periodTd.appendChild(rankingsLink);
            tr.appendChild(periodTd);

            const valueTd = document.createElement('td');
            if (value) {
                const precision = Util.getPrecision(cag.variables?.locationId ?? '', parameter);
                let dispValue = Util.format.number(value, precision);
                valueTd.dataset.sortval = value;
                valueTd.textContent = dispValue + paramMeta.unitsAbbr.replace(/^in$/, '"');
            } else {
                valueTd.dataset.sortval = "";
                valueTd.textContent = '--';
            }
            tr.appendChild(valueTd);
            tbody.appendChild(tr);
        });
    });

    table.appendChild(tbody);

    $('#data-table').html(table);
    valuesTableSorter('#values-table', cag.constants.section);

    $('.nonEndMonth').hide();
    displayPeriod('showEnd');
    $('.display-period').click(function(){ displayPeriod($(this).attr('id')); return false; });
}

function getGlobalHaywoodRankingsUrl(prdDate, prd) {
    const { region, lat, lon, parameter, surface } = cag.variables;
    const coordsOrRegion = region === 'coords'
        ? (parseFloat(lat) + ',' + parseFloat(lon))
        : encodeURIComponent(region);
    return `${base}/${scope}/rankings/${coordsOrRegion}/${parameter}/${surface}/${prdDate}#${prd}`;
}

function getUsHaywoodRankingsUrl(prdDate, prd){
    const { locationId, parameter } = cag.variables;
    return `${base}/${scope}/rankings/${locationId}/${parameter}/${prdDate}#${prd}`;
}

function displayPeriod(prd) {
    let selector = '#values-table tbody tr';

    $('.display-period').removeClass('selected');
    $('#' + prd).addClass('selected');

    if (prd === 'showAll') {
        $('.nonEndMonth').show();
    } else {
        $('.nonEndMonth').hide();
        selector += ':not(.nonEndMonth)';
    }

    $(selector).removeClass('even odd').
        each(function(ndx, row) {
            $(this).addClass(ndx%2 ? 'even' : 'odd');
        });
}