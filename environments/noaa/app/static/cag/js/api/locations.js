import { cag } from '../globals.js';

async function fetchJson(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`Failed to load ${path}`);
    return res.json();
}

export async function getLocations(scope) {
    let locations;

    switch (scope) {
        case "global":
            locations = JSON.parse(JSON.stringify(cag.constants.globalRegions)); // clone
            break;
        case "national":
            locations = JSON.parse(JSON.stringify(cag.constants.conus)); // clone
            break;
        case "regional":
            locations = await processRegional(cag.constants.usRegions, cag.constants.usStates);
            break;
        case "statewide":
            locations = JSON.parse(JSON.stringify(cag.constants.usStates)); // clone
            break;
        case "divisional":
            locations = await processDivisional(cag.constants.usClimateDivisions, cag.constants.usStates);
            break;
        case "county":
            locations = JSON.parse(JSON.stringify(cag.constants.usCounties)); // clone
            break;
        case "city":
            locations = await processCity(cag.constants.usCities, cag.constants.usStates, cag.constants.minDates);
            break;
    }

    // Remove unwanted keys
    const keysToRemove = ["centroid", "center", "bounds", "zoom", "regionGroupId", "oldName", "lats"];
    locations = Object.fromEntries(
        Object.entries(locations).map(([id, loc]) => {
            keysToRemove.forEach(k => delete loc[k]);
            return [id, loc];
        })
    );

    return locations;
}

async function processRegional(locations, usStates) {
    let maps = [];
    const mapFile = "/monitoring-content/monitoring-references/maps/metadata/maps.json";
    try {
        maps = await fetchJson(mapFile);
    } catch (err) {
        console.warn(`Missing ${mapFile}`);
    }

    for (const id in locations) {
        const region = locations[id];
        if (region.stateIds) {
            region.states = Object.fromEntries(
                region.stateIds.map(stateId => [stateId, usStates[stateId]?.abbr || ""])
            );
            delete region.stateIds;
        } else {
            for (const attr of Object.values(maps)) {
                if (attr.regions?.[id]?.climateDivisions) {
                    region.climateDivisions = attr.regions[id].climateDivisions;
                    break;
                }
            }
        }
    }
    return locations;
}

async function processDivisional(locations, usStates) {
    const newLocs = {};
    Object.entries(locations)
        .sort(([a], [b]) => a.localeCompare(b))
        .forEach(([id, division]) => {
            division.stateAbbr = usStates[division.stateId]?.abbr || "";
            newLocs[id] = division;
        });
    return newLocs;
}

async function processCity(locations, usStates, begDates) {
    for (const id in locations) {
        const city = locations[id];
        city.begdate = parseInt(begDates[id] || begDates["national"]);
        city.stateAbbr = usStates[city.stateId]?.abbr || "";
    }
    return locations;
}
