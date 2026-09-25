import { monthNames } from '../globals.js';

export function getDateDisplay(date, month, timescale) {
    let dateDisplay = document.createDocumentFragment();

    const year = parseInt(date.toString().substr(0, 4));

    if (((timescale == 12 || timescale == 'ytd') && month == 12) || timescale == 'ann') {
        dateDisplay.appendChild(document.createTextNode(year));
        return dateDisplay;
    }

    const dateMonth = parseInt(String(date).slice(-2));
    let begMonth = (timescale === 'ytd' ? 1 : (dateMonth - timescale) + 1);
    let yearDiff = 0;

    while (begMonth < 1) {
        begMonth += 12;
        yearDiff++;
    }

    if ((timescale > 1) || (timescale === 'ytd' && dateMonth > 1)) {
        let begMonthName = monthNames[begMonth - 1];
        dateDisplay.appendChild(document.createTextNode(begMonthName.substring(0, 3)));

        if (begMonthName.length > 3) {
            let begMonthlongSpan = document.createElement('span');
            begMonthlongSpan.className = 'monthlong';
            begMonthlongSpan.textContent = begMonthName.substring(3);
            dateDisplay.appendChild(begMonthlongSpan);
        }

        if (yearDiff > 0) {
            dateDisplay.appendChild(document.createTextNode(` ${year - yearDiff}`));
        }

        dateDisplay.appendChild(document.createTextNode('-'));
        dateDisplay.appendChild(document.createElement('wbr'));
    }

    let endMonthName = monthNames[dateMonth - 1];
    dateDisplay.appendChild(document.createTextNode(endMonthName.substring(0, 3)));

    if (endMonthName.length > 3) {
        let endMonthlongSpan = document.createElement('span');
        endMonthlongSpan.className = 'monthlong';
        endMonthlongSpan.textContent = endMonthName.substring(3);
        dateDisplay.appendChild(endMonthlongSpan);
    }

    dateDisplay.appendChild(document.createTextNode(` ${year}`));

    return dateDisplay;
}
