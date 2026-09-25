import {
    cag,
    base,
    content,
    scopes,
    scope,
    section,
    begDates,
    basePeriods,
    monthNames
} from '../globals.js';
import { citiesTableSorter } from '../shared/tablesorter.js';
import Util from '../utils/util.js';

const isHome = Util.section.is.home(section);

export function initDataInfo() {
    updateText(scope, begDates, basePeriods);

    generateDataInfoModal();

    const useUsScope = isHome || scope !== 'global';
    const usCities = useUsScope ? cag.constants.usCities : [];
    const usStates = useUsScope ? cag.constants.usStates : [];

    const relevantScope = isHome ? cag.variables.homeScope : scope;
    dataInfoToggle(base, content, scopes, relevantScope, usCities, usStates, begDates, basePeriods);

    $('#data-info-toggle').click(function(){
        const relevantScope = isHome ? cag.variables.homeScope : scope;
        fillDataInfo(base, content, scopes, relevantScope, usCities, usStates, begDates, basePeriods);
    });
}

function generateDataInfoModal(){
    $('#title-data-info div:last-child').append(`
    <a
            id="data-info-toggle"
            class="btn btn-primary"
            title="Data Information"
            data-bs-toggle="modal"
            data-bs-target="#data-info"
        >
            Data Info
        </a>
    `);

    $('body').append(`
        <div class="modal fade text-wrap" id="data-info" tabindex="-1" aria-labelledby="more-info" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        <div class="modal-title" id="more-info">
                            Climate at a Glance
                            <div id="data-info-title"></div>
                        </div>
                    </div>
                    <div class="modal-body text-left"></div>
                    <div class="modal-footer">
                        <button type="button" class="btn" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `);
}

function dataInfoToggle(base, content, scopes, dataInfoScope, usCities, usStates, begDates, basePeriods) {
    $('#data-info-toggle').attr('href', `${base}/${dataInfoScope}/data-info`);
    $('#data-info-toggle').attr({
        'href': `${base}/${dataInfoScope}/data-info`,
        'title': `${scopes[dataInfoScope]} Data Info`
    });

    const modalEl = document.getElementById('data-info');
    const modal = new bootstrap.Modal(modalEl);

    if (cag.variables.showDataInfo) {
        fillDataInfo(base, content, scopes, dataInfoScope, usCities, usStates, begDates, basePeriods);
        cag.variables.docUri = `${base}/${dataInfoScope}`;
        modal.show();

        cag.variables.showDataInfo = false;
    }

    modalEl.addEventListener('show.bs.modal', function () {
        cag.variables.docUri = window.location.href;
        const newUri = `${base}/${dataInfoScope}/data-info`;
        history.pushState(null, null, newUri);
    });

    modalEl.addEventListener('hidden.bs.modal', function () {
        if ($('.modal:visible').length === 0) history.pushState(null, null, cag.variables.docUri);
    });
}

function fillDataInfo(base, content, scopes, dataInfoScope, usCities = [], usStates = [], begDates, basePeriods){
    history.pushState(null, null, `${base}/${dataInfoScope}/data-info`);

    $('#data-info .modal-title #data-info-title').text(`${scopes[dataInfoScope]} Data Information`);

    $('#data-info .modal-body').html(
        '<div class="center">' +
            '<img alt="loader" src="/monitoring-content/lib/images/noaa-loader.gif">' +
        '</div>'
    );

    if (dataInfoScope === 'city') {
        getCityDataInfo(content, usCities, usStates, begDates);
    } else {
        getNonCityDataInfo(content, dataInfoScope, begDates, basePeriods);
    }
}

function getCityDataInfo(content, usCities, usStates, begDates) {
    $.ajax({
        url: `${content}/template/html/data-info/city-data-info.html`
    }).done(function(html){
        $('#data-info .modal-body').html(html);
        $('.cityCount').text(Object.values(usCities).length);
        generateCityTable(usCities, usStates, begDates);
        citiesTableSorter('#cities');
    }).fail(function(){
        $('#data-info .modal-body').html('<p class="red-txt">Data Information failed to load.</p>');
    });
}

function generateCityTable(usCities, usStates, begDates) {
    const tableRows = [];
    const ushcnSet = new Set(Object.keys(usCities).filter(id => id.startsWith("USH00")));

    $.each(usCities, function (id, city) {
        let begDateDisp = '';
        let begDateSortVal = '';

        if (begDates[id] && /^\d{6}$/.test(begDates[id])) {
            const begDate = String(begDates[id]);
            const begYear = begDate.slice(0, 4);
            const begMonth = parseInt(begDate.slice(-2), 10);
            const begMonthName = monthNames[begMonth - 1];

            begDateSortVal = begDate;
            begDateDisp = `<span class="monthabbr">${begMonthName.slice(0, 3)}</span>` +
                `<span class="monthlong">${begMonthName.slice(3)}</span> ${begYear}`;
        }

        tableRows.push(
            `<tr${ushcnSet.has(id) ? ' class="ushcn"' : ''}>
                <td class="city">${city.name}</td>
                <td class="state-name">${usStates[city.stateId].name}</td>
                <td class="state-abbr">${usStates[city.stateId].abbr}</td>
                <td class="id"><a href="https://www.ncei.noaa.gov/access/homr/#qid=GHCND:${id}">${id}</a></td>
                <td class="begdate" data-sortval="${begDateSortVal}">${begDateDisp}</td>
            </tr>`
        );
    });

    $('#cities tbody').html(tableRows.join(''));
}

function getNonCityDataInfo(content, dataInfoScope, begDates, basePeriods) {
    const isValidScope   = dataInfoScope in scopes;
    const isValidPre = /^\/monitoring-content\/[\w\/-]+$/.test(`${content}/template/html/data-info/${dataInfoScope}`);

    const url = isValidScope && isValidPre ? `${content}/template/html/data-info/${dataInfoScope}-data-info.html` : null;

    if (!url) {
        $('#data-info .modal-body').html('<p class="red-txt">Invalid Data Information parameters.</p>');
        return;
    }

    $.ajax({ url }).then(function(html) {
        $('#data-info .modal-body').html(html);
        updateText(dataInfoScope, begDates, basePeriods);
    })
    .fail(function() {
        $('#data-info .modal-body').html('<p class="red-txt">Data Information failed to load.</p>');
    });
}

function updateText(scope, begDates, basePeriods) {
    const updates = [
        { selector: '.minYear', value: String(parseInt(begDates[scope === 'global' ? 'global' : 'national'], 10)).substring(0, 4) },
        { selector: '.akMinYear', value: parseInt(String(begDates['alaska']).substring(0, 4), 10) },
        { selector: '.hiMinYear', value: parseInt(String(begDates['hawaii']).substring(0, 4), 10) },
        { selector: '.begPcpYear', value: parseInt(String(begDates['global-pcp']).substring(0, 4), 10) },
        { selector: '.globalBasePeriod', value: Object.values(basePeriods['global']['globe']).map(v => parseInt(v, 10)).join('-') },
        { selector: '.griddedBasePeriod', value: Object.values(basePeriods['global']['gridded']).map(v => parseInt(v, 10)).join('-') },
        { selector: '.regionalBasePeriod', value: Object.values(basePeriods['global']['region']).map(v => parseInt(v, 10)).join('-') },
        { selector: '.globalPcpBasePeriod', value: Object.values(basePeriods['global']['pcp']).map(v => parseInt(v, 10)).join('-') }
    ];

    updates.forEach(function(item) {
        if ($(item.selector).length) {
            $(item.selector).text(item.value);
        }
    });
}
