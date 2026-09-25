import {
    cag,
    base,
    content,
    http,
    scopes,
    scope,
    sections,
    section,
    begDates,
    basePeriods,
    monthNames
} from '../globals.js';
import { getLocations } from './locations.js';
import Util from '../utils/util.js';

const {
    global:   isGlobal,
    regional: isRegional,
    city:     isCity,
    substate: isSubstate
} = Util.scope.is;
const isTimeSeries = Util.section.is.timeSeries;

export function initApiDoc() {
    $(async function(){
        if (isTimeSeries(section)) {
            await generateApiDocModal();
            populateApiDoc(base, scope, section);
            apiDocToggle();
        }
    });
}

async function generateApiDocModal(){
    $('#title-data-info div:last-child').append(`
        <a
            id="data-svc-toggle"
            class="btn btn-primary"
            title="${scopes[scope]} ${sections[section]} Data Service"
            data-bs-toggle="modal"
            data-bs-target="#api-doc"
        >
            Data Service
        </a>
    `);

    const response = await fetch(`${content}/template/html/api/time-series-api-doc.html`);
    const html = await response.text();
    document.body.insertAdjacentHTML('beforeend', html);
}

function apiDocToggle() {
    const $apiDocModal = $('#api-doc');

    if (cag.variables.showApiDoc) {
        cag.variables.docUri = `${base}/${scope}/${section}`;
        $apiDocModal.modal('show');
        cag.variables.showApiDoc = false;
    }

    // Remove previous handlers to prevent multiple bindings
    $apiDocModal.off('show.bs.modal hidden.bs.modal');

    $apiDocModal.on('show.bs.modal', () => {
        // Capture the current URL before the modal is shown
        cag.variables.docUri = window.location.href;
        const newUri = `${base}/${scope}/${section}/service-api`;
        history.pushState(null, null, newUri);
    });

    $apiDocModal.on('hidden.bs.modal', () => {
        if ($('.modal:visible').length === 0) history.pushState(null, null, cag.variables.docUri);
    });
}

function populateApiDoc(appBase, apiScope, apiSection) {
    const href = `${appBase}/${apiScope}/${apiSection}/service-api`.replace(/[^-\w\/]/g, '');
    $('#data-svc-toggle').attr('href', href);
    $('.scopeApiName').text(isGlobal(apiScope) ? 'Global' : 'National');
    $('.sectionApiName').text(sections[apiSection]);
    $('.http').text(http);

    const $locationVar = $('.locationVarName');
    const $surfaceElements = $('#template-uri #uriSurface, #request-parameters #surface-parameter');

    if (isGlobal(apiScope)) {
        $locationVar.text('region');
        $surfaceElements.show();

        if ($('#global-note').length === 0) {
            $('#query-parameters').append(`
                <p id="global-note" class="small italic">
                    <strong>Note:</strong> A base period is used to calculate departures based on the average of the
                    requested period. <strong class="dk-gray-txt">basePeriod</strong> is not applicable to Global
                    Average Temperature Departures (<strong class="dk-gray-txt">parameter</strong> =
                    <em class="dk-gray-txt">tavg</em>) since base periods are fixed for each region. See
                    <a id="global-data-info-toggle" data-bs-target="#data-info" data-bs-toggle="modal" data-bs-dismiss="modal" href="${base}/global/data-info">Data Info</a>.
                </p>
            `);
            $('#global-data-info-toggle').click(function(){
                cag.variables.showDataInfo = true;
                cag.variables.docUri = `${base}/${scope}/${section}`;
                fillDataInfo(base, content, scopes, apiScope, [], [], begDates, basePeriods);
            });
        }
    } else {
        $locationVar.text('location');
        $surfaceElements.hide();
        $('#global-note').remove();
    }

    if (isGlobal(apiScope)) {
        fillApiDocGlobalRegions();
        fillApiDocSurfaces(apiScope);
        $('#scopeUriValue').text('global');
        $('#scope-parameter').hide();
    } else {
        $('#surface-parameter').remove();
        fillApiDocScopes(apiScope);
        fillApiDocLocations(apiScope);
    }

    fillApiDocParameters(apiScope);
}

function fillApiDocScopes(apiScope) {
    if (isGlobal(apiScope)) {
        $('#scopeUriValue').text('global');
        $('#scope-parameter').hide();
        return;
    }

    $('#scopeUriValue').html('<strong>{scope}</strong>');

    const $scopeDesc = $('#scope-parameter .parameter-description .table-display');
    const scopeRows = [];

    Object.entries(scopes).forEach(([key, title]) => {
        if (isGlobal(key)) return;

        const scopeVal = escapeHtml(key);
        const name = escapeHtml(title);

        scopeRows.push(`
            <div class="table-row">
                <div class="table-cell dk-gray-txt italic smallPadRight">${scopeVal}</div>
                <div class="table-cell">${name}</div>
            </div>
        `);
    });

    $scopeDesc.append(scopeRows.join(''));
    $('#scope-parameter').show();
}

function fillApiDocGlobalRegions() {
    const $apiDescTable = $('#location-parameter .parameter-description .table-display');
    const tableRows = [];

    if ($('#global-sfc-note').length === 0) {
        $('#location-parameter .parameter-description').prepend(`
            <div id="global-sfc-note" class="marginBottom small italic">
                Accepted <strong class="dk-gray-txt">surface</strong> values in parentheses
            </div>
        `);
    }


    const getDispName = (val, name) => {
        const links = {
            caribbeanIslands: "global-regions-map-1.png",
            eastNPacific: "global-regions-map-1.png",
            hawaiianRegion: "global-regions-map-1.png",
            atlanticMdr: "global-regions-map-2.png",
            gulfOfAmerica: "global-regions-map-2.png"
        };
        const link = links[val];
        if (link) {
            const displayName = val === "atlanticMdr" || val === "gulfOfAmerica"
                ? name.replace('MDR', 'Main Development Region')
                : name;
            return `<a href="/monitoring-content/monitoring-references/dyk/images/${link}">${displayName}</a>`;
        }
        return name;
    };

    const createTableRow = (val, dispName, surfaces) => {
        const surfaceText = surfaces.length
            ? ` <em class="small dk-gray-txt nowrap">(${surfaces.join(', ')})</em>`
            : '';

        return `
            <div class="table-row">
                <div class="table-cell dk-gray-txt italic smallPadRight">${val}</div>
                <div class="table-cell">${dispName}${surfaceText}</div>
            </div>
        `;
    };

    $.each(cag.constants.globalRegions, (key, attr) => {
        const val = escapeHtml(key);
        const name = escapeHtml(attr.title);
        const dispName = getDispName(val, name);

        tableRows.push(createTableRow(val, dispName, attr.surfaces));
    });

    $apiDescTable.append(tableRows.join(''));
}

async function fillApiDocLocations(apiScope) {
    if (isGlobal(apiScope)) {
        $('#national-location-note').remove();
        return;
    }

    const $locDesc = $('#location-parameter .parameter-description .table-display');
    const locRows = [];
    const locIds = {};

    $locDesc
        .find('.table-row:first-child .table-cell:first-child')
        .append(`<div class="italic small" id="national-location-note">(click scope to toggle)</div>`);

    for (const [scopeKey, title] of Object.entries(scopes)) {
        if (isGlobal(scopeKey)) continue;

        const scopeVal = escapeHtml(scopeKey);
        const name = escapeHtml(title);

        const locs = await getLocations(scopeKey);

        locIds[scopeVal] = [];
        let regionGroup = null;

        Object.entries(locs)
            .sort(([a], [b]) => a.localeCompare(b, 'en', { numeric: true }))
            .forEach(([locId, attr]) => {
                let locName = attr.name;

                if (isSubstate(scopeVal) && attr.hasOwnProperty('stateAbbr')) {
                    locName += `, ${attr.stateAbbr}`;
                    if (isCity(scopeVal)) {
                        const begDate = String(attr.begdate);
                        const begYear = begDate.slice(0, 4);
                        const begMonth = begDate.slice(-2);
                        const begMonthName = monthNames[begMonth - 1];
                        locName += ` <em class="dk-gray-txt small">(${begMonthName} ${begYear})</em>`;
                    }
                } else if (isRegional(scopeVal)) {
                    if (regionGroup !== attr.regionGroup) {
                        regionGroup = attr.regionGroup;
                        locIds[scopeVal].push({
                            id: '<span class="inline-block smallMarginTop">&nbsp;</span>',
                            name: `<strong class="inline-block smallMarginTop">${regionGroup}</strong>`
                        });
                    }
                }

                locIds[scopeVal].push({ id: locId, name: locName });
            });

        const cityNote = isCity(scopeVal)
            ? `<em class="location-values ${scopeVal}-locations dk-gray-txt small">(start dates are in parentheses)</em>`
            : '';

        locRows.push(`
            <div class="table-row">
                <div class="table-cell dk-gray-txt italic">
                    <a data-scope="${scopeVal}" class="location-toggle" href="${base}/${scopeVal}/locations.json">
                        ${name} <span class="toggle-arrow" id="${scopeVal}-toggle-arrow">↓</span>
                    </a>${cityNote}
                </div>
            </div>
            <div class="table-row">
                <div class="table-cell dk-gray-txt italic">
                    <div id="${scopeVal}-location-table" class="table-display location-values ${scopeVal}-locations"></div>
                </div>
            </div>
        `);
    }

    $locDesc.append(locRows.join(''));

    $('.location-values').hide();
    Object.entries(locIds).forEach(([scopeVal, locArray]) => {
        locArray.forEach(item => {
            $(`#${scopeVal}-location-table`).append(`
                <div class="table-row">
                    <div class="table-cell nowrap smallPadRight">${item.id}</div>
                    <div class="table-cell">${item.name}</div>
                </div>
            `);
        });
    });

    toggleLocationValues(apiScope);

    $('.location-toggle').click(function () {
        const locScope = $(this).data('scope');
        toggleLocationValues(locScope);
        return false;
    });
}
function toggleLocationValues(locScope){
    $(`.${locScope}-locations`).slideToggle(function(){
        $(`#${locScope}-toggle-arrow`).text(
            $(`#${locScope}-location-table`).is(':visible')
                ? '↑'
                : '↓'
        );
    });
}

function fillApiDocParameters(apiScope) {
    const $apiDescTable = $('#parameter-parameter .parameter-description .table-display');
    const $porApiDesc = $('.year-parameter .parameter-description .table-display');

    if (isGlobal(apiScope)) {
        $('#us-parameter-note').remove();
    } else {
        $apiDescTable.find('.table-row:first-child .table-cell:first-child').append('*');
        const $usNotes = $('#us-notes');
        const $toggleUsNotes = $('#toggle-us-notes');
        $usNotes.hide();
        $toggleUsNotes.click(function(){
            $usNotes.slideToggle(function(){
                $toggleUsNotes.find('span').text(
                    $usNotes.is(':visible') ? '↑' : '↓'
                );
            });
            return false;
        });
    }

    const tableRows = [];
    const porTableRows = [];

    $.each(cag.constants.parameters, (key, attr) => {
        const param = escapeHtml(key);
        const name  = escapeHtml(attr.title);

        tableRows.push(
            `<div class="table-row">
                <div class="table-cell dk-gray-txt italic smallPadRight">${param}</div>
                <div class="table-cell">${name}</div>
            </div>`
        );

        if (isGlobal(apiScope)) {
            const minYr = escapeHtml(attr.minYear);
            const maxYr = escapeHtml(attr.maxYear);
            porTableRows.push(
                `<div class="table-row ${key}-por-row">
                    <div class="table-cell dk-gray-txt italic smallPadRight">${minYr}-${maxYr}</div>
                    <div class="table-cell">${name}</div>
                </div>`
            );
        }
    });

    if (isGlobal(apiScope)) {
        $porApiDesc.append(porTableRows.join(''));
    } else {
        let minYr = parseInt(String(begDates['national']).substring(0, 4));
        let maxYr = parseInt(String(cag.constants.maxDate).substring(0, 4)) ;
        $porApiDesc.html(
            `<div class="table-row por-row">
                <div class="table-cell dk-gray-txt italic smallPadRight">${minYr}-${maxYr}</div>
            </div>`
        );
    }

    $apiDescTable.append(tableRows.join(''));
}

function fillApiDocSurfaces(apiScope) {
    if (apiScope !== 'global') {
        $('#surface-parameter').remove();
        return
    }

    const $apiDescTable = $('#surface-parameter .parameter-description .table-display');

    const opts = [];
    const tableRows = [];

    $.each(cag.constants.surfaces, (key, title) => {
        const param = escapeHtml(key);
        const name = escapeHtml(title);

        tableRows.push(
            `<div class="table-row">
                <div class="table-cell dk-gray-txt italic smallPadRight">${param}</div>
                <div class="table-cell">${name}</div>
            </div>`
        );

        opts.push(`<option value="${param}">${name}</option>`);
    });

    tableRows.push(
        `<div class="table-row">
            <div class="table-cell dk-gray-txt italic smallPadRight">[-90&mdash;90],[-180&mdash;180]</div>
            <div class="table-cell">Latitude and Longitude*</div>
        </div>`
    );

    $apiDescTable.
        append(tableRows.join('')).
        after(`
            <div class="marginTop small italic">
                *If '<em class="dk-gray-txt">coords</em>' is entered for <strong class="dk-gray-txt bold">region</strong>, use comma separated latitude (between <em class="dk-gray-txt">-90.0</em> and <em class="dk-gray-txt">90.0</em>) and longitude (between <em class="dk-gray-txt">-180.0</em> and <em class="dk-gray-txt">180.0</em>) with no spaces (e.g., <em class="dk-gray-txt">30.4,84.3</em>).
            </div>
        `);
}
