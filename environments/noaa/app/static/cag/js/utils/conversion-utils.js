import FormatUtil from './format-utils.js';

const toNumber = FormatUtil.toNumber;

const ConversionUtil = {
    conversions: {
        identity: (x) => toNumber(x),
        fToC:     (x) => (toNumber(x) - 32) / 1.8,
        cToF:     (x) => toNumber(x) * 1.8 + 32,
        inToMm:   (x) => toNumber(x) * 25.4,
        mmToIn:   (x) => toNumber(x) / 25.4,
        cToFAnom: (x) => toNumber(x) * 1.8,
        fToCAnom: (x) => toNumber(x) / 1.8
    }
};

export default ConversionUtil;