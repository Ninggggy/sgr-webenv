/**
 * Increment a YYYYMM integer by 1 month or YYYY by 1 year
 * @param {number|string} date - e.g. 1977 or 197710
 * @returns {number} - The next month in YYYYMM format or year as YYYY
 */
export function incrementDate(date, monthly) {
    if (monthly) {
        // Expecting YYYYMM
        const year = parseInt(String(date).slice(0, 4), 10);
        const month = parseInt(String(date).slice(4, 6), 10);
        const d = new Date(year, month - 1); // JS months are 0-based
        d.setMonth(d.getMonth() + 1);
        return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}`;
    } else {
        // Expecting year format YYYY
        return (parseInt(date, 10) + 1).toString();
    }
}