import { LocationIdsDao } from './LocationIdsDao.js';
import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class UsTimeSeriesDao {
    constructor() {
        this.locIdDao = new LocationIdsDao();
    }

    async getUsTimeSeriesData(scope, parameter, locId, timescale, month) {
        const safeScope = encodeURIComponent(scope);
        const safeParam = encodeURIComponent(parameter);
        const safeTs = encodeURIComponent(timescale);

        const safeMonth = Number.parseInt(month, 10);
        if (Number.isNaN(safeMonth)) {
            throw new Error(`Invalid month: ${month}`);
        }

        const rawId = this.locIdDao.getDataLocationId(scope, locId, true);
        const safeId = encodeURIComponent(rawId);

        const dataUrl = `${base}/${safeScope}/time-series/${safeId}/${safeParam}/${safeTs}/${safeMonth}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'UsTimeSeriesDao.getUsTimeSeriesData', fallback: {} });
    }
}