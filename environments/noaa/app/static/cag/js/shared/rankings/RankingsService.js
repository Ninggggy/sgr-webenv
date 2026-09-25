export class RankingsService {
    /**
     * A two-tailed approach to ranking. Sorts low-to-high for the bottom half
     * and high-to-low for the top half, but handles tied values as blocks.
     * @param {object} data - Object with date keys and numeric values.
     * @returns {object} Object with date keys and integer ranks.
     * @private
     */
    async getRanks(data) {
        const ranks = {};

        // Pre-fill null ranks where data values are null (so they are never skipped)
        for (const [key, value] of Object.entries(data)) {
            if (value === null) {
                ranks[key] = null;
            }
        }

        // Count numeric values
        const numVals = Object.values(data).filter(v => typeof v === 'number').length;
        if (numVals === 0) return {};

        // --- Sort lowest to highest ---
        const ascEntries = Object.entries(data).sort(([, a], [, b]) => {
            if (a === null) return 1;
            if (b === null) return -1;
            return a - b;
        });

        let count = 0;
        for (let i = 0; i < ascEntries.length; ) {
            const [ , value ] = ascEntries[i];
            if (value === null) {
                i++;
                continue;
            }

            // Collect block of tied values
            let j = i;
            while (j < ascEntries.length && ascEntries[j][1] === value) {
                j++;
            }

            const loRank = count + 1; // rank starts at first position of block
            for (let k = i; k < j; k++) {
                ranks[ascEntries[k][0]] = loRank;
            }

            count += (j - i);
            if (count > numVals / 2) break; // stop after finishing this block
            i = j;
        }

        // --- Sort highest to lowest ---
        const descEntries = Object.entries(data).sort(([, a], [, b]) => {
            if (a === null) return 1;
            if (b === null) return -1;
            return b - a;
        });

        count = 0;
        for (let i = 0; i < descEntries.length; ) {
            const [ , value ] = descEntries[i];
            if (value === null) {
                i++;
                continue;
            }

            // Collect block of tied values
            let j = i;
            while (j < descEntries.length && descEntries[j][1] === value) {
                j++;
            }

            const hiRank = numVals - count; // rank for the first element in this block
            for (let k = i; k < j; k++) {
                //only assign if not already ranked by ascending
                const date = descEntries[k][0];
                if (!(date in ranks)) {
                    ranks[date] = hiRank;
                }
            }

            count += (j - i);
            if (count >= numVals / 2) break; // stop after finishing this block
            i = j;
        }

        return ranks;
    }

    /** @private */
    async getTies(values, year) {
        const targetValue = values[year];
        if (targetValue === undefined) return [];

        return Object.keys(values).filter(y => y !== year && values[y] === targetValue);
    }
}
