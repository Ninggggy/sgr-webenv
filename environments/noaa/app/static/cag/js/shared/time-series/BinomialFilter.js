import { incrementDate } from "../../utils/date-key-utils.js";

export class BinomialFilter {
    constructor() {}

    /**
     * Smooths the data using a binomial filter.
     * @param {Object} data - An object with date-like keys and numeric/null values.
     * @param {number} numPoints - Odd number >= 3 for smoothing window size.
     * @returns {Object} - x-point binomial filtered series with the same keys and nulls preserved.
     */
    smooth(data, numPoints) {
        if (numPoints % 2 !== 1 || numPoints < 3) {
            return data;
        }

        const filteredData = this.getFilteredData(data, numPoints);

        // return filtered data with same index as data
        const keys = Object.keys(data).sort();
        const monthly = keys[0].length === 6;
        const result = {};
        let i = 0;

        let date = keys[0];
        const endDate = keys[keys.length - 1];

        while (date <= endDate) {
            result[date] = data[date] !== undefined && data[date] !== null ? filteredData[i++] : null;

            date = incrementDate(date, monthly);
        }

        return result;
    }

    /**
     * Generate filtered values from non-null input data using binomial weights.
     * assume persistent end point values
     * @private
     */
    getFilteredData(data, numPoints) {
        const nonNullData = Object.values(data).filter((v) => v !== null);
        const weights = this.getWeights(numPoints);
        const filtered = [];

        for (let i = 0; i < nonNullData.length; i++) {
            let sum = nonNullData[i] * weights[0];

            for (let j = 1; j <= (numPoints - 1) / 2; j++) {
                const left = Math.max(i - j, 0);
                const right = Math.min(i + j, nonNullData.length - 1);
                sum += nonNullData[left] * weights[j];
                sum += nonNullData[right] * weights[j];
            }

            filtered[i] = sum;
        }

        return filtered;
    }

    /**
     * Computes normalized binomial weights.
     * @private
     */
    getWeights(numPoints) {
        const binomialRow = this.getBinomialRow(numPoints);
        const sum = binomialRow.reduce((a, b) => a + b, 0);
        const weights = [];

        for (let i = Math.floor(numPoints / 2); i >= 0; i--) {
            weights.push(binomialRow[i] / sum);
        }

        return weights;
    }

    /**
     * Calculates binomial coefficients for row n of Pascal's triangle.
     * @private
     */
    getBinomialRow(n) {
        const row = [1];
        for (let k = 1; k < n; k++) {
            row[k] = (row[k - 1] * (n - k)) / k;
        }
        return row;
    }
}
