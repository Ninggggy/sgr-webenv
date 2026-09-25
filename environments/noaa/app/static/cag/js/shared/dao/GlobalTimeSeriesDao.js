import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class GlobalTimeSeriesDao {
    async getGlobalTimeSeriesData(vars) {
        const { parameter, region, surface, lat, lon, timescale, month } = vars;
        const rgn = region === 'coords' ? `${Number(lat)},${Number(lon)}` : `${encodeURIComponent(region)}`;
        const safeSfc = encodeURIComponent(surface);
        const safeParam = encodeURIComponent(parameter);
        const safeTs = encodeURIComponent(timescale);

        const safeMonth = Number.parseInt(month, 10);
        if (Number.isNaN(safeMonth)) {
            throw new Error(`Invalid month: ${month}`);
        }

        const dataUrl = `${base}/global/time-series/${rgn}/${safeSfc}/${safeParam}/${safeTs}/${safeMonth}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'GlobalTimeSeriesDao.getGlobalTimeSeriesData', fallback: {} });
    }
}