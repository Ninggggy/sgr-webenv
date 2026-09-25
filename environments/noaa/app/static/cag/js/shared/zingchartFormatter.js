import { cag } from "../globals.js";
import Util from "../utils/util.js";

const conversions  = Util.conversion.conversions;
const toNumber     = Util.format.toNumber;
const paramMetaVal = Util.parameter.metaVal;
const formatNumber = Util.format.number;

const decimals = (x) => x > -100 && x < 100 ? paramMetaVal('precision') : 0;
const separator = (x) => x > 9999 ? ',' : '';

function cagScaleYFormat(val) {
    const num = toNumber(val);
    const units = (paramMetaVal('unitsAbbr') ?? '').replace(/^in$/, '"');
    return formatNumber(num, decimals(num), separator(num)) + units;
}

function cagScaleY2Format(val) {
    const num = toNumber(val);

    const useAnom = (cag.variables.basePeriod && cag.variables.plotDepartures);
    let convKey = paramMetaVal('convType') ?? "identity";

    if (useAnom && (convKey === "fToC" || convKey === "cToF")) {
        convKey += "Anom";
    }
    
    const fn = conversions[convKey] ?? conversions.identity;

    const convVal = fn(num);

    const units = (convKey === "identity"
        ? paramMetaVal('unitsAbbr')
        : (paramMetaVal('units2Abbr') ?? "")).replace(/^in$/, '"');

    return formatNumber(convVal, decimals(convVal), separator(convVal)) + units;
}

function cagRolloverText(p) {
    //const date     = p.scaletext;
    const value    = p.value;
    const dispVal  = formatNumber(value, paramMetaVal('precision'));
    const posColor = paramMetaVal('posHex') ?? paramMetaVal('hex');
    const negColor = Util.scope.is.global(cag.constants.scope) || Util.parameter.is.palmer(cag.variables.parameter) || cag.variables.plotDepartures
        ? paramMetaVal('negHex') ?? paramMetaVal('hex')
        : paramMetaVal('posHex') ?? paramMetaVal('hex');
    const text  = `<strong>${paramMetaVal('shortTitle')}:</strong> `;
    const units = paramMetaVal('unitsAbbr') ?? '';

    return {
        text: `${text}${dispVal}${units}`,
        backgroundColor: (value >= 0 ? posColor : negColor)
    };
};

export { separator };

// attach to window for ZingChart to be able to recognize
if (typeof window !== "undefined") {
    window.cagScaleYFormat = cagScaleYFormat;
    window.cagScaleY2Format = cagScaleY2Format;
    window.cagRolloverText = cagRolloverText;
}