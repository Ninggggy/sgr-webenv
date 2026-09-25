export class DataAveragesDao {
    async getDataAverages(parameter, unfilteredData, month, timescale, precision, allMonths = false) {
        // remove null values
        const data = Object.fromEntries(
            Object.entries(unfilteredData).filter(([_, value]) => value !== null)
        );
        if (Object.keys(data).length === 0) {
            console.error('Invalid data for averaging');
            return {};
        }

        const values = {};
        const denominators = {};

        const begMonth = (timescale === 'ytd') ? 1 : month - timescale + 1;
        let adjBegMonth = begMonth;
        let yearsBack = 0;

        while (adjBegMonth < 1) {
            adjBegMonth += 12;
            yearsBack++;
        }

        const keys = Object.keys(data).sort();
        let firstYear = parseInt(String(keys[0]).slice(0, 4)) + yearsBack;
        let lastYear = parseInt(String(keys[keys.length - 1]).slice(0, 4));
        const monthInt = parseInt(month);
        const tsInt = parseInt(timescale);
        const padMonth = m => String(m).padStart(2, '0');

        while (lastYear >= firstYear) {
            const key = `${lastYear}${padMonth(month)}`;
            if (key in data) {
                break; // found it
            }
            lastYear--;
        }

        if (timescale !== 'ytd' && tsInt > 1) {
            let begDate = new Date(firstYear, monthInt - 1, 10);
            begDate.setMonth(begDate.getMonth() - (tsInt - 1));
            let begDateKey = `${begDate.getFullYear()}${padMonth(begDate.getMonth() + 1)}`;

            while (!(begDateKey in data)) {
                firstYear++;
                if (firstYear > lastYear) break;
                begDate = new Date(firstYear, monthInt - 1, 10);
                begDate.setMonth(begDate.getMonth() - (tsInt - 1));
                begDateKey = `${begDate.getFullYear()}${padMonth(begDate.getMonth() + 1)}`;
            }
        }

        for (let year = firstYear; year <= lastYear; year++) {
            const dateKey = allMonths ? `${year}${padMonth(month)}` : String(year);
            denominators[dateKey] = 0;
            const begYear = year - yearsBack;
            let skip = false;

            for (let y = begYear; y <= year; y++) {
                const beg_m = (y === begYear ? adjBegMonth : 1);
                const end_m = (y === year ? month : 12);

                for (let m = beg_m; m <= end_m; m++) {
                    const dataKey = `${y}${padMonth(m)}`;
                    if (data.hasOwnProperty(dataKey) && !skip) {
                        values[dateKey] = (values[dateKey] || 0) + data[dataKey];
                        denominators[dateKey]++;
                    } else {
                        delete values[dateKey];
                        skip = true;
                    }
                }
            }
        }

        const avg = {};
        const isAverage = /^(tavg|tmax|tmin|pdsi|phdi|zndx|MNTM)$/i.test(parameter);
        const denom = timescale === 'ytd' ? month : timescale;

        for (const [key, val] of Object.entries(values)) {
            if (isAverage) {
                if (denominators[key] < denom) continue;
                avg[key] = parseFloat((val / denominators[key]).toFixed(precision));
            } else {
                avg[key] = parseFloat(val.toFixed(precision));
            }
        }

        return avg;
    }

    async getOneMonth(data, month, precision, monthKey = false) {
        const results = {};
        for (const [date, value] of Object.entries(data)) {
            if (parseInt(String(date).slice(4, 6)) === parseInt(month)) {
                const dateKey = monthKey ? date : String(date).slice(0, 4);
                results[dateKey] = value === null ? null : parseFloat(value.toFixed(precision));
            }
        }
        return results;
    }

    async getTimescaleAvg(parameter, data, month, timescale, precision) {
        const tsAvg = {};

        if (Object.keys(data).length === 0 || timescale === 'ann') {
            console.error(timescale === 'ann' ? 'Invalid timescale' : 'Empty data');
            return tsAvg;
        }

        if ((month > 0 && timescale == 1) || (timescale === 'ytd' && month == 1)) {
            return await this.getOneMonth(data, month, precision);
        }

        const ts = timescale === 'ytd' ? month : timescale;

        if (month == 0) {
            for (let m = 1; m <= 12; m++) {
                Object.assign(tsAvg, ts === 1
                    ? await this.getOneMonth(data, m, precision, true)
                    : await this.getDataAverages(parameter, data, m, ts === 0 ? m : ts, precision, true));
            }
            return Object.fromEntries(Object.entries(tsAvg).sort());
        }

        return await this.getDataAverages(parameter, data, month, ts, precision);
    }

    async getTimeSeriesBasePrdAvg(data, month, precision, begBaseYear, endBaseYear) {
        let basePrdAvg = {};
        let firstBaseYear, lastBaseYear;

        if (month == 0) {
            for (let mon = 1; mon <= 12; mon++) {
                const monthlyData = {};
                for (const [key, value] of Object.entries(data)) {
                    if (parseInt(String(key).slice(-2), 10) === mon) {
                        monthlyData[String(key).slice(0, 4)] = value;
                    }
                }
                const monResult = await this.getBasePrdAvg(monthlyData, begBaseYear, endBaseYear, precision)
                basePrdAvg[mon] = monResult.avg;
            }
            const overall = await this.getBasePrdAvg(data, begBaseYear, endBaseYear, precision);
            basePrdAvg[0] = overall.avg;
            firstBaseYear = overall.begBaseYear;
            lastBaseYear = overall.endBaseYear;
        } else {
            const result = await this.getBasePrdAvg(data, begBaseYear, endBaseYear, precision);
            basePrdAvg[month] = result.avg;
            firstBaseYear = result.begBaseYear;
            lastBaseYear = result.endBaseYear;
        }

        return {
            base_prd_avg: basePrdAvg,
            firstbaseyear: firstBaseYear,
            lastbaseyear: lastBaseYear
        };
    }

    async getBasePrdAvg(data, begBaseYear, endBaseYear, precision) {
        let total = 0;
        let count = 0;
        let beg = Infinity;
        let end = -Infinity;

        for (const [date, value] of Object.entries(data)) {
            const year = parseInt(String(date).slice(0, 4));
            if (year >= begBaseYear && year <= endBaseYear && value !== null && value !== undefined) {
                total += value;
                count++;
                if (year < beg) beg = year;
                if (year > end) end = year;
            }
        }

        let avg = null;
        if (count > 0) {
            // mimic PHP round() by shifting decimal before rounding
            // move decimal point to the right by 1, round, then move it back
            // to avoid native floating-point rounding errors
            const rawAvg = total / count;
            avg = Number(Math.round(rawAvg + "e+" + precision) + "e-" + precision);
        }

        return {
            avg: avg,
            begBaseYear: beg,
            endBaseYear: end
        };
    }
}
