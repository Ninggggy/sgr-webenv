import zingchart from '../../../assets/zingchart-2.9.16-1/es6.js';
import { loadZingChartConfig } from '../../utils/load-zingchart-config.js';
import { HaywoodDao } from '../dao/HaywoodDao.js';
import { createHaywoodDataTable } from './haywood-table.js';
import { getUsTitle, getGlobalTitle } from './title-util.js';
import { getSeries, getMonthLabels } from './haywood-util.js';
import Util from '../../utils/util.js';

const { configDownload } = Util.config;
const { dryToWet: isDryToWet, degreeDay: isDegreeDay } = Util.parameter.is;
const paramMetaVal = Util.parameter.metaVal;
const isGlobal = Util.scope.is.global;

async function plotHaywood(cag) {
    zingchart.exec('chartCanvas', 'destroy');
    $('#chartCanvas').empty();
    $('#download-display').hide();
    $('#data-table').html(`
        <div class="center pad">
            <img alt="loader" src="/monitoring-content/lib/images/noaa-loader.gif">
        </div>
    `);
    const { scope, colors } = cag.constants;
    const { parameter, month } = cag.variables;
    const prdEndMonth  = parseInt(month, 10);

    configDownload(cag.variables.url);

    const isPrd = prdEndMonth < 12;
    const terms = isPrd
        ? { all: 'Periods', end: 'Period' }
        : { all: 'Months',  end: 'Month' };

    $('#showAll').text(`All ${terms.all}`);
    $('#showEnd').text(`End ${terms.end}`);

    let hi5Colors, lo5Colors, currentColor, palette;
    if (isDryToWet(parameter)) {
        ({ hi: hi5Colors, lo: lo5Colors, current: currentColor } = colors.wetDry);
        palette = {
            highest: hi5Colors[0],
            lowest: lo5Colors[4],
            current: currentColor
        };
    } else {
        ({ hi: hi5Colors, lo: lo5Colors, current: currentColor } = colors.hotCold);

        if (parameter === "hdd") {
            // swap & reverse hi/lo
            [hi5Colors, lo5Colors] = [lo5Colors.slice().reverse(), hi5Colors.slice().reverse()];

            palette = {
                highest: hi5Colors[2],
                lowest: lo5Colors[4],
                current: currentColor
            };
        } else {
            palette = {
                highest: hi5Colors[0],
                lowest: lo5Colors[2],
                current: currentColor
            };
        }
    }

    $('.highest').text(paramMetaVal('highest').toLowerCase());
    $('.lowest').text(paramMetaVal('lowest').toLowerCase());
    $(".highest-phrase").css("color", palette.highest);
    $(".lowest-phrase").css("color", palette.lowest);
    $(".current-phrase").css("color", palette.current);

    const haywoodDao = new HaywoodDao();
    const [template, data] = await Promise.all([
        loadZingChartConfig('haywood'),
        haywoodDao.getHaywoodData(cag.constants, cag.variables)
    ]);

    if (!data || Object.keys(data).length === 0) {
        zingchart.exec('chartCanvas', 'destroy');
        $('#chartCanvas').html('<div class="red-txt pad">Data failed to load. Please try again.</div>');
        $('#data-table').html('');
        console.error('Failed to load Haywood data.');
        return false;
    }

    const precision = Util.getPrecision(cag.variables?.locationId ?? '', parameter);
    const units = (paramMetaVal('unitsAbbr') ?? '').replace(/^in$/, '"');

    let title;
    if (isGlobal(scope)) {
        const { globalRegions, surfaces } = cag.constants;
        const { region, surface, lat, lon } = cag.variables;
        title = getGlobalTitle(globalRegions, surfaces, region, lat, lon, surface);
    } else {
        const { usStates, locations } = cag.constants;
        const location = cag.variables.locationId;
        title = getUsTitle(scope, usStates, locations, location);
    }

    const formatMonth = m =>
        new Date(2000, m - 1, 10).toLocaleString('en-US', { month: 'long' });

    const startMonth = formatMonth((prdEndMonth % 12) + 1);
    const endMonth   = formatMonth(prdEndMonth);

    const monthRange = `${startMonth}-${endMonth}`;

    const baseSubtitle = isPrd ? monthRange : 'Year-to-Date';

    const anomalies = (isGlobal(scope) && parameter === 'tavg') ? ' Departures' : '';

    const subtitle = `${baseSubtitle} ${paramMetaVal('title')}${anomalies}`;

    const series = await getSeries(
        scope,
        data,
        parameter,
        precision,
        units,
        prdEndMonth,
        hi5Colors,
        lo5Colors,
        currentColor
    );

    createHaywoodDataTable(title, subtitle, series);
    $('#download-display').show();

    const { lbls, ls } = await getMonthLabels(prdEndMonth);

    // max of column 12 (last month in series)
    const maxCount = Math.max(
    ...Object.values(data) // get all year objects
        .filter(year => typeof year === "object") // skip non-objects if any
        .map(year => year["189512"] ?? year["12"]) // grab 12th value
        .filter(v => v !== null && v !== undefined && !isNaN(v))
    );

    // flatten + filter numeric + non-missing
    const nonMissing = Object.values(data) // years
        .flatMap(year => Object.values(year)) // all monthly values
        .filter(value => value !== null && value !== undefined && value !== "" && !isNaN(value));

    // get minimum numeric value
    const minVal = Math.min(...nonMissing.map(Number));

    // Deep clone to avoid mutating the base config
    const config = structuredClone(template);

    config.type = "line";

    config.title = config.title || {};
    config.title.text = title;

    config.subtitle = config.subtitle || {};
    config.subtitle.text = subtitle;

    config.scaleX = config.scaleX || {};
    config.scaleX.maxItems = 12;
    config.scaleX.guide = { visible: false };
    config.scaleX.zooming = false;
    config.scaleX.mediaRules = [
        {
            "minWidth": 371,
            "labels": lbls
        },
        {
            "maxWidth": 370,
            "labels": ls
        }
    ];

    config.scaleY             = config.scaleY || {};
    config.scaleY.label       = config.scaleY.label || {};
    config.scaleY.label.text  = isDegreeDay(parameter) ? (paramMetaVal('unitsText') ?? "") : "";
    config.scaleY.format      = 'cagScaleYFormat()';//from '../zingchartFormatter.js';//`%v${units}`;
    config.scaleY.minValue    = parseFloat(minVal);

    config.scaleY2            = config.scaleY2 || {};
    config.scaleY2.label      = config.scaleY2.label || {};
    config.scaleY2.label.text = isDegreeDay(parameter) ? (paramMetaVal('units2Text') ?? "") : "";
    config.scaleY2.format     = 'cagScaleY2Format()';//from '../zingchartFormatter.js';
    config.scaleY2.minValue   = parseFloat(minVal);
    config.scaleY2.zooming    = true;

    config.plot = {
        highlight: true,
        tooltip: {
            text: `%k %t: %v${units}`,
            fontColor: "#ffffff",
            borderRadius: "5px",
            callout: true
        },
        legendMarker: { showLine: true }
    };

    config.legend = config.legend || {};
    config.legend.adjustLayout = true;
    config.legend.marginTop = 62;
    config.legend.layout = "x1";
    config.legend.toggleAction = "remove";

    delete config.crosshairX;
    delete config.zoom;
    delete config.scrollX;

    config.series = series;

    zingchart.render({
        id: 'chartCanvas',
        data: config,
        height: 500,
        width: '100%',
    });
}

export { plotHaywood };
