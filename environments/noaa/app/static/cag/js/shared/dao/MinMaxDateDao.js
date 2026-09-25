import { minDates, maxDates } from "../../globals.js";
import ScopeUtil from "../../utils/scope-utils.js";

const {
    global:     isGlobal,
    national:   isNational,
    regional:   isRegional,
    statewide:  isStatewide,
    divisional: isDivisional,
    county:     isCounty,
    city:       isCity
} = ScopeUtil.is;

class MinMaxDateDao {
    constructor(sessionData = null) {
        // Optionally inject session-like data structure (if needed)
        this.sessionData = sessionData;
    }

    getFirstDate(scopeKey) {
        return minDates[scopeKey] || Math.min(...Object.values(minDates));
    }

    getLastDate(scopeKey) {
        return maxDates[scopeKey] || Math.max(...Object.values(maxDates));
    }

    getMinDate(scope, section, param, location = null) {
        if (isGlobal(scope)) {
            return minDates[param === 'pcp' ? 'global-pcp' : 'global'];
        }

        // Fallback to sessionData location if none supplied
        if (
            !location &&
            this.sessionData &&
            this.sessionData.cag &&
            this.sessionData.cag[scope] &&
            this.sessionData.cag[scope][section] &&
            this.sessionData.cag[scope][section].location
        ) {
            location = this.sessionData.cag[scope][section].location;
        }

        if (section === 'data-info' || isNational(scope) || isRegional(scope)) {
            return minDates.national;
        }

        if (section === 'mapping' || isStatewide(scope)) {
            if (location == 50) {
                return minDates.alaska;
            } else if (location == 51) {
                return minDates.hawaii;
            } else {
                return minDates.national;
            }
        }

        if (isCounty(scope)) {
            const locStr = String(location || '');
            if (locStr.startsWith('AK')) {
                return minDates.alaska;
            } else if (locStr.startsWith('HI')) {
                return minDates.hawaii;
            } else {
                return minDates.national;
            }
        }

        if (isDivisional(scope)) {
            const stateCode = location != null ? String(location).slice(0, -2) : '';
            if (stateCode === '50') {
                return minDates.alaska;
            } else if (stateCode === '51') {
                return minDates.hawaii;
            } else {
                return minDates.national;
            }
        }

        if (isCity(scope)) {
            return this.getCityMinDate(minDates, location);
        }

        return minDates.national;
    }

    getCityMinDate(minDates, cityId) {
        return (cityId && minDates.hasOwnProperty(cityId))
            ? minDates[cityId]
            : minDates.national;
    }

    getMaxDate(scope, param) {
        const key =
            isGlobal(scope)
                ? (param === 'pcp' ? 'global-pcp' : 'global')
                : 'national';

        return parseInt(maxDates[key], 10);
    }
}

export default MinMaxDateDao;