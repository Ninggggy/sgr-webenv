import {
    cag,
    base,
    pubDate,
    currDate,
    http,
    scopes,
    sections,
    section,
    scope
} from '../globals.js';

export function initPageConfig() {
    loadElemValues(http, base, scopes, scope, sections, section);
    setDataAccess();
    setCitation();

    cag.variables.formState = $('#select-form').serialize();
    $('#select-form').on('change input', function() {
        cag.variables.formChanged = $('#select-form').serialize() !== cag.variables.formState;
    });
}

function loadElemValues(http, base, scopes, scope, sections, section) {
    $('.scopeName').text(scopes[scope]);
    $('.sectionName').text(sections[section]);
    $('.http').text(http);
    $('#select-form').attr('action', `${base}/${scope}/${section}/plot`);

    if ($('.minYear').length) $('.minYear').text(cag.constants.minYear);
}

function setDataAccess() {
    const formats = [
        { id: 'csv', mime: 'text/csv', download: 'data.csv', title: 'CSV', abbrTitle: 'Comma Separated Values' },
        { id: 'json', mime: 'application/json', download: 'data.json', title: 'JSON', abbrTitle: 'JavaScript Object Notation' },
        { id: 'xml', mime: 'application/xml', download: 'data.xml', title: 'XML', abbrTitle: 'Extensible Markup Language' }
    ];

    const elements = formats.map(({ id, mime, download, title, abbrTitle }) => 
        `<a id="${id}-download" class="btn btn-download" title="Download data in ${title} format" type="${mime}" download="${download}">
            <abbr title="${abbrTitle}">${title}</abbr>
        </a>`
    );

    $('#data-access').empty().html(elements.join(' '));
}

function setCitation() {
    const scopeUrl = `${base}/${scope}`;
    const sectionUrl = `${scopeUrl}/${section}`;
    const httpUrl = `${http}${sectionUrl}`;

    $('#page-content').append(`
        <h3>Citing This Page</h3>
        <ul class="references">
            <li>
                NOAA National Centers for Environmental information, Climate at a Glance:
                ${scopes[scope]} ${sections[section]},
                published ${pubDate}, retrieved on ${currDate}
                from <a href="${sectionUrl}">${httpUrl}</a>
            </li>
        </ul>
    `);
}
