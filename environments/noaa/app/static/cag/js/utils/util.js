import ConfigUtil     from "./config-utils.js";
import FormUtil       from "./form-utils.js";
import FormatUtil     from "./format-utils.js";
import ParameterUtil  from "./parameter-utils.js";
import ScopeUtil      from "./scope-utils.js";
import SectionUtil    from "./section-utils.js"
import LocationUtil   from "./location-utils.js";
import ConversionUtil from "./conversion-utils.js";
import RanksUtil      from "./ranks-utils.js";

import { insufficientVariability } from "./insufficient-variability.js"

const Util = {
    config:     ConfigUtil,
    conversion: ConversionUtil,
    form:       FormUtil,
    format:     FormatUtil,
    location:   LocationUtil,
    parameter:  ParameterUtil,
    ranks:      RanksUtil,
    scope:      ScopeUtil,
    section:    SectionUtil,

    is: {
        /**
         * (Very) Basic mobile detection
         */
        mobile: /Mobi|Android/i.test(navigator.userAgent),

        insufficientVariability
    },

    /**
     * @param {number} begYYYYMM - e.g., 189501
     * @param {number} endYYYYMM - e.g., 202601
     * @param {number} month     - The target month (1-12)
     * @param {number} timescale - The duration in months
     */
    numYears: (begYYYYMM, endYYYYMM, month, timescale) => {
        const begYear  = Math.floor(begYYYYMM / 100);
        const begMonth = begYYYYMM % 100;

        const endYear  = Math.floor(endYYYYMM / 100);
        const endMonth = endYYYYMM % 100;

        const begAbs = begYear * 12 + (begMonth - 1);
        const endAbs = endYear * 12 + (endMonth - 1);

        // window start months
        const first = begAbs + (timescale - 1);
        const last  = endAbs;

        if (first > last) return 0;

        // anchor on the requested month
        const firstYear = Math.floor(first / 12);
        const firstAnchor =
            firstYear * 12 + (month - 1) +
            (first % 12 > month - 1 ? 12 : 0);

        return Math.max(0, Math.floor((last - firstAnchor) / 12) + 1);
    },

    getPrecision: (location = null, parameter = null) => {
        return (location == 11000 || location == 110) && ParameterUtil.is.temp(parameter)
            ? 2
            : cag.constants.parameters[parameter].precision
    },

    getQueryParam: (key, pattern, flags = '', defaultValue) => {
        const params = new URLSearchParams(window.location.search);
        const value = params.get(key);
        const regex = new RegExp(pattern, flags);
        
        return value !== null && regex.test(value)
            ? value
            : defaultValue;
    }
};

export default Util;
