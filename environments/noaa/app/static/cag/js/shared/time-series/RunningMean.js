export class RunningMean {
    getRunningMean(values, run) {
        const keys = Object.keys(values).sort();
        const result = {};
        const firstYear = parseInt(String(keys[0]).slice(0, 4)) + (run - 1);

        for (const key of keys) {
            const year = parseInt(String(key).slice(0, 4));
            const month = key.length === 6 ? String(key).slice(-2) : '';
            if (year < firstYear) {
                result[key] = null;
                continue;
            }

            let sum = 0;
            let count = 0;

            for (let ry = year - (run - 1); ry <= year; ry++) {
                const runKey = `${ry}${month}`;
                if (values.hasOwnProperty(runKey) && values[runKey] !== null) {
                    sum += values[runKey];
                    count++;
                } else if (ry === year - (run - 1)) {
                    break;
                }
            }

            result[key] = count > 0 ? sum / count : null;
        }

        return result;
    }
}
