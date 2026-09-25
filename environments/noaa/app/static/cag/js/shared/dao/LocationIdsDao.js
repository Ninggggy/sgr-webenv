import { content } from '../../globals.js';
import Util from '../../utils/util.js';
const {
    national:        isNational,
    statewide:       isStatewide,
    divisional:      isDivisional,
    stateToNational: isStateToNational
} = Util.scope.is;

export class LocationIdsDao {
    async getUsMappingLocationIds(scope) {
        const scopeKey = isNational(scope) ? 'regional' : scope;
        const url = `${content}/metadata/${scopeKey}-location-ids.json`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                console.error(`${url} failed to load (status ${response.status})`);
                return [];
            }

            const locationIds = await response.json();
            if (!Array.isArray(locationIds) || Object.keys(locationIds).length === 0) {
                console.error(`Failed to retrieve location IDs from ${url}`);
                return [];
            }

            return locationIds.map((locationId) => {
                let id = locationId;

                if (isStateToNational(scope)) {
                    // Strip trailing double zeroes
                    id = String(id).replace(/^(\d{2,3})00$/, '$1');
                }

                if (isStatewide(scope)) {
                    id = parseInt(id, 10);
                }

                return id;
            });
        } catch (err) {
            console.error(`Error fetching ${url}`)
            return [];
        }
    }

    /**
     * Formats location ID based on scope
     * @param {string} scope - 'national', 'regional', 'statewide', 'divisional', 'county', 'city'
     * @param {string|number} locId - location ID
     * @returns {string} - formatted location ID
     */
    getDataLocationId(scope, locId, urlId = false) {
        let dataLocId = locId;
        const geState = isStateToNational(scope);
        const isDiv = isDivisional(scope);

        if (geState || isDiv){
            const numId = Number(locId);
            if (!Number.isFinite(numId)) {
                throw new Error('Invalid numeric location ID');
            }

            // divisional IDs for state IDs < 10 require a leading zero (so, numId isn't valid for those)
            if (!isDiv && urlId) return numId;

            if (geState) {
                dataLocId = String(numId).padStart(3, '0') + '00';
            } else {
                dataLocId = String(numId).padStart(4, '0');
            }
        }

        return this.#validateLocId(scope, dataLocId);
    }

    #validateLocId(scope, locId) {
        const str = String(locId).toUpperCase();

        const patterns = {
            national:   /^\d{3}00$/,        // (e.g., '11000')
            regional:   /^\d{3}00$/,        // (e.g., '10300')
            statewide:  /^\d{3}00$/,        // (e.g., '00100')
            divisional: /^\d{4}$/,          // (e.g., '0101')
            county:     /^[A-Z]{2}-\d{3}$/, // (e.g., 'FL-073')
            city:       /^[A-Z0-9]{11}$/    // (e.g., 'USW00093805')
        };

        const pattern = patterns[scope];

        if (!pattern || !pattern.test(str)) {
            throw new Error(`Invalid location ID for scope "${scope}"`);
        }

        if (['__proto__', 'constructor', 'prototype'].includes(str)) {
            throw new Error('Invalid location ID');
        }

        return str;
    }
}
