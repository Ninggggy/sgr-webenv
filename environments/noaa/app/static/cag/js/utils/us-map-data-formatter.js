/**
 * Processes and formats map data for city locations into a GeoJSON FeatureCollection.
 * This is suitable for plotting points on a map.
 *
 * @param {object} data - The raw data object containing value, rank, anomaly, etc., keyed by cityId.
 * @param {object} parameters - Configuration object for parameters.
 * @param {string} parameter - The key for the specific parameter being processed.
 * @param {object} cities - An object containing city details (name, stateId, lon, lat), keyed by cityId.
 * @param {object} usStates - An object containing US state details (name, abbr), keyed by stateId.
 * @returns {object} A GeoJSON FeatureCollection object.
 */
const getCityMapData = async (data, cities, usStates, precision) => {
    const geoJson = { type: 'FeatureCollection', features: [] };

    const keys = Object.keys(data);
    if (!keys.length) return geoJson;

    const cityIds = Object.keys(data[keys[0]]);
    const roundToPrecision = num => Number(parseFloat(num).toFixed(precision));

    for (const cityId of cityIds) {
        const cityInfo = cities[cityId];
        const val = data.value?.[cityId];
        if (val == null || !cityInfo) continue;

        const rawRank = data.rank[cityId];
        const rank = Math.floor(rawRank);
        const ties = parseInt((rawRank - rank).toFixed(4).substring(2), 10);

        const stateInfo = usStates[cityInfo.stateId];

        geoJson.features.push({
            type: 'Feature',
            ghcnId: cityId,
            properties: {
                name: cityInfo.name,
                stateName: stateInfo?.name,
                stateAbbr: stateInfo?.abbr,
                ghcnId: cityId,
                value: roundToPrecision(val),
                rank,
                ties,
                anomaly: roundToPrecision(data.anomaly[cityId]),
                pctavg: data.pctavg?.[cityId] ?? null,
                mean: roundToPrecision(data.mean[cityId]),
            },
            geometry: {
                type: 'Point',
                coordinates: [cityInfo.lon, cityInfo.lat],
            },
        });
    }

    return geoJson;
};

/**
 * Processes and formats map data for non-city scopes (e.g., county, divisional, state).
 *
 * @param {string} scope - The geographic scope (e.g., 'divisional', 'county').
 * @param {object} data - The raw data object containing value, rank, anomaly, etc., keyed by locationId.
 * @param {object} parameters - Configuration object for parameters.
 * @param {string} parameter - The key for the specific parameter being processed.
 * @param {object} locations - An object containing location details (name, stateId, centroid), keyed by locationId.
 * @param {object} usStates - An object containing US state details (name, abbr), keyed by stateId.
 * @returns {object} An object containing the processed map data, keyed by locationId.
 */
const getNonCityMapData = async (scope, data, locations, usStates, precision) => {
    const mapJson = {};

    const keys = Object.keys(data);
    if (!keys.length) return mapJson;

    // Get location IDs from the first data category
    const locationIds = Object.keys(data[keys[0]]);
    const roundToPrecision = num => Number(parseFloat(num).toFixed(precision));

    for (const locationId of locationIds) {
        const locationInfo = locations[locationId];
        const val = data.value?.[locationId];

        // Skip invalid or missing locations
        if (val == null || !locationInfo) continue;

        // Determine stateId
        const stateId = scope === 'divisional'
            ? parseInt(String(locationId).slice(0, -2), 10)
            : locationInfo.stateId ?? false;

        // Divisional key → integer, others → string
        const key = scope === 'divisional'
            ? parseInt(locationId, 10)
            : locationId;

        const rawRank = data.rank[locationId];
        const rank = Math.floor(rawRank);
        const ties = parseInt((rawRank - rank).toFixed(4).substring(2), 10);

        mapJson[key] = {
            name: locationInfo.name,
            value: roundToPrecision(val),
            rank,
            ties,
            anomaly: roundToPrecision(data.anomaly[locationId]),
            pctavg: data.pctavg?.[locationId] ?? null,
            mean: roundToPrecision(data.mean[locationId]),
            centroid: { ...locationInfo.centroid },
        };

        if (stateId && usStates[stateId]) {
            mapJson[key].stateName = usStates[stateId].name;
            mapJson[key].stateAbbr = usStates[stateId].abbr;
        }
    }

    return mapJson;
};

/**
 * Main router function to configure map data based on the specified scope.
 * This function is exported and can be imported into other parts of a JS application.
 *
 * @param {string} scope - The geographic scope ('city', 'county', 'divisional', etc.).
 * @param {object} data - The raw data object.
 * @param {int} precision - The number of decimals to be used in rounding data.
 * @param {object} locations - Object containing location details (cities, counties, etc.), keyed by ID.
 * @param {object} usStates - Object containing US state details, keyed by stateId.
 * @returns {object} The configured map data object, either as GeoJSON (for cities) or a keyed object.
 */
export const configMapData = async (scope, data, locations, usStates, precision) => {
    if (!data || Object.keys(data).length === 0) {
        console.error('US Mapping data empty, cannot configure');
        return [];
    }

    // This is the main entry point. It checks the scope and calls the appropriate helper function.
    // The `locations` parameter is used for both cities and other locations.
    return scope === 'city'
        ? await getCityMapData(data, locations, usStates, precision)
        : await getNonCityMapData(scope, data, locations, usStates, precision);
};
