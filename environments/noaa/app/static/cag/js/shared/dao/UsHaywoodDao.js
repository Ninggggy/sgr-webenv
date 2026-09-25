import { LocationIdsDao } from './LocationIdsDao.js';
import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class UsHaywoodDao {
    constructor() {
        this.locIdDao = new LocationIdsDao();
    }

    async getUsHaywoodData(scope, parameter, locId, month) {
        const safeScope = encodeURIComponent(scope);
        const safeParam = encodeURIComponent(parameter);

        const rawId = this.locIdDao.getDataLocationId(scope, locId, true);
        const safeId = encodeURIComponent(rawId);

        const safeMonth = Number.parseInt(month, 10);
        if (Number.isNaN(safeMonth)) {
            throw new Error(`Invalid month: ${month}`);
        }

        const dataUrl = `${base}/${safeScope}/haywood/${safeId}/${safeParam}/${safeMonth}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'UsHaywoodDao.getUsHaywoodData', fallback: {} });
    }
}