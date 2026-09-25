import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class GlobalRankingsDao {
    async getGlobalRankingsData(vars) {
        const { parameter, region, surface, lat, lon, date } = vars;
        const rgn = region === 'coords' ? `${Number(lat)},${Number(lon)}` : `${encodeURIComponent(region)}`;
        const safeSfc = encodeURIComponent(surface);
        const safeParam = encodeURIComponent(parameter);
        const safeDate = encodeURIComponent(date);
        const dataUrl = `${base}/global/rankings/${rgn}/${safeParam}/${safeSfc}/${safeDate}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'GlobalRankingsDao.getGlobalRankingsData', fallback: {} });
    }
}