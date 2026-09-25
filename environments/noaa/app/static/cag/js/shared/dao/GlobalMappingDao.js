import { base } from '../../globals.js';
import { fetchJson } from '../../utils/fetch.js';

export class GlobalMappingDao {
    /**
     * @param {string} parameter - e.g., 'tavg'
     * @param {string} year - YYYY format
     * @param {string} month - '1', '13' (for annual)
     */
    async getGlobalMappingData(parameter, year, month) {
        const yr = Number(year);
        if (Number.isNaN(yr)) {
            throw new Error(`Invalid year: ${year}`);
        }

        const mn = Number(month);
        if (Number.isNaN(mn)) {
            throw new Error(`Invalid month: ${month}`);
        }

        const safeParam = encodeURIComponent(parameter);
        const date      = `${yr}${mn === 13 ? '' : String(mn).padStart(2, '0')}`;

        const dataUrl   = `${base}/global/mapping/${safeParam}-${date}/data.json?raw=1`;

        return fetchJson(dataUrl, { context: 'GlobalMappingDao.getGlobalMappingData', fallback: {} });
    }
}
