import { base, content, scope, section } from './globals.js';
import { initHome } from './home/home.js';

import { initDataInfo } from './shared/data-info.js';

import { initPageConfig } from './config/page-config.js';
import { setupNav } from './config/cag-nav.js';
import { setBreadcrumb } from './config/set-breadcrumb.js';
import { getGlobalNote, getUsNote } from './config/get-note.js';

import { initApiDoc } from './api/api-doc.js';

import { fillUsStates, fillUsLocations } from './config/fill-us-locations.js';

import { initGlobalForm } from './config/global-form-config.js';

import { initGlobalMapping } from './global/mapping.js';
import { initGlobalTimeSeries } from './global/time-series.js';
import { initGlobalRankings } from './global/rankings.js';
import { initGlobalHaywood } from './global/haywood.js';

import { initUsMapping } from './us/mapping.js';
import { initUsTimeSeries } from './us/time-series.js';
import { initUsRankings } from './us/rankings.js';
import { initUsHaywood } from './us/haywood.js';

import Util from './utils/util.js';

const { global: isGlobal, substate: isSubstate } = Util.scope.is;
const isMapping = Util.section.is.mapping;

const initializers = {
    "global": {
        "mapping":     initGlobalMapping,
        "time-series": initGlobalTimeSeries,
        "rankings":    initGlobalRankings,
        "haywood":     initGlobalHaywood
    },
    "us": {
        "mapping":     initUsMapping,
        "time-series": initUsTimeSeries,
        "rankings":    initUsRankings,
        "haywood":     initUsHaywood
    }
};

$(function() {
    $(window).on('popstate', () => location.reload());
});

initDataInfo();

if (['home', 'data-info', 'background'].includes(section)) {
    initHome();
} else {
    initPageConfig();
    setupNav();
    setBreadcrumb(base, scope, section);
    initApiDoc();

    if (isGlobal(scope)) {
        getGlobalNote(content, section);
        initGlobalForm();

        initializers.global[section]?.();
    } else {
        getUsNote(content, scope, section);

        // populate form
        if (!isMapping(section) && isSubstate(scope)) {
            fillUsStates();
        }
        fillUsLocations();

        // reset formChanged after form population
        cag.variables.formChanged = false;

        initializers.us[section]?.();
    }
}
