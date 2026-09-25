const getStateId = (locations, location) =>
    locations?.[location]?.stateId ?? null;

const getStateName = (usStates, locations, location) => {
    const id = getStateId(locations, location);
    return id && usStates?.[id]?.name ? usStates[id].name : '';
};

const getLocationName = (locations, location) =>
    locations?.[location]?.name?.replace(' Climate Region', '') ?? '';

export function getUsTitle(scope, usStates, locations, location) {
    let title = '';

    if (scope === 'divisional') {
        const division = parseInt(String(location).slice(-2));
        title = `${getStateName(usStates, locations, location)}, Climate Division ${isNaN(division) ? '' : division}`;
    } else {
        title = getLocationName(locations, location);
        if (['county', 'city'].includes(scope)) {
            title += `, ${getStateName(usStates, locations, location)}`;
        }
    }

    return title.trim();
}

export function getGlobalTitle(regions, surfaces, region, lat, lon, surface) {
    if (region === 'coords') {
        return `${Math.abs(lat)}°${lat < 0 ? 'S' : 'N'}, ${Math.abs(lon)}°${lon < 0 ? 'W' : 'E'}`;
    }

    const title = regions?.[region]?.title ?? '';
    if (['globe', 'nhem', 'shem'].includes(region)) {
        return `${title} ${surfaces?.[surface] ?? ''}`.trim();
    }

    return title;
}
