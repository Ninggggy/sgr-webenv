import zingchart from '../../../assets/zingchart-2.9.16-1/es6.js';
import { loadZingChartConfig } from '../../utils/load-zingchart-config.js';
import { TimeSeriesDao } from '../dao/TimeSeriesDao.js';
import {
    getValues,
    getBasePrdMean,
    getMinMaxValues,
    getMinMaxKeys,
    getParameterSeries,
    getFilterSeries,
    getTrendSeries
} from './time-series-util.js';
import { LinearModel } from './LinearModel.js';
import TitleUtil from './title-util.js';
import Util from '../../utils/util.js';

const { degreeDay: isDegreeDay, precip: isPrecip } = Util.parameter.is;
const isGlobal = Util.scope.is.global;
const paramMetaVal = Util.parameter.metaVal;

async function plotTimeSeries(cag, chartId = 'chartCanvas') {
    const consts = cag.constants;
    const vars = cag.variables;

    const { parameters, filters } = consts;
    const {
        locationId,
        region: globalRegion,
        month,
        timescale,
        filter,

        basePeriod,
        begBaseYear,
        endBaseYear,

        trend,
        trend_base,
        begtrendyear,
        endtrendyear,
    } = vars;

    const scope     = consts.scope;
    const parameter = vars.parameter
    const paramMeta = parameters[parameter];

    const precision = Util.getPrecision(locationId, parameter);

    const tsDao = new TimeSeriesDao();
    const [template, timeSeries] = await Promise.all([
        loadZingChartConfig('time-series'),
        tsDao.getTimeSeriesData(consts, vars)
    ]);

    if (!timeSeries || Object.keys(timeSeries).length === 0) {
        console.error('Failed to load time series data.');
        return false;
    }

    // Deep clone to avoid mutating the base config
    const config = structuredClone(template);

    const isDegDay = isDegreeDay(parameter);

    const minDate = Object.keys(timeSeries)[0];
    const maxDate = Object.keys(timeSeries)[Object.keys(timeSeries).length - 1];
    const values = await getValues(timeSeries, vars.begyear, vars.endyear, month, minDate, maxDate);
    if (!Object.keys(values).length) {
        console.warn(`${parameter} values empty`);
    }

    // Check if we are dealing with global tavg
    const isGlobalTavg = isGlobal(scope) && parameter === 'tavg';
    
    // Trigger departure math if the checkbox is checked, OR if it's global tavg with a custom base period
    const plotDeparturesChecked = !!document.getElementById('plotDepartures')?.checked || (isGlobalTavg && basePeriod);

    let mean = {};
    let meanText = '';
    if (basePeriod) {
        const basePrdMean = await getBasePrdMean(timeSeries, month, paramMeta, begBaseYear, endBaseYear);
        if (basePrdMean && basePrdMean.range && basePrdMean.label) {
            if (!plotDeparturesChecked) config.scaleY.markers = [basePrdMean];
            mean = basePrdMean.mean;
            meanText = basePrdMean.label.text;
        }
    }

    const series = [];

    const plotDepartures = plotDeparturesChecked && (!isNaN(mean[month]));

    const parameterSeries = await getParameterSeries(values, paramMeta, month, precision, plotDepartures, mean);
    const tableValues = parameterSeries.tableValues;
    delete parameterSeries.tableValues;
    if (parameterSeries.length === 0) {
        console.warn(`${parameter} Series empty`);
    }

    series.push(parameterSeries);

    if (filter && filter !== 'none') {
        // Rebuild object with chronological keys so the filter doesn't pad with undefined indices
        const anomaliesObj = {};
        let idx = 0;
        for (const key of Object.keys(values)) {
            anomaliesObj[key] = parameterSeries.values[idx++];
        }
        
        const filterSeries = await getFilterSeries(anomaliesObj, paramMeta, filter, filters, trend && month > 0);
        series.push(filterSeries);
    }

    let trendValues = {};
    if (trend && month > 0) {
        const { minKey: begDate, maxKey: endDate } = await getMinMaxKeys(values);
        const linearModel    = new LinearModel();
        const slopeIntercept = linearModel.getSlopeIntercept(timeSeries, begtrendyear, endtrendyear);

        trendValues = linearModel.getTrendValues(timeSeries, minDate, maxDate, slopeIntercept);

        if (plotDepartures) {
            for (let k in trendValues) {
                if (typeof trendValues[k] === 'number') {
                    let anom;
                    if (month > 0) {
                        anom = trendValues[k] - mean[month];
                    } else {
                        const m = Number(String(k).slice(-2));
                        anom = trendValues[k] - mean[m];
                    }
                    trendValues[k] = anom; 
                }
            }
        }

        const trendSeries = await getTrendSeries(
            begDate,
            endDate,
            paramMeta,
            consts.trendBases,
            trend_base,
            month,
            trendValues,
            slopeIntercept
        );
        series.push(trendSeries);
    }

    let title, shortTitle;
    if (isGlobal(scope)) {
        const { globalRegions, surfaces } = consts;
        const { region, surface, lat, lon } = vars;
        title = TitleUtil.getGlobalTitle(
            parameters,
            parameter,
            globalRegions,
            region,
            lat,
            lon,
            surfaces,
            surface
        );
        shortTitle = title;
    } else {
        const { locations, usStates } = consts;
        title      = TitleUtil.getUsTitle(scope, locations, locationId, parameters, parameter, usStates, false);
        shortTitle = TitleUtil.getUsTitle(scope, locations, locationId, parameters, parameter, usStates, true);
    }
    const subtitle      = TitleUtil.getDateSpan(timescale, month);
    const shortSubtitle = TitleUtil.getDateSpan(timescale, month, true);

    const { minVal, maxVal } = await getMinMaxValues(parameterSeries.values, trendValues, plotDepartures ? {} : mean, plotDepartures);

    if (plotDepartures) {
        if (!isGlobal(scope) || parameter !== 'tavg') title += ' Departure';
    }
    config.title.text = title;
    config.title.mediaRules.push({ 'minWidth': 1110, text: title });
    config.title.mediaRules.push({ 'maxWidth': 1109, text: title });

    let deptStr = '';
    let shortDeptStr = '';

    if (plotDepartures || isGlobalTavg) {
        const units = (paramMeta.unitsAbbr ?? '').replace(/^in$/, '"');
        
        // Default to the correct standard baseline if the user hasn't defined a custom base period
        let startBase = basePeriod ? begBaseYear : (globalRegion === 'coords' ? 1991 : 1901);
        let endBase = basePeriod ? endBaseYear : (globalRegion === 'coords' ? 2020 : 2000);
        
        // Only show the offset mean if they checked the box/shifted the baseline
        const meanVal = (mean && mean[month]) ? mean[month] : 0; 
        const meanStr = (month > 0 && plotDepartures && !isGlobalTavg) ? ` (${meanVal}${units})` : '';
        
        deptStr = ` ${startBase}-${endBase}${isGlobalTavg ? ' Base Period' : ' Departure'}${meanStr}`;
        shortDeptStr = ` ${deptStr.replace('Departure', 'Dept')}`;
    }

    config.subtitle.text = `${subtitle}${deptStr}`;
    config.subtitle.mediaRules.push({ 'minWidth': 1109, text: `${subtitle}${deptStr}` });
    config.subtitle.mediaRules.push({ 'maxWidth': 1109, text: `${shortSubtitle}${shortDeptStr}` });

    // NOAA watermark x location
    if (scope !== 'global') {
        config.images[0]['x'] = isDegDay ? 115 : 85;
    }

    if (parameterSeries.type === 'bar') {
        const dynamicOffset = (100 / (2 * Object.values(parameterSeries.values).length)) + "%";
        config.scaleX.offsetStart = dynamicOffset;
        config.scaleX.offsetEnd = dynamicOffset;
    }

    config.scaleX.labels = month == 0
        // Display MMM YYYY date format when all months is selected (month == 0)
        ? Object.keys(values).map(date => {
            const year = parseInt(String(date).slice(0, 4), 10);
            const month = String(date).slice(4, 6) - 1;
            return new Date(year, month, 10).toLocaleString('en-US', { month: 'short', year: 'numeric' });
        })
        // else, display key value (year)
        : Object.keys(values);

    config.scaleY.label.text = isDegDay ? paramMetaVal['unitsText'] : '';
    config.scaleY.format     = 'cagScaleYFormat()';//from '../zingchartFormatter.js';
    config.scaleY.decimals   = isGlobal(scope) && isPrecip(parameter) ? 0 : precision;
    config.scaleY.minValue   = parseFloat(minVal);
    config.scaleY.maxValue   = parseFloat(maxVal);

    config.scaleY2.label.text = isDegDay ? paramMetaVal['units2Text'] : '';
    config.scaleY2.format     = 'cagScaleY2Format()';//from '../zingchartFormatter.js';
    config.scaleY2.decimals   = isGlobal(scope) && isPrecip(parameter) ? 0 : precision;
    config.scaleY2.minValue   = parseFloat(minVal);
    config.scaleY2.maxValue   = parseFloat(maxVal);

    if (isDegDay && maxVal < 10) {
        config.scaleY.step = 1;
        config.scaleY2.step = 1;
    }

    config.crosshairX.plotLabel.backgroundColor = paramMetaVal['hex'];
    config.legend.visible = (series.length > 1);

    config.series = series;

    // if all months is selected (month == 0), too many points to animate
    if (month > 0) {
        config.plot.animation = [];
    } else {
        delete config.plot.animation;
    }

    zingchart.render({
        id: chartId,
        data: config,
        height: 500,
        width: '100%'
    });

    return {
        'title':    config.title.text,
        'subtitle': config.subtitle.text,
        'dates':    config.scaleX.labels,
        'values':   tableValues,
        mean,
        meanText
    }
}

export { plotTimeSeries };