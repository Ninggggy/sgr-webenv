export const cag = window.cag = window.cag || {};

export const constants = cag.constants || {};

export const {
    http,
    base,
    content,
    cloud,
    dataDirs,
    scopes,
    scope,
    sections,
    section,
    pubDate,
    currDate,
    timescales,
    filters,
    basePeriods,
    begDates,
    endDates,
    minDates,
    maxDates,
    maxDate
} = constants;

cag.variables.docUri = window.location.href;
cag.variables.formChanged = false;
cag.variables.formState = '';
window.cag.variables.pageState = '';

export const monthNames  = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
    'Annual'
];
