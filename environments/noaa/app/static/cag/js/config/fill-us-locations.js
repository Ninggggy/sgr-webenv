import { cag, section, scope } from '../globals.js';
import { fillUsParameters } from './fill-us-parameters.js';
import { initYearRange } from '../shared/year-ranges.js';
import Util from '../utils/util.js';

const {
    national:   isNational,
    statewide:  isStatewide,
    divisional: isDivisional,
    county:     isCounty,
    city:       isCity,
    substate:   isSubstate
} = Util.scope.is;
const isMapping = Util.section.is.mapping;

export function fillUsStates() {
    const $elem = $('#state');
    let options = [];

    Object.entries(cag.constants.usStates).forEach(([stId, stateAttr]) => {
        const stateId   = parseInt(stId);
        const stateName = escapeHtml(stateAttr.name);

        if (skipState(stateId)) return;
        options.push({ stateId, stateName });
    });

    // sort by name
    options.sort((a, b) => {
        return a.stateName.localeCompare(b.stateName);
    });

    $elem.empty();
    options.forEach(({ stateId, stateName }) => {
        $elem.append(`<option value="${stateId}">${stateName}</option>`);
    });

    const selected = $elem.find(`option[value="${cag.variables.state}"]`).length > 0
        ? cag.variables.state
        : Object.keys(cag.constants.usStates)[0];
    $elem.val(selected);
}

export function fillUsLocations() {
    const $location = $('#location');
    const $label = $('label[for=location]');
    const $locationOptions = $('#location-options');
    const $stateOptions = $('#state-options');
    const selectedState = parseInt($('#state').val());
    $location.empty();

    if (isMapping(section)) {
        if (isNational(scope)) {
            $locationOptions.hide();
        } else {
            $locationOptions.show();
            const labelMap = {
                regional: 'Region(s):',
                statewide: 'State:',
                divisional: 'State:',
                county: 'State:',
                city: 'State:'
            };
            $label.text(labelMap[scope] || 'Location:');
        }
    } else {
        switch (scope) {
            case 'national':
                $stateOptions.hide();
                $location.html(`<option value="110">Contiguous U.S.</option>`);
                $('#location').val(110);
                $('#location-options').hide();
                fillUsParameters();
                return true;
            case 'regional':
                $stateOptions.hide();
                $label.text('Region:');
                break;
            case 'statewide':
                $stateOptions.hide();
                $label.text('State:');
                break;
            case 'divisional':
                $stateOptions.show();
                $label.text('Division:');
                break;
            case 'county':
            case 'city':
                $stateOptions.show();
                $label.text(`${scope.charAt(0).toUpperCase()}${scope.slice(1)}:`);
                break;
        }
    }

    // Containers for options: ungrouped options will be alphabetized,
    // while grouped options (with an optGroup property) preserve insertion order.
    const ungroupedOptions = [];
    const groupedOptions = {}; // { groupLabel: [ { locId, locationName }, ... ] }
    const optGroupOrder = [];  // preserves the order optGroup labels are encountered
    const locations = cag.constants.locations;

    for (const locId in locations) {
        const locData = locations[locId];

        if (isMapping(section)) {
            if (
                // if statewide, divisional, county, skip CONUS, DC, and PR
                (
                    ['statewide', 'divisional', 'county'].includes(scope) &&
                    ((locId == 49 || locId > 51) && locId != 110)
                ) ||
                // if city, and state not represented
                (
                    isCity(scope) &&
                    !Object.values(cag.constants.usCities).some(city => city.stateId == locId) &&
                    locId != 110
                )
            ) {
                continue;
            }
        } else {
            const stateId = parseInt(('stateId' in locData) ? locData.stateId : locId);
            if (skipState(stateId, selectedState)) continue;
        }

        // If divisional, prefix the name with the last two digits of locId
        const locationName =
            (isDivisional(scope) && !isMapping(section) ? `${parseInt(String(locId).slice(-2))}. ` : '') +
            (locData.name || locData);

        const optionObj = { locId, locationName };

        if (locData.regionGroup && locData.regionGroup !== '') {
            optionObj.optGroup = locData.regionGroup;
            if (!groupedOptions[locData.regionGroup]) {
                groupedOptions[locData.regionGroup] = [];
                optGroupOrder.push(locData.regionGroup); // record the order of appearance
            }
            groupedOptions[locData.regionGroup].push(optionObj);
        } else {
            ungroupedOptions.push(optionObj);
        }
    }

    // Only alphabetize ungrouped options.
    ungroupedOptions.sort((a, b) => {
        const regex = /^(\d+)\. /;
        const numA = a.locationName.match(regex);
        const numB = b.locationName.match(regex);
        if (numA && numB) {
            return parseInt(numA[1]) - parseInt(numB[1]);
        }
        return a.locationName.localeCompare(b.locationName);
    });

    // Append ungrouped options (110 CONUS, first)
    ungroupedOptions.sort((a, b) => {
        if (a.locId == 110) return -1;
        if (b.locId == 110) return 1;
        return 0;
    });
    ungroupedOptions.forEach(({ locId, locationName }) => {
        $location.append(`<option value="${locId}">${locationName}</option>`);
    });
      
    // Append grouped options in the order they were encountered; do not sort them.
    optGroupOrder.forEach((groupLabel) => {
        const $optgroup = $(`<optgroup label="${groupLabel}"></optgroup>`);
        groupedOptions[groupLabel].forEach(({ locId, locationName }) => {
            $optgroup.append(`<option value="${locId}">${locationName}</option>`);
        });
        $location.append($optgroup);
    });

    $location.off('change.locUpdate').on('change.locUpdate', function(e) {
        fillUsParameters();
        if (section !== 'haywood') {
            initYearRange(this.value);
        }
    });

    // Select the current location if it exists and trigger change.
    if ($location.find(`option[value="${cag.variables.locationId}"]`).length > 0) {
        $location.val(cag.variables.locationId);
    }

    document.getElementById('location').dispatchEvent(new Event('change', { bubbles: true }));
}

function skipState(stateId, selectedState = null) {
    return (
        // if statewide or divisional, skip DC & PR
        (
          (isStatewide(scope) || isDivisional(scope)) &&
          (stateId == 49 || stateId == 66)
        ) ||
        // if county, skip PR
        (isCounty(scope) && stateId == 66) ||
        // if city, and state not represented in usCities
        (
            isCity(scope) &&
            !Object.values(cag.constants.usCities).map(city => city.stateId).includes(stateId)
        ) ||
        // if divisional, county, or city, selected state has to match
        (selectedState !== null && isSubstate(scope) && stateId != selectedState)
    );
}