import { UsMappingDao } from './UsMappingDao.js';
import { GlobalMappingDao } from './GlobalMappingDao.js';

export class MappingDao {
    async getMappingData(scope, vars) {
        const parameter = vars.parameter;

        if (scope === 'global') {
            const { year, month } = vars;
            const globalDao = new GlobalMappingDao();
            return await globalDao.getGlobalMappingData(parameter, year, month)
        } else {
            const { locationId, parameter, timescale, date } = vars;
            const usDao = new UsMappingDao();
            return await usDao.getUsMappingData(scope, locationId, parameter, timescale, date)
        }
    }
}