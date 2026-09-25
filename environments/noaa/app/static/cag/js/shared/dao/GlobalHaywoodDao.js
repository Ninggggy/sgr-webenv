import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class GlobalHaywoodDao {
    async getGlobalHaywoodData(vars) {
        const { parameter, region, surface, lat, lon, month } = vars;
        const rgn = region === 'coords' ? `${Number(lat)},${Number(lon)}` : `${encodeURIComponent(region)}`;
        const safeSfc = encodeURIComponent(surface);
        const safeParam = encodeURIComponent(parameter);

        const safeMonth = Number.parseInt(month, 10);
        if (Number.isNaN(safeMonth)) {
            throw new Error(`Invalid month: ${month}`);
        }

        const dataUrl = `${base}/global/haywood/${rgn}/${safeParam}/${safeSfc}/${safeMonth}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'GlobalHaywoodDao.getGlobalHaywoodData', fallback: {} });
    }
}