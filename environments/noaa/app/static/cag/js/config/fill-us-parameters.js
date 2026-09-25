import { cag, scope, section } from '../globals.js';
import Util from '../utils/util.js';

const isCity    = Util.scope.is.city;
const isHaywood = Util.section.is.haywood;

const {
    degreeDay:  isDegreeDay,
    palmer:     isPalmer,
    nonZPalmer: isNonZPalmer
} = Util.parameter.is;

const {
    alaska: isAlaska,
    hawaii: isHawaii,
    agBelt: isAgBelt,
    riverBasin: isRiverBasin
} = Util.location.withContext(scope, section).is;

export function fillUsParameters() {
    const parameters = cag.constants.parameters;
    const $parameterElem = $('#parameter');
    const selectedParameter = $parameterElem.val() || cag.variables.parameter;
    const selectedLocation = $('#location').val();

    const isMiscRgns = (loc) => [111, 115, 120].includes(Number(loc));

    const fragment = document.createDocumentFragment();
    Object.entries(parameters).forEach(([param, attr]) => {
        // 1. Haywood: Skip Non-Z-Index Palmers (PDSI, PHDI, PMDI)
        if (isHaywood(section) && isNonZPalmer(param)) return;

        // 2. Degree Days not provided for Cities, AK, HI, River Basins, Misc Regions, or Ag Belts
        if (
            isDegreeDay(param) &&
            (
                isCity(scope) ||
                isAlaska(selectedLocation) ||
                isHawaii(selectedLocation) ||
                isRiverBasin(selectedLocation) ||
                isMiscRgns(selectedLocation) ||
                isAgBelt(selectedLocation)
            )
        ) return;

        // 3. Palmers not available for cities, AK, or HI
        if (
            isPalmer(param) &&
            (
                isCity(scope) ||
                isAlaska(selectedLocation) ||
                isHawaii(selectedLocation)
            )
        ) return;

        const option = document.createElement('option');
        option.value = param;
        option.textContent = attr['title'];
        fragment.appendChild(option);
    });

    $parameterElem.empty().append(fragment);
    if ($parameterElem.find(`option[value="${selectedParameter}"]`).length > 0) {
        $parameterElem.val(selectedParameter);
    }
    $parameterElem.trigger('change');
}
