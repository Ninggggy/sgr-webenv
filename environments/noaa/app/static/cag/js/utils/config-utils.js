import ParameterUtil from "./parameter-utils.js";

const ConfigUtil = {
    /**
     * Update download links based on the given base URL and query string.
     */
    configDownload(url, qStr = '') {
        const query = qStr ? (qStr.startsWith('?') ? qStr : `?${qStr}`) : '';
        ['xml', 'csv', 'json'].forEach(fmt => {
            document.getElementById(`${fmt}-download`).href = `${url}/data.${fmt}${query}`;
        });
    },

    /**
     * Push updated URL to history if formChanged is false
     */
    updateUrl() {
        if (window.cag?.variables?.formChanged === false) {
            const { origin, search, hash } = window.location;
            const newUrl = `${origin}${cag.variables.url}${search}${hash}`;
            if (window.location.href !== newUrl) {
                window.history.pushState(null, null, newUrl);
            }
            return false;
        }
    },

    /**
     * Only Palmer Z-index is available for all timescales.
     * Disable non-1-month timescales for Non-Z Palmers
     */
    disableTimescales() {
        const isNonZPalmer      = ParameterUtil.is.nonZPalmer;
        const $timescale        = $('#timescale');
        const selectedTimescale = $timescale.val();
        const selectedParameter = $('#parameter').val();

        $timescale.find('option').prop('disabled', false);
        if (isNonZPalmer(selectedParameter)) {
            if (selectedTimescale != 1) {
                $timescale.val(1).trigger('change');
            }
            $timescale.find('option').not('[value="1"]').prop('disabled', true);
        }
    }
};

export default ConfigUtil;
