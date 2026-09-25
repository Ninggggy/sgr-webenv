import { cag } from '../globals.js';

const sets = {
    precip: new Set(['pcp']),
    palmer: new Set(['pdsi', 'phdi', 'pmdi', 'zndx']),
    degreeDay: new Set(['cdd', 'hdd']),
    temp: new Set(['tavg', 'tmax', 'tmin']),
};

sets.nonZPalmer = new Set([...sets.palmer].filter(p => p !== 'zndx'));

const ParameterUtil = {
    is: {
        precip:     param => sets.precip.has(param),
        palmer:     param => sets.palmer.has(param),
        nonZPalmer: param => sets.nonZPalmer.has(param),
        degreeDay:  param => sets.degreeDay.has(param),
        temp:       param => sets.temp.has(param),
        coldToHot:  param => sets.temp.has(param),
        dryToWet:   param => sets.precip.has(param) || sets.palmer.has(param),
    },
    // return parameter metadata value
    metaVal: (attr, param = cag.variables.parameter, params = cag.constants.parameters) =>
        params?.[param]?.[attr] ?? ''
};

export default ParameterUtil;
