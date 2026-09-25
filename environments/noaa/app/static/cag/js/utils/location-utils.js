import SectionUtil from "./section-utils.js";
import ScopeUtil from "./scope-utils.js";

const isMapping = SectionUtil.is.mapping;
const { statewide: isStatewide, divisional: isDivisional, county: isCounty } = ScopeUtil.is;
const CLIMATE_REGIONS = new Set(Array.from({ length: 9 }, (_, i) => 101 + i));
const NWS_REGIONS = new Set(Array.from({ length: 4 }, (_, i) => 121 + i));
const RIVER_BASINS = new Set(Array.from({ length: 18 }, (_, i) => 201 + i));
const AG_BELTS = new Set([
    ...Array.from({ length: 16 }, (_, i) => 250 + i),
    ...Array.from({ length: 16 }, (_, i) => 350 + i)
]);
const MISC_REGIONS = new Set(Array.from({ length: 10 }, (_, i) => 111 + i));

const isSomeState = (stateId, stateAbbr) => (scope, section, locationId) => {
    const id = String(locationId);

    return (
        (isStatewide(scope) && id === stateId) ||
        (isDivisional(scope) && id.slice(0, -2) === stateId) ||
        (isMapping(section) && id === stateId) ||
        (!isMapping(section) && isCounty(scope) && id.startsWith(stateAbbr))
    );
};

const isSomeRegion = (section, locationId, regionIdList, mappingRegionsId) => {
    const numLoc = Number(locationId);
    return (!isMapping(section) && regionIdList.has(numLoc)) || (isMapping(section) && numLoc === mappingRegionsId);
}

const LocationUtil = {
    is:{
        louisiana: isSomeState('16', 'LA'),
        maryland: isSomeState('18', 'MD'),
        alaska: isSomeState('50', 'AK'),
        hawaii: isSomeState('51', 'HI'),
        puertoRico: isSomeState('66', 'PR'),
        dc: isSomeState('49', 'DC'),
        conusState: (scope, section, locationId) => locationId <= 48,
        conus: (scope, section, locationId) => String(locationId) === '110',
        agBelt: (scope, section, locationId) => {
            const numLoc = Number(locationId);
            return AG_BELTS.has(numLoc);
        },
        miscRegion: (scope, section, locationId) => {
            const numLoc = Number(locationId);
            return MISC_REGIONS.has(numLoc);
        },
        climateRegion: (scope, section, locationId) => {
            return isSomeRegion(section, locationId, CLIMATE_REGIONS, -1);
        },
        nwsRegion: (scope, section, locationId) => {
            return isSomeRegion(section, locationId, NWS_REGIONS, -2);
        },
        riverBasin: (scope, section, locationId) => {
            return isSomeRegion(section, locationId, RIVER_BASINS, -3);
        }
    }
};

LocationUtil.withContext = (scope, section) => ({
    is: Object.fromEntries(
        Object.entries(LocationUtil.is).map(([key, fn]) => [
            key,
            (...args) => fn(scope, section, ...args)
        ])
    )
});

export default LocationUtil;