import { UsHaywoodDao } from './UsHaywoodDao.js';
import { GlobalHaywoodDao } from './GlobalHaywoodDao.js';

export class HaywoodDao {
    async getHaywoodData(consts, vars) {
        const scope = consts.scope;

        if (scope === 'global') {
            const globalDao = new GlobalHaywoodDao();
            return await globalDao.getGlobalHaywoodData(vars);
        } else {
            const { parameter, locationId, month } = vars;
            const usDao = new UsHaywoodDao();
            return await usDao.getUsHaywoodData(scope, parameter, locationId, month);
        }
    }
}
