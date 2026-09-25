import Util from "../../utils/util.js";
import { separator } from '../zingchartFormatter.js';

const formatNumber = Util.format.number;
const toNumber = Util.format.toNumber;

const legendValue = (x, precision) => {
    const num = toNumber(x);
    return formatNumber(num, precision, separator(num));
};

function orderData(data) {
    const allKeys = Object.keys(data);

    // separate years and Average
    const years = allKeys.filter(k => k !== "Average");
    const lastYear = Math.max(...years.map(Number)).toString();

    // pick 12th month values (or last available month if missing)
    const decValues = years.map(year => {
        const months = Object.keys(data[year]);
        const lastMonthKey = months[months.length - 1];
        return { year, value: data[year][lastMonthKey] ?? null };
    });

    // exclude last year from ranking
    const filtered = decValues.filter(d => d.year !== lastYear && d.value != null);

    // sort ascending
    filtered.sort((a, b) => a.value - b.value);

    // bottom 5 → reverse so it's highest → lowest
    const bottom5 = filtered.slice(0, 5).reverse().map(d => d.year);

    // top 5 → already highest → lowest
    const top5 = filtered.slice(-5).reverse().map(d => d.year);

    // desired last 12
    const orderedKeys = [...top5, "Average", ...bottom5, lastYear];

    // base keys = everything except those 12, in original order
    const baseKeys = allKeys.filter(k => !orderedKeys.includes(k));

    // final order
    const finalKeys = [...baseKeys, ...orderedKeys];

    // build Map (preserves order properly for numeric keys)
    const ordered = new Map();
    for (const key of finalKeys) {
        ordered.set(key, data[key]);
    }

    return ordered;
}

export async function getSeries(scope, unorderedData, parameter, precision, units, seriesEndMonth, hi5Colors, lo5Colors, currentColor) {
    if (!unorderedData || Object.keys(unorderedData).length === 0) {
        return '';
    }

    const data = orderData(unorderedData);

    /*
     * Last 12 elements of data array:
     *
     * -- top 5 years (that are not current year)
     * -- average
     * -- bottom 5 years (that are not current year)
     * -- current year
     */
    
    // Last 12 keys in the data object
    const last12 = [...data.keys()].slice(-12);
    const lastYear = last12[11];

    const lineStyles = {
        // current year
        [last12[11]]: { color: currentColor, style: 'solid', markerType: 'square' },

        // lowest years
        [last12[10]]: { color: lo5Colors[4], style: 'solid', markerType: 'triangle' },
        [last12[9]]: { color: lo5Colors[3], style: 'dashed', markerType: 'star5' },
        [last12[8]]: { color: lo5Colors[2], style: 'dotted', markerType: 'rpoly5' },
        [last12[7]]: { color: lo5Colors[1], style: 'solid', markerType: 'diamond' },
        [last12[6]]: { color: lo5Colors[0], style: 'solid', markerType: 'star8' },

        'Average': { color: '#000000', style: 'solid' },

        // highest years
        [last12[4]]: { color: hi5Colors[4], style: 'solid', markerType: 'circle' },
        [last12[3]]: { color: hi5Colors[3], style: 'dashed', markerType: 'star7' },
        [last12[2]]: { color: hi5Colors[2], style: 'dotted', markerType: 'star6' },
        [last12[1]]: { color: hi5Colors[1], style: 'solid', markerType: 'star4' },
        [last12[0]]: { color: hi5Colors[0], style: 'solid', markerType: 'star3' }
    };

    const series = [];

    for (const [year, monthData] of data) {
        // skip Average for global tavg anoms (since mean anom = 0)
        if (scope === 'global' && parameter === 'tavg' && year === 'Average') {
            continue;
        }

        let lineStyle = 'solid';
        let lineColor = '#c6cace';
        let lineWidth = 1;

        if (lineStyles[year]) {
            ({ style: lineStyle, color: lineColor } = lineStyles[year]);
            if (year === lastYear) {
                lineWidth = 4;
            } else if (year === 'Average') {
                lineWidth = 3;
            } else {
                lineWidth = 2;
            }
        }

        // get last non-null value in monthData
        // monthData may be an Object or a Map
        const monthValues = monthData instanceof Map
            ? Array.from(monthData.values())
            : Object.values(monthData);

        // filter out null/undefined
        const nonNullValues = monthValues.filter(v => v !== null && v !== undefined);

        const legendItemValue = nonNullValues.length
            ? legendValue(nonNullValues[nonNullValues.length - 1], precision)
            : '';

        // values arrays
        let values1 = [], values2 = [];

        if (seriesEndMonth < 12) {
            const range = Array.from({ length: 12 - seriesEndMonth }, (_, i) => i + seriesEndMonth + 1);
            values1 = await getValues(seriesEndMonth, year, range, monthData, precision);
        }

        const range2 = Array.from({ length: seriesEndMonth }, (_, i) => i + 1);
        values2 = await getValues(seriesEndMonth, year, range2, monthData, precision);

        const values = values1.concat(values2);

        const marker = (lineStyles[year] && lineStyles[year].markerType)
            ? { backgroundColor: lineColor, type: lineStyles[year].markerType, size: 6 }
            : { visible: false };

        const highlightMarker = { lineWidth: lineWidth * 2, alpha: 1 };

        const legendMarker = (lineStyles[year] && lineStyles[year].markerType)
            ? { type: lineStyles[year].markerType }
            : [];


        let legendItem, guideLabel;

        if (lineStyles[year]) {
            let mediaRules;
            if (year === 'Average') {
                mediaRules = [
                    { minWidth: 931, text: `${year} (${legendItemValue}${units})` },
                    { maxWidth: 930, text: `${year.replace('Average', 'Avg')} (${legendItemValue}${units})` },
                    { maxWidth: 690, text: year.replace('Average', 'Avg'), fontSize: '14px' },
                    { maxWidth: 689, fontSize: '12px' }
                ];
            } else {
                mediaRules = [
                    { minWidth: 691, text: `${year} (${legendItemValue}${units})` },
                    { maxWidth: 690, text: year, fontSize: '14px' },
                    { maxWidth: 689, fontSize: '12px' }
                ];
            }

            legendItem = { visible: true, mediaRules };
            guideLabel = { visible: true };
        } else {
            legendItem = guideLabel = { visible: false };
        }

        series.push({
            text: String(year),
            marker,
            highlightMarker,
            scales: 'scaleX,scaleY,scaleY2',
            lineColor,
            lineWidth,
            lineStyle,
            guideLabel,
            legendItem,
            legendMarker,
            values
        });
    }

    return series;
}

async function getValues(seriesEndMonth, year, range, inMonthData, precision) {
    const values = [];

    // convert Map to Object ("Average" is Map to preserve its key order)
    let monthData;
    if (inMonthData instanceof Map) {
        monthData = Object.fromEntries(inMonthData);
    } else {
        monthData = inMonthData;
    }

    for (const month of range) {
        const dateKey = (year === "Average")
            ? String(month)
            : `${month <= seriesEndMonth ? year : year - 1}${String(month).padStart(2, "0")}`;

        let value = monthData.hasOwnProperty(dateKey) && monthData[dateKey] != null
            ? Number.parseFloat(monthData[dateKey])
            : null;

        if (value !== null) {
            const factor = Math.pow(10, precision);
            value = Math.round(value * factor) / factor;
        }

        const monthName = new Date(2000, month - 1, 10)
        .toLocaleString("en-US", { month: "long" });

        values.push([monthName, value]);
    }

    return values;
}

export async function getMonthLabels(month) {
    const lbls = [], ls = [];
    for (let m = month + 1; m <= 12; m++) addMonth(m);
    for (let m = 1; m <= month; m++) addMonth(m);

    function addMonth(m) {
        const date = new Date(2000, m - 1, 1);
        const monthName = date.toLocaleString('en-US', { month: 'long' });
        lbls.push(monthName.substring(0, 3));
        ls.push(monthName[0]);
    }

    return { lbls, ls };
}
