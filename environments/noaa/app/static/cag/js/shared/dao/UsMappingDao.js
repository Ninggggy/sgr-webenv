import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class UsMappingDao {
    /**
     * @param {string} scope - 'national', 'statewide', etc.
     * @param {string} locationId - e.g., '110'
     * @param {string} parameter - e.g., 'tavg'
     * @param {string} timescale - e.g., '2', 'ytd'
     * @param {string} date - YYYYMM format
     */
    async getUsMappingData(scope, locationId, parameter, timescale, date) {
        const safeScope = encodeURIComponent(scope);
        const safeLoc   = encodeURIComponent(locationId);
        const safeParam = encodeURIComponent(parameter);
        const safeDate  = encodeURIComponent(date);

        let tsValue;
        if (timescale === 'ytd') {
            const month = Number.parseInt(String(date).slice(-2), 10);
            if (Number.isNaN(month)) {
                throw new Error(`Invalid date for Year-to-Date timescale: ${date}`);
            }
            tsValue = month;
        } else {
            tsValue = timescale;
        }
        const safeTs = encodeURIComponent(tsValue);

        const dataUrl   = `${base}/${safeScope}/mapping/${safeLoc}-${safeParam}-${safeDate}-${safeTs}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'UsMappingDao.getUsMappingData', fallback: {} });
    }
}