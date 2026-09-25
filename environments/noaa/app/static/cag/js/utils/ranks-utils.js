import { insufficientVariability } from "./insufficient-variability.js"

const percentiles = [
    'lowest',
    'bottom-tenth',
    'bottom-third',
    'normal',
    'top-third',
    'top-tenth',
    'highest'
];
const thresholds = (numYears) => {
    const bottom10 = Math.round(numYears / 10);
    const bottom33 = Math.round(numYears / 3);

    const top10lower = numYears - bottom10 + 1;
    const top33Lower = numYears - bottom33 + 1;

    return [
        1,
        2,
        bottom10 + 1, // start after bottom 10%
        bottom33 + 1, // start after bottom 33%
        top33Lower,   // start of top 33%
        top10lower,   // start of top 10%
        numYears      // max
    ];
}

const thresholdIndex = (rank, numYears) => {
    const rankThresholds = thresholds(numYears);
    for (let ndx = rankThresholds.length-1; ndx >= 0; ndx--) {
        if (rank >= rankThresholds[ndx]) {
            return ndx;
        }
    }
    return -1;
}

const RanksUtil = {
    percentiles,
    thresholds,
    thresholdIndex,
    percentile: (parameter, rank, numYears) => {
        const list = (parameter === 'hdd')
            ? [...percentiles].reverse()
            : percentiles;

        const ndx = thresholdIndex(rank, numYears);
        return ndx >= 0 ? list[ndx] : 'lowest';
    },

    tiesNumerousRecords: (rank, ties, numYrs) => {
        return (
            (rank == 1 || rank == numYrs) &&
            insufficientVariability(ties, numYrs)
        );
    }
};

export default RanksUtil;
