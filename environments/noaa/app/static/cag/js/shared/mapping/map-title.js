import Util from "../../utils/util.js";

const {
    national: isNational,
    regional: isRegional,
    global:   isGlobal
} = Util.scope.is;

export function getMapTitle(scope, scopes, parameter, returnType, basePeriod, numYears) {
    const parameterOption = document.querySelector(`#parameter option[value="${parameter}"]`);
    let title = '';

    if (!isGlobal(scope) && !isNational(scope) && !isRegional(scope)) {
        title = (scopes[scope] || '') + ' ';
    }

    const paramTitle = parameterOption.textContent || '';
    title += ['cdd', 'hdd'].includes(parameter) ? paramTitle : paramTitle.split(' (')[0];


    if (isGlobal(scope) && parameter === 'tavg') {
        title = title.replace('Average Temperature', '<span class="longname">Average </span>Temp<span class="longname">erature</span>');
    }

    if (returnType !== 'value') {
        const returnRadio = document.querySelector(`#return input[value="${returnType}"]`);
        const returnText = returnRadio
            ? (returnRadio.labels[0]?.title.trim() || '')
                .replace('Departure from Average', 'Departure<span class="longname"> from Average</span>')
            : '';

        title += ` ${returnText} <span class="small dk-gray-txt normal-font-weight">(${returnType === 'rank' ? `${numYears} years` : basePeriod})</span>`;
    }

    return title;
}