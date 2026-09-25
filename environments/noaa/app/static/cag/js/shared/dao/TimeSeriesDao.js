import { UsTimeSeriesDao } from './UsTimeSeriesDao.js';
import { GlobalTimeSeriesDao } from './GlobalTimeSeriesDao.js';

export class TimeSeriesDao {
    async getTimeSeriesData(consts, vars) {
        const scope = consts.scope;

        if (scope === 'global') {
            const globalDao = new GlobalTimeSeriesDao();
            return await globalDao.getGlobalTimeSeriesData(vars);
        } else {
            const { parameter, locationId, timescale, month } = vars;
            const usDao = new UsTimeSeriesDao();
            return await usDao.getUsTimeSeriesData(scope, parameter, locationId, timescale, month);
        }
    }
}
