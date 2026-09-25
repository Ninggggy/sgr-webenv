export class LinearModel {
    constructor() {}

    getSlopeIntercept(data, begTrendYear, endTrendYear) {
        const keys = Object.keys(data);
        const firstYear = keys.reduce((min, k) => Math.min(min, parseInt(k.substring(0, 4))), Infinity);
        const lastYear = keys.reduce((max, k) => Math.max(max, parseInt(k.substring(0, 4))), -Infinity);

        const filtered = Object.fromEntries(
            Object.entries(data).filter(([date, value]) => {
                const year = parseInt(date.substring(0, 4));
                return (
                    year >= firstYear &&
                    year <= lastYear &&
                    year >= begTrendYear &&
                    year <= endTrendYear
                );
            })
        );

        const slopeIntercept = this.#leastSquares(filtered);

        slopeIntercept.begTrendyear = Math.max(firstYear, begTrendYear);
        slopeIntercept.endTrendyear = Math.min(lastYear, endTrendYear);

        return slopeIntercept;
    }

    // #private
    // These are units/year.
    // Multiply by 10 or 100 if per decade or century; and by 12 if all months is selected.
    #leastSquares(values) {
        let count = 0;
        let xSum = 0;
        let ySum = 0;
        let xxSum = 0;
        let xySum = 0;
        let yySum = 0;

        /**
         * Reindex array using values (sans date keys)
         * since "All Months" uses non-sequential x-values
         * (e.g., 202211, 202212, 202301, 202302...)
         */
        const valueArray = Object.values(values);

        valueArray.forEach((value, index) => {
            if (value === null || value === undefined) return;

            xSum += index;
            ySum += value;
            xySum += index * value;
            xxSum += index * index;
            yySum += value * value;
            count++;
        });

        if (count <= 1) {
            return { m: 0, b: 0, ciLower: null, ciUpper: null };
        }

        // Helper variables for Sum of Squares
        const S_xx = xxSum - (xSum * xSum) / count;
        const S_yy = yySum - (ySum * ySum) / count;
        const S_xy = xySum - (xSum * ySum) / count;

        const slope = S_xy / S_xx;
        const intercept = (ySum - slope * xSum) / count;

        let ciLower = null;
        let ciUpper = null;

        // Confidence interval calculation requires at least 3 points
        // because the degrees of freedom in the denominator is (count - 2)
        if (count > 2) {
            let se2 = (S_yy - slope * S_xy) / (count - 2);
            
            // Safeguard against tiny negative numbers caused by JS floating point math
            se2 = Math.max(0, se2);

            // sigmab formula
            const sigmab = Math.sqrt(se2 / S_xx);

            // 95% confidence interval
            ciLower = slope - 1.96 * sigmab;
            ciUpper = slope + 1.96 * sigmab;
        }

        return { m: slope, b: intercept, ciLower, ciUpper };
    }

    /**
     * 
     * @param {object} timeSeries timescale averaged data
     * @param {number|string} minDate beginning of period of record
     * @param {number|string} maxDate end of period of record
     * @param {object} slopeIntercept calculated trend: begTrendYear, endTrendYear, slope (m), intercept (b)
     * @returns values of trend line
     */
    getTrendValues(timeSeries, minDate, maxDate, slopeIntercept) {
        if (!timeSeries || Object.keys(timeSeries).length === 0) {
            return {};
        }

        const { m, b } = slopeIntercept;
        let { begTrendyear, endTrendyear } = slopeIntercept;

        const minYear = String(minDate).substring(0, 4);
        const maxYear = String(maxDate).substring(0, 4);

        if (begTrendyear < minYear) begTrendyear = minYear;
        if (endTrendyear > maxYear) endTrendyear = maxYear;

        /**
         * Slope & intercept are calculated with a zero-based index because of the non-sequential nature of monthly data
         * (...198412, 198501...). Thus, a zero-based index (using array_values) is used to calculate the trend values
         * and the date keys are added back in after calculations.
         */
        const dates = Object.keys(timeSeries).sort();

        /**
         * National Data
         *
         * Use separate index (trendNdx) for when begTrendyear does not equal
         * national beg date (/monitoring-content/cag/metadata/beg-dates.json).
         *
         * All Time Series begin at the national beg date (/monitoring-content/cag/metadata/beg-dates.json). Some city
         * data begin at a later date. Therefore, it is necessary to have a separate index (trendNdx) for when data
         * actually begin, which makes trend line values accurate.
         */
        const begDate = Math.min(...dates);
        const endDate = Math.max(...dates);
        const begYear = parseInt(String(begDate).slice(0, 4), 10);

        let trendNdx = (begYear > minYear ? begYear : minYear) - begTrendyear;

        /**
        const trendValues = new Map();

        dates.forEach((date, ndx) => {
            const year = parseInt(String(date).slice(0, 4), 10);

            const inRange =
                year >= begTrendyear &&
                year <= endTrendyear &&
                date >= begDate &&
                date <= endDate;

            trendValues.set(date, inRange ? trendNdx * m + b : null);

            if (year >= minYear) trendNdx++;
        });
        /**/
        /**/
        const trendValues = {};

        Object.values(timeSeries).forEach((value, ndx) => {
            const date = dates[ndx];
            const year = parseInt(String(date).slice(0, 4), 10);

            const inRange =
            year >= begTrendyear &&
            year <= endTrendyear &&
            date >= begDate &&
            date <= endDate;

            trendValues[date] = inRange ? trendNdx * m + b : null;

            if (year >= minYear) trendNdx++;
        });
        /**/

        return trendValues;
    }
}