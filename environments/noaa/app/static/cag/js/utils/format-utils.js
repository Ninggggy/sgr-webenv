/**
 * Converts a string or number into a numeric value.
 *
 * - Removes thousands separators (commas).
 * - Validates that the cleaned string is a properly formatted number
 *   (optional leading "-", optional decimal part).
 * - Returns the parsed number if valid, otherwise NaN.
 *
 * Examples:
 *   toNumber("1,234.56") → 1234.56
 *   toNumber("-42")      → -42
 *   toNumber("12abc")    → NaN
 *
 * @param {string|number} val - The input value to convert.
 * @returns {number} The parsed number, or NaN if invalid.
 */
const toNumber = (val) => {
    const str = String(val).replace(/,/g, "");
    if (!/^-?\d+(\.\d+)?$/.test(str)) return NaN;
    return Number(str);
};

const FormatUtil = {
   toNumber,

    /**
     * Format a number with commas and optional decimal precision.
     * @param {string|number} input 
     * @param {number} precision 
     * @returns {string|null}
     */
    number: (input, precision = 0, thousandsSeparator = ',') => {
        const num = toNumber(input);
        if (isNaN(num)) return null;

        let safeNum = Object.is(num, -0) ? 0 : num;

        // more accurate rounding than toFixed
        const accurateNum = Number(Math.round(safeNum + "e+" + precision) + "e-" + precision);
        // return string with any potential trailing zeros
        const fixed = accurateNum.toFixed(precision);
        const parts = fixed.split('.');

        if (thousandsSeparator) {
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
        }

        return parts.join('.');
    }
};

export default FormatUtil;
