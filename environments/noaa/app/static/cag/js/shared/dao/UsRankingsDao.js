import { LocationIdsDao } from './LocationIdsDao.js';
import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class UsRankingsDao {
    constructor() {
        this.locIdDao = new LocationIdsDao();
    }

    async getUsRankingsData(scope, parameter, locId, date) {
        const safeScope = encodeURIComponent(scope);
        const safeParam = encodeURIComponent(parameter);
        const safeDate = encodeURIComponent(date);

        const rawId = this.locIdDao.getDataLocationId(scope, locId, true);
        const safeId = encodeURIComponent(rawId);

        const dataUrl = `${base}/${safeScope}/rankings/${safeId}/${safeParam}/${safeDate}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'UsRankingsDao.getUsRankingsData', fallback: {} });
    }
}