const TimeSeriesTitleUtil = {
    getGlobalTitle: (
        parameters,
        parameter,
        regions,
        region,
        lat,
        lon,
        surfaces,
        surface,
        short = false
    ) => {
        let title;

        if (region === 'coords') {
            const latNS = lat < 0 ? 'S' : 'N';
            const lonEW = lon < 0 ? 'W' : 'E';
            const formattedLat = Math.abs(lat).toFixed(1);
            const formattedLon = Math.abs(lon).toFixed(1);
            title = `${formattedLat}°${latNS}, ${formattedLon}°${lonEW}`;
        } else {
            title = regions[region].title;

            const surfaceList = regions[region].surfaces;
            const hasMultipleSurfaces = surfaceList.length > 1;

            if (
                hasMultipleSurfaces &&
                (!short || (short && surface !== 'land_ocean'))
            ) {
                title += ` ${surfaces[surface]}`;
            }
        }

        title += ` ${parameters[parameter][short ? 'shortTitle' : 'title']}`;

        /*
        if (parameter === 'tavg') {
            title += short ? ' Dept' : ' Departures';
        }
        */

        return title;
    },

    getUsTitle: (scope, locations, locationId, parameters, parameter, usStates, short = false) => {
        let title;

        if (scope === 'divisional') {
            const stateId = locations[locationId]['stateId'];
            const stateName = usStates[stateId][short ? 'abbr' : 'name'];
            const divisionNumber = parseInt(String(locationId).slice(-2), 10);
            title = `${stateName}, ${short ? 'CD' : 'Climate Division'} ${divisionNumber}`;
        } else {
            title = locations[locationId]['name'].replace(' Climate Region', '');
            
            if (scope === 'county' || scope === 'city') {
                const stateId = locations[locationId]['stateId'];
                const stateName = usStates[stateId][short ? 'abbr' : 'name'];
                title += `, ${stateName}`;
            }
        }

        title += ` ${parameters[parameter][short ? 'shortTitle' : 'title']}`;

        return title;
    },

    getDateSpan: (timescale, month, short = false) => {
        let datespan = '';

        if (timescale === 'ytd' && month !== 1) {
            datespan = (month == 0 ? 'Year-to-Date' : 'January-');
        } else if (month > 0 && timescale > 1 && timescale <= 12) {
            // Calculate the starting month of the range
            const startMonth = month - timescale + 1;
            const date = new Date(2000, startMonth - 1, 10);
            datespan = `${date.toLocaleString('default', { month: 'long' })}-`;
        } else if (
            timescale !== 'ytd' &&
            ((month == 0 && timescale > 1) || timescale > 12)
        ) {
            datespan = `${timescale}-Month${short ? 's' : ' Period'}`;
            if (month > 0) {
                datespan += ' Ending ';
                if (!short) {
                    datespan += 'in ';
                }
            }
        }

        if (month > 0) {
            const endDate = new Date(2000, month - 1, 10);
            datespan += endDate.toLocaleString('default', { month: 'long' });
        }

        return datespan;
    }
};

export default TimeSeriesTitleUtil;
