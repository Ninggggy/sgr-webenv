import { UsRankingsDao } from './UsRankingsDao.js';
import { GlobalRankingsDao } from './GlobalRankingsDao.js';

export class RankingsDao {
    async getRankingsData(consts, vars) {
        const scope = consts.scope;

        if (scope === 'global') {
            const globalDao = new GlobalRankingsDao();
            return await globalDao.getGlobalRankingsData(vars);
        } else {
            const { parameter, locationId, date } = vars;
            const usDao = new UsRankingsDao();
            return await usDao.getUsRankingsData(scope, parameter, locationId, date);
        }
    }
}
