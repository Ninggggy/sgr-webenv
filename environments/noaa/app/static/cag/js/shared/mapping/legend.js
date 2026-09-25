import {
    base,
    scope,
    section,
} from '../../globals.js'
import Util from '../../utils/util.js';

const locWithContext = Util.location.withContext(scope, section);
const {
    alaska: isAlaska,
    hawaii: isHawaii,
} = locWithContext.is;

const {
    temp: isTemp,
    coldToHot: isColdToHot,
    degreeDay: isDegreeDay,
    dryToWet: isDryToWet,
    palmer: isPalmer
} = Util.parameter.is;

let ddScales;

async function getDdScales() {
    if (!ddScales) {
        const res = await fetch(`${base}/api/config/map/dd-scales.json`);
        if (!res.ok) throw new Error('Degree Day scales failed to load');
        ddScales = await res.json();
    }
    return ddScales;
}

let legendConfig;

async function getLegendConfig() {
    if (!legendConfig) {
        const res = await fetch(`${base}/api/config/map/legend.json`);
        if (!res.ok) throw new Error('Legend config file failed to load');
        legendConfig = await res.json();
    }
    return legendConfig;
}

let climateRegionStates;

async function getClimateRegionStates() {
    if (!climateRegionStates) {
        const res = await fetch(`${base}/api/config/map/us-climate-regions.json`);
        if (!res.ok) throw new Error('Climate Regions failed to load');
        const climateRegions = await res.json();
        climateRegionStates = Object.entries(climateRegions).reduce((acc, [id, data]) => {
            acc[Number(id)] = data.stateIds;
            return acc;
        }, {});
    }
    return climateRegionStates;
}

const handlers = {
    value_temp: handleValueTemp,
    value_pcp: handleValuePcp,
    value_cdd: handleValueDegreeDays,
    value_hdd: handleValueDegreeDays,
    value_palmer: handleValuePalmer,
    anomaly_temp: handleAnomalyTemp,
    anomaly_pcp: handleAnomalyPcp,
    anomaly_cdd: handleAnomalyDegreeDays,
    anomaly_hdd: handleAnomalyDegreeDays,
    anomaly_palmer: handleAnomalyPalmer,
    pctavg_pcp: handlePctAvg
};

function getLegend(type, param, config) {
    return config[type][param];
}

/**
 * Finds the highest threshold that the current timescale has met/surpassed
 */
const getValueBins = (ts, bins) => {
    const threshold = Object.keys(bins)
        .map(Number)
        .sort((a, b) => b - a)
        .find(t => Number(ts) >= t);

    return threshold ? bins[threshold] : [];
};

export async function loadLegendConfig(returnType, parameter, locationId, timescale, month, numYears) {
    let bins = [];
    let colors = [];

    const config = await getLegendConfig();

    // -----------------------------
    // Rank
    // -----------------------------

    if (returnType === 'rank') {
        bins = Util.ranks.thresholds(numYears);

        if (isColdToHot(parameter) || parameter === 'cdd') {
            colors = config.rank.coldToHot;
        }
        else if (parameter === 'hdd') {
            colors = [...config.rank.coldToHot].reverse();
        }
        else if (isDryToWet(parameter)) {
            colors = config.rank.dryToWet;
        }

        return { bins, colors };
    }

    // --------------------------------------------
    // Value, Percent of Average, Anomaly, and Mean
    // --------------------------------------------

    const type = returnType === 'mean' ? 'value' : returnType;
    const param = isTemp(parameter)
        ? 'temp'
        : isPalmer(parameter)
            ? 'palmer'
            : parameter;
    const key = `${type}_${param}`;
    const handler = handlers[key];

    if (!handler) return { bins: [], colors: [] };

    return await handler({
        parameter,
        locationId,
        timescale,
        month,
        config,
        scope
    });
}

function getScopeFamily(scope) {
     return scope === 'global' ? 'global'
        : 'us';
}

function getUsEntity(locationId) {
     return isAlaska(locationId) ? 'alaska'
        : isHawaii(locationId) ? 'hawaii'
        : 'conus';
}

function handleValueTemp({locationId, config}) {
    const cfg = getLegend('value', 'temp', config);
    const entity = getUsEntity(locationId);

    return {
        bins: cfg.bins.us[entity],
        colors: cfg.colors
    };
}

function handleValuePcp({timescale, config, scope}) {
    const cfg = getLegend('value', 'pcp', config);

    const family = getScopeFamily(scope);

    return {
        bins: getValueBins(timescale, cfg.bins[family]),
        colors: cfg.colors
    };
}

async function handleValueDegreeDays({
    parameter,
    locationId,
    timescale,
    month,
    config
}) {
    const bins = await getDegreeDayBins(parameter, locationId, timescale, month);

    const cfg = getLegend('value', parameter, config);

    return { bins, colors: cfg.colors };
}

function handleValuePalmer({config}) {
    const cfg = getLegend('value', 'palmer', config);

    return {
        bins: cfg.bins.us,
        colors: cfg.colors
    };
}

function handleAnomalyTemp({locationId, timescale, config, scope}) {
    const cfg = getLegend('anomaly', 'temp', config);

    if (scope === 'global') {
        return {
            colors: cfg.colors.global,
            bins: cfg.bins.global
        };
    }

    const entity = getUsEntity(locationId);

    return {
        colors: cfg.colors.us,
        bins: getValueBins(
            timescale,
            cfg.bins.us[entity]
        )
    };
}

function handleAnomalyPcp({timescale, config, scope}) {
    const cfg = getLegend('anomaly', 'pcp', config);

    const family = getScopeFamily(scope);

    return {
        bins: getValueBins(timescale, cfg.bins[family]),
        colors: cfg.colors
    };
}

function handleAnomalyDegreeDays({parameter, config}) {
    const cfg = getLegend('anomaly', parameter, config);

    return {
        bins: cfg.bins.us,
        colors: cfg.colors
    };
}

function handleAnomalyPalmer({config}) {
    const cfg = getLegend('anomaly', 'palmer', config);

    return {
        bins: cfg.bins.us,
        colors: cfg.colors
    };
}

function handlePctAvg({timescale, config}) {
    const cfg = getLegend('pctavg', 'pcp', config);

    return {
        bins: getValueBins(timescale, cfg.bins),
        colors: cfg.colors
    };
}

async function getDegreeDayBins(dd, locId, ts, mn) {
    const climateRegionStates = await getClimateRegionStates();

    const intTs = parseInt(ts === 'ytd' ? mn : ts, 10);
    const numBins = 10;

    const intLocId = parseInt(locId, 10);
    let climateRegion = 110;

    for (const [region, stateIds] of Object.entries(climateRegionStates)) {
        if (stateIds.includes(intLocId)) {
            climateRegion = Number(region);
            break;
        }
    }

    let begVal;
    let interval;

    const scales = await getDdScales();
    const regionScales = scales?.[dd]?.[climateRegion];
    if (!regionScales) {
        throw new Error(`Missing degree day scale for ${dd} region ${climateRegion}`);
    }

    // Find matching timescale configuration
    for (const [ts, stats] of Object.entries(regionScales)) {
        if (intTs <= Number(ts)) {
            begVal = stats.begVal;
            interval = stats.interval;
            break;
        }
    }

    // Generate bins
    const bins = [0];

    for (let bin = 0; bin < numBins; bin++) {
        bins.push(begVal + (bin * interval));
    }

    return bins;
}

/**
 * Builds HTML for a binned (value/anomaly/mean) legend.
 *
 * @param {Object} opts
 * @param {String} opts.id                DOM id prefix (parameter name)
 * @param {Array}  opts.bins              Bin values
 * @param {Number} opts.colorCount        Number of color buckets
 * @param {Function} opts.getColor        (val) => color
 * @param {Boolean} opts.showLeftArrow
 * @param {Function} opts.formatLabel     (val, ndx, isLast) => html string
 * @param {Boolean} [opts.showRightArrow] default true
 */
export function buildBinnedLegendHtml({
    id,
    bins,
    colorCount,
    getColor,
    showLeftArrow,
    formatLabel,
    showRightArrow = true
}) {
    let colors = '';
    let labels = '';

    const hasOuterColors = colorCount === bins.length + 1;
    const isOneToOne     = colorCount === bins.length;

    // LEFT ARROW
    if (showLeftArrow) {
        const val = bins[0] - 1;
        colors += `<span class="left-arrow value-arrow" style="border-right-color:${getColor(val)}"></span>`;
    }

    // Determine rectangle range
    let start = 0;
    let end   = bins.length;

    if (hasOuterColors) {
        // skip last threshold (outer bucket handled by arrow)
        end = bins.length - 1;
    } 
    else if (isOneToOne) {
        // prevent duplicating edge colors when arrows exist
        if (showLeftArrow)  start = 1;
        if (showRightArrow) end   = bins.length - 1;
    }

    // RECTANGLES
    for (let i = start; i < end; i++) {
        const val = bins[i];
        colors += `<span class="key" style="background-color:${getColor(val)}"></span>`;
    }

    // LABELS
    for (let i = 0; i < bins.length; i++) {
        const isLast = i === bins.length - 1;
        labels += `<span class="label">${formatLabel(bins[i], i, isLast)}</span>`;
    }

    // RIGHT ARROW
    if (showRightArrow) {
        const val = Infinity;
        colors += `<span class="right-arrow value-arrow" style="border-left-color:${getColor(val)}"></span>`;
    }

    return `
        <div id="${id}-keys">${colors}</div>
        <div id="${id}-labels">${labels}</div>
    `;
}

/**
 * Generates the HTML for the rank legend.
 * @param {Array} colors - Array of color strings.
 * @param {Array} bins - Array of bin values.
 * @param {String} lowLabel - Text for the lowest rank.
 * @param {String} highLabel - Text for the highest rank.
 */
export function buildRankLegendHtml(colors, bins, lowLabel, highLabel) {
    const lastNdx = bins.length - 1;
    
    const rankCells = [
        `<span class="rankLabel" style="color:${colors[0]}">${lowLabel}</span>`,
        `<span class="left-arrow rank-arrow" style="border-right-color:${colors[0]}"></span>`
    ];

    bins.forEach((i, ndx) => {
        if (ndx === 0 || ndx === lastNdx) return;

        let full = '';
        let medium = '';
        let compact = '';

        if (ndx === 1) {
            full    = 'Much Below';
            medium  = 'Much Below';
            compact = '&#8675;&#8530;';
        } else if (ndx === 2) {
            full    = 'Below Average';
            medium  = 'Below Avg';
            compact = '&#8675;&#8531;';
        } else if (ndx === lastNdx - 2) {
            full    = 'Above Average';
            medium  = 'Above Avg';
            compact = '&#8673;&#8531;';
        } else if (ndx === lastNdx - 1) {
            full    = 'Much Above';
            medium  = 'Much Above';
            compact = '&#8673;&#8530;';
        } else {
            full    = 'Near Average';
            medium  = 'Near Avg';
            compact = 'Avg';
        }

        const label = `
            <span class="rank-text label-full">${full}</span>
            <span class="rank-text label-medium">${medium}</span>
            <span class="rank-text label-compact">${compact}</span>
        `;

        const color = colors[ndx];
        rankCells.push(`<span class="rankKey" style="background-color:${color}">${label}</span>`);
    });

    rankCells.push(
        `<span class="right-arrow rank-arrow" style="border-left-color:${colors[lastNdx]}"></span>` +
        `<span class="rankLabel" style="color:${colors[lastNdx]}">${highLabel}</span>`
    );

    return `<div>${rankCells.join('')}</div>`;
}