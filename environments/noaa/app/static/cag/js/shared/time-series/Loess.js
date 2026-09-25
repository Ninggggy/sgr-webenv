export class LoessInterpolator {
    /**
     * bandwidth
     * 
     * The bandwidth parameter: when computing the loess fit at
     * a particular point, this fraction of source points closest
     * to the current point is taken into account for computing
     * a least-squares regression.
     *
     * A sensible value is usually 0.25 to 0.5.
     */

    /**
     * robustness
     * 
     * The number of robustness iterations parameter: this many
     * robustness iterations are done.
     *
     * A sensible value is usually 0 (just the initial fit without any
     * robustness iterations) to 4.
     */
    constructor(bandwidth = 0.3, robustnessIters = 2) {
        if (bandwidth < 0 || bandwidth > 1) {
            throw new Error(`bandwidth must be in the interval [0,1], but got ${bandwidth}`);
        }
        this.bandwidth = bandwidth;

        if (robustnessIters < 0) {
            throw new Error(`the number of robustness iterations must be non-negative, but got ${robustnessIters}`);
        }
        this.robustnessIters = robustnessIters;
    }

    /**
     * Compute a loess fit on the data for the original abscissae.
     * @param {Object} data - Keys are abscissae (x), values are ordinates (y).
     * @returns {Object} - Smooth values at original keys.
     */
    smooth(data) {
        const origKeys = Object.keys(data);
        // Remove null data to determine trend
        const filtered = Object.entries(data)
            .filter(([_, v]) => v !== null)
            .map(([k, v]) => [parseFloat(k), v]);

        const xval = filtered.map(([k]) => Number(k));
        const yval = filtered.map(([, v]) => v);

        const n = xval.length;
        if (n === 0) throw new Error('Loess expects at least 1 point');

        this.checkAllFiniteReal(xval, true);
        this.checkAllFiniteReal(yval, false);
        this.checkStrictlyIncreasing(xval);

        if (n === 1) return { [xval[0]]: yval[0] };
        if (n === 2) return { [xval[0]]: yval[0], [xval[1]]: yval[1] };

        const bandwidthInPoints = Math.floor(this.bandwidth * n);
        if (bandwidthInPoints < 2) {
            throw new Error(
                'Bandwidth must be large enough to accommodate at least 2 points. ' +
                `There are ${n} data points, and bandwidth must be at least ${2 / n} but it is only ${this.bandwidth}.`
            );
        }

        let res = new Array(n);
        let residuals = new Array(n);

        /**
         * Do an initial fit and 'robustnessIters' robustness iterations.
         * This is equivalent to doing 'robustnessIters+1' robustness iterations
         * starting with all robustness weights set to 1.
         */
        let robustnessWeights = Array(n).fill(1);

        for (let iter = 0; iter <= this.robustnessIters; iter++) {
            let bandwidthInterval = [0, bandwidthInPoints - 1];

            for (let i = 0; i < n; i++) {
                let x = xval[i];

                // Find out the interval of source points on which a regression is to be made.
                if (i > 0) {
                    bandwidthInterval = this.updateBandwidthInterval(xval, i, bandwidthInterval);
                }

                const [ileft, iright] = bandwidthInterval;

                // Compute the point of the bandwidth interval that is farthest from x
                const edge = (xval[i] - xval[ileft]) > (xval[iright] - xval[i]) ? ileft : iright;

                /**
                 * Compute a least-squares linear fit weighted by
                 * the product of robustness weights and the tricube
                 * weight function.
                 * See http://en.wikipedia.org/wiki/Linear_regression
                 * (section "Univariate linear case")
                 * and http://en.wikipedia.org/wiki/Weighted_least_squares
                 * (section "Weighted least squares")
                 */
                let sumWeights = 0, sumX = 0, sumXSquared = 0, sumY = 0, sumXY = 0;
                let denom = Math.abs(1.0 / (xval[edge] - x));

                for (let k = ileft; k <= iright; k++) {
                    const xk = xval[k], yk = yval[k];
                    const dist = k < i ? x - xk : xk - x;
                    const w = this.tricube(dist * denom) * robustnessWeights[k];
                    const xkw = xk * w;
                    sumWeights += w;
                    sumX += xkw;
                    sumXSquared += xk * xkw;
                    sumY += yk * w;
                    sumXY += yk * xkw;
                }

                const meanX = sumX / sumWeights;
                const meanY = sumY / sumWeights;
                const meanXY = sumXY / sumWeights;
                const meanXSquared = sumXSquared / sumWeights;

                const beta =
                    meanXSquared === meanX ** 2
                        ? 0
                        : (meanXY - meanX * meanY) / (meanXSquared - meanX ** 2);

                const alpha = meanY - beta * meanX;

                res[i] = beta * x + alpha;
                residuals[i] = Math.abs(yval[i] - res[i]);
            }

            // No need to recompute the robustness weights at the last
            // iteration, they won't be needed anymore
            if (iter === this.robustnessIters) break;

            // Recompute robustness weights

            // Find the median residual
            const sortedResiduals = [...residuals].sort((a, b) => a - b);
            const medianResidual = sortedResiduals[Math.floor(n / 2)];
            if (medianResidual === 0) break;

            for (let l = 0; l < n; l++) {
                const arg = residuals[l] / (6 * medianResidual);
                robustnessWeights[l] = arg >= 1 ? 0 : (1 - arg ** 2) ** 2;
            }
        }

        // Combine results with original keys, fill missing with null
        const smooth = {};
        for (let i = 0; i < xval.length; i++) {
            smooth[xval[i]] = res[i];
        }
        for (const key of origKeys) {
            if (!smooth.hasOwnProperty(key)) {
                smooth[key] = null;
            }
        }
        // Sort smooth by key if desired
        return Object.fromEntries(
            Object.entries(smooth).sort((a, b) => Number(a[0]) - Number(b[0]))
        );
    }

    /**
     * Update bandwidth interval for local regression.
     * 
     * Given an index interval into xval that embraces a certain number of
     * points closest to xval[i-1], update the interval so that it embraces
     * the same number of points closest to xval[i]
     *
     * @param xval arguments array
     * @param i the index around which the new interval should be computed
     * @param bandwidthInterval a two-element array {left, right} such that: <p/>
     * <tt>(left==0 or xval[i] - xval[left-1] > xval[right] - xval[i])</tt>
     * <p/> and also <p/>
     * <tt>(right==xval.length-1 or xval[right+1] - xval[i] > xval[i] - xval[left])</tt>.
     * The array will be updated.
     */
    updateBandwidthInterval(xval, i, bandwidthInterval) {
        let [left, right] = bandwidthInterval;

        // The right edge should be adjusted if the next point to the right
        // is closer to xval[i] than the leftmost point of the current interval
        if (
            right < xval.length - 1 &&
            xval[right + 1] - xval[i] < xval[i] - xval[left]
        ) {
            left++;
            right++;
        }
        return [left, right];
    }

    /**
     * Compute the tricube weight function
     * http://en.wikipedia.org/wiki/Local_regression#Weight_function
     *
     * @param x the argument
     * @return (1-|x|^3)^3
     */
    tricube(x) {
        const absX = Math.abs(x);
        const tc = 1 - absX ** 3;
        return tc * tc * tc;
    }

    /**
     * Check that all elements of an array are finite real numbers.
     *
     * @param values the values array
     * @param isAbscissae if true, elements are abscissae otherwise they are ordinatae
     * @throws MathException if one of the values is not
     *         a finite real number
     */
    checkAllFiniteReal(values, isAbscissae) {
        for (let i = 0, n = values.length; i < n; ++i) {
            const value = values[i];
            if (!Number.isFinite(value)) {
                const coords = isAbscissae ? 'abscissae' : 'ordinates';
                throw new Error(
                    `all ${coords} must be finite real numbers, but at index ${i} got ${value}`
                );
            }
        }
    }

    /**
     * Check that elements of the abscissae array are in a strictly
     * increasing order.
     *
     * @param xval the abscissae array
     * @throws MathException if the abscissae array
     * is not in a strictly increasing order
     */
    checkStrictlyIncreasing(xval) {
        for (let i = 1; i < xval.length; i++) {
            if (xval[i - 1] >= xval[i]) {
                throw new Error(
                    `The abscissae array must be sorted in strictly increasing order, but index ${i - 1} is ${arr[i - 1]} and index ${i} is ${arr[i]}`
                );
            }
        }
    }
}
