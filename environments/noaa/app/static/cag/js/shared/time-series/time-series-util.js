import { DataAveragesDao } from '../dao/DataAveragesDao.js';
import { BinomialFilter } from './BinomialFilter.js';
import { LoessInterpolator } from './Loess.js';
import { RunningMean } from './RunningMean.js';
import FormatUtil from '../../utils/format-utils.js';

export async function getValues(data, begYear, endYear, month, minDate, maxDate) {
    if (!data || Object.keys(data).length === 0) {
        return [];
    }

    const begDate = month == 0 ? `${begYear}01` : `${begYear}`;
    const endDate = month == 0 ? `${endYear}12` : `${endYear}`;

    const values = {};

    for (const key in data) {
        if (!data.hasOwnProperty(key)) continue;

        if (key >= begDate && key <= endDate) {
            if (key < minDate || key > maxDate) continue;
            values[key] = data[key];
        }
    }

    return values;
}

export async function getMinMaxValues(values, trendValues, mean, plotDepartures = false) {
    const allSources = [
        ...Object.values(values || {}),
        ...Object.values(trendValues || {}),
        ...Object.values(mean || {})
    ];

    const numericValues = allSources.filter(
        val => typeof val === 'number' && !isNaN(val)
    );

    let minVal = numericValues.length > 0 ? Math.min(...numericValues) : 0;
    let maxVal = numericValues.length > 0 ? Math.max(...numericValues) : 0;

    // Force the 0-line to always be visible on departure charts
    if (plotDepartures) {
        minVal = Math.min(minVal, 0);
        maxVal = Math.max(maxVal, 0);
    }

    return { minVal, maxVal };
}

export async function getMinMaxKeys(values) {
    if (!values || Object.keys(values).length === 0) {
        return { minKey: 0, maxKey: 0 };
    }

    const keys = Object.keys(values)
        .map(k => parseInt(k, 10))
        .filter(num => !isNaN(num));

    if (keys.length === 0) {
        return { minKey: 0, maxKey: 0 };
    }

    const minKey = Math.min(...keys);
    const maxKey = Math.max(...keys);

    return { minKey, maxKey };
}

export async function getParameterSeries(values, paramMeta, month, precision, plotDepartures = false, mean = {}) {
    if (!values || Object.keys(values).length === 0) return [];

    const chartType = plotDepartures ? 'bar' : paramMeta.chartType;
    const color = paramMeta.hex;
    const backgroundColor = chartType === 'area' ? `#fff ${color}` : color;
    const text = paramMeta.title + (plotDepartures ? ' Departure' : '');
    const legendItemText = paramMeta.shortTitle.replace(/ /g, '\n');

    // Convert to array, map numeric values
    const filteredValues = Object.entries(values).map(([date, value]) => {
        if (typeof value === 'number' && !isNaN(value)) {
            if (plotDepartures) {
                let anom;
                if (month > 0) {
                    anom = value - mean[month];
                } else {
                    const m = Number(String(date).slice(-2));
                    anom = value - mean[m];
                }
                return Number((anom).toFixed(precision));
            }
            return value;
        }
        return null;
    });

    const tableValues = plotDepartures
        ? Object.values(values).map(value => typeof value === 'number' && !isNaN(value) ? parseFloat(value) : null)
        : filteredValues;

    const parameterSeries = {
        tableValues,
        type: chartType,
        lineColor: color,
        backgroundColor: backgroundColor,
        marker: {
            backgroundColor: backgroundColor
        },
        scales: 'scaleX,scaleY,scaleY2',
        text: text,
        legendItem: {
            visible: false,
            text: legendItemText,
            mediaRules: [
                {
                    maxWidth: 689,
                    fontSize: '12px'
                }
            ]
        },
        values: filteredValues,
        guideLabel: {
            jsRule: 'cagRolloverText()'//from '../zingchartFormatter.js';
        }
    };

    // Add bar-specific styling rules
    if (chartType === 'bar') {
        parameterSeries.rules = [
            {
                rule: '%v > 0',
                backgroundColor: paramMeta.posHex,
                lineColor: paramMeta.posHex
            },
            {
                rule: '%v < 0',
                backgroundColor: paramMeta.negHex,
                lineColor: paramMeta.negHex
            }
        ];
        parameterSeries.borderColor = '#000';
        parameterSeries.borderWidth = (month == 0 ? 0 : 1);
    }

    return parameterSeries;
}

export async function getBasePrdMean(timeSeries, month, paramMeta, begBaseYear, endBaseYear) {
    if (!timeSeries || Object.keys(timeSeries).length === 0) return;

    const precision = paramMeta.precision ?? 0;
    const unitsAbbr = paramMeta.unitsAbbr ?? '';

    const dataAvgsDao = new DataAveragesDao();
    const basePrdAvg = await dataAvgsDao.getTimeSeriesBasePrdAvg(timeSeries, month, precision, begBaseYear, endBaseYear);

    const base_prd_avg = basePrdAvg.base_prd_avg;
    const mean = base_prd_avg[month];
  
    // Format number with fixed precision
    const formattedAvg = FormatUtil.number(mean, precision);

    // Replace 'in' with '"' if unitsAbbr exists
    const unitsText = unitsAbbr === 'in' ? '"' : unitsAbbr;

    const text = `${basePrdAvg.firstbaseyear}-${basePrdAvg.lastbaseyear} Average: ${formattedAvg}${unitsText}`;

    return {
        type: 'line',
        range: [parseFloat(mean)],
        lineColor: paramMeta.meanHex,
        lineWidth: 2,
        placement: 'top',
        label: {
            text: text,
            backgroundColor: 'white',
            alpha: 0.7,
            textAlpha: 1,
            offsetX: 10,
            offsetY: -1,
            mediaRules: [
                {
                    minWidth: 690,
                    fontSize: '16px'
                },
                {
                    maxWidth: 689,
                    fontSize: '12px'
                }
            ]
        },
        mean: base_prd_avg
    };
}

export async function getFilterSeries(values, paramMeta, filter, filters, trend) {
    if (!values || Object.keys(values).length === 0) return [];

    let filterValues = [];
    if (filter === 'binomial') {
        const binomialFilter = new BinomialFilter();
        filterValues = binomialFilter.smooth(values, 9);
    } else if (filter === 'loess') {
        const loessInterpolator = new LoessInterpolator();
        filterValues = loessInterpolator.smooth(values);
    } else if (filter === 'running-mean') {
        const runningMean = new RunningMean();
        filterValues = runningMean.getRunningMean(values, 5);
    }

    const title = filters[filter]['name'];
    return {
            'type':       'line',
            'marker':     {'visible': false},
            'text':       title,
            'legendItem': {
                'text': trend ? title.replace(/ /g, '\n') : title,
                'mediaRules': [
                    {
                        'maxWidth': 689,
                        'fontSize': "12px"
                    }
                ]
            },
            'lineColor':  paramMeta.filterHex,
            'values':     Object.values(filterValues)
                .filter(value => value === null || (typeof value === 'number' && !isNaN(value))),
            'guideLabel': {'visible': false}
        };
}

export async function getTrendSeries(
    begDate,
    endDate,
    paramMeta,
    trendBases,
    trendBase,
    month,
    trendValues,
    slopeIntercept
) {
    const start = parseInt(begDate, 10);
    const end = parseInt(endDate, 10);

    const filtered = Object.entries(trendValues)
        .filter(([key]) => {
            const numKey = parseInt(key, 10);
            return numKey >= start && numKey <= end;
        })
        .map(([, value]) => (typeof value === 'number' && !isNaN(value)) ? value : null);

    // These are units/year.
    // Multiply by 10 or 100 if per decade or century; and by 12 if all months is selected.
    const { begTrendyear, endTrendyear, m, ciUpper } = slopeIntercept;

    const precision    = paramMeta.precision;
    const units        = (paramMeta.unitsAbbr ?? '').replace(/^in$/, '"');
    const multiplier   = parseInt(trendBase, 10) * (month === 0 ? 12 : 1);
    const trendValue   = m * multiplier;
    const ciUpperValue = ciUpper * multiplier;
    const trend        = FormatUtil.number(trendValue, precision);
    const sign         = m > 0 ? '+' : '';

    // Calculate the margin of error (distance from trend to upper bound)
    const marginOfError = ciUpperValue - trendValue;
    const ciMoe = FormatUtil.number(marginOfError, precision);

    let text = `${begTrendyear}-${endTrendyear} Trend\n(${sign}${trend}`;
    if (ciMoe !== null && parseFloat(ciMoe) !== 0) {
        text += ` ± ${ciMoe}`;
    }
    text += `${units}/${trendBases[trendBase]})`;

    return {
        'type': 'line',
        'marker': {'visible': 'false'},
        'text': 'Trend',
        'legendItem': {
            'text': text,
            'mediaRules': [
                {
                    'maxWidth': 689,
                    'fontSize': "12px"
                }
            ]
        },
        'lineColor': paramMeta.trendHex ?? '#000',
        'values': filtered,
        'guideLabel': {'visible': 'false'}
    };
}