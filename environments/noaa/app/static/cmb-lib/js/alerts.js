/**
 * alerts.js
 *
 * Script to append alert(s) to .alerts
 */

/**
 * NCEI Alerts
 *
 * The folowing displays the JSON message from the NCEI Drupal Alerts API.
 *
 * NCEI Drupal Alerts API
 *
 * https://www.ncei.noaa.gov/alerts/${endpoint}/api
 *
 * Since Monitoring applications are handled with redirects and do not match their location in DOCUMENT_ROOT, an
 * associative array of endpoints is maintained to ensure the alerts are displayed on the correct pages.
 *
 * climon-prod:/mondata/preview/lib/reference/ncei-alerts-endpoints.json
 */
$(function(){
    $.ajax({
        url: '/monitoring-content/lib/reference/ncei-alerts-endpoints.json',
        dataType: 'json'
    }).then(function(endpoints){
        addNceiAlerts(endpoints);
    });
});

function addNceiAlerts(endpoints) {
    const currentPath = window.location.pathname;

    Object.entries(endpoints).forEach(([path, endpoint]) => {
        // generate regex of path to test for match
        const escapedPath = path.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const searchRegex = new RegExp(escapedPath, 'g');

        // append ncei alert with unique ID "ncei-alert-[ENDPOINT]0, ncei-alert-[ENDPOINT]1..."
        if (currentPath.match(searchRegex)) {
            $.ajax({
                url: `/alerts/${endpoint}/api`,
                dataType: 'json'
            }).then((alerts) => {
                if (alerts.length > 0) {
                    alerts.forEach((alert, id) => {
                        // Only append the alert if it doesn't already exist
                        if ($(`#ncei-alert-${endpoint}${id}`).length === 0) {
                            const alertValue = alert.field_alert_type[0].value;
                            const description = alert.metatag[1].attributes.content;

                            $('.alerts').append(`
                                <div id="ncei-alert-${endpoint}${id}" class="ncei-alert-${endpoint} alert ${alertValue}">
                                    ${description}
                                </div>
                            `);
                        }
                    });
                }
            });
        } else {
            // Remove alerts if the path does not match
            $(`.ncei-alert-${endpoint}`).remove();
        }
    });
}

/**
 * Monitoring Alerts
 *
 *** Variables ***
 *****************
 *
 * /monitoring-content/lib/reference/alerts.json
 *
 * array of objects with the following elements:
 *
 * path  : relative path to app where the alert is to be displayed
 *         Use app root path, no subpaths (due to use of pushState within the apps to dynamically update browser URL)
 * note  : text to be displayed
 * class : list of class names separated by spaces, beginning with "alert" and followed by
 *         "info", "warning", "low", "medium", "high", "success", "error"
 * start (optional) : Date time string when the alert is to start
 * end (optional) : Date time string in Eastern Time when the alert is to end
 *
 * The Monitoring alerts file alerts.json is read by /cmb-lib/js/alerts.js and added to the appropriate application(s) based on the path attribute.
 *
 * Example:
 *
 * [
 *    {
 *        "path"  : "/access/",
 *        "note"  : "Please note: Due to scheduled maintenance, many NCEI systems will be unavailable February 13th, 8:00 AM ET - February 14th, 10:00 PM ET. We apologize for any inconvenience.",
 *        "class" : "alert high",
 *        "start" : "2024-02-12T00:00",
 *        "end"   : "2024-02-14T22:00"
 *    },
 *    {
 *        "path"  : "/access/monitoring/weekly-palmers",
 *        "note"  : "Please note, beginning September 4, 2021 the temperature and precipitation input for this product changed from CPC's station based data to NCEI's nClimGrid Daily data.",
 *        "class" : "alert info",
 *        "start" : "2021-09-04T00:00",
 *        "end"   : false
 *    }
 * ]
 */
 $(function(){
    $.ajax({
        url: '/monitoring-content/lib/reference/alerts.json',
        dataType: 'json'
    }).then(function(alerts){
        addAlerts(alerts);
    });
});

function addAlerts(alerts) {
    const currentPath = window.location.pathname;
    const currentDate = new Date().toLocaleString("en-US", { timeZone: "America/New_York" });
    const easternTime = new Date(currentDate);

    alerts.forEach((alert, id) => {
        // Skip this alert if it hasn't started yet or has already ended
        if (
            (alert.start && new Date(alert.start) > easternTime) ||
            (alert.end && new Date(alert.end) < easternTime)
        ) {
            return;
        }

        // generate regex of path to test for match
        const escapedPath = alert.path.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const searchRegex = new RegExp(escapedPath, 'g');

        // append alert with unique ID ("alert0", "alert1", ...)
        if (currentPath.match(searchRegex)) {
            if (!$(`#alert${id}`).length) {
                $('.alerts').append(`
                    <div id="alert${id}" class="${alert.class}">
                        ${alert.note}
                    </div>
                `);
            }
        } else {
            $(`#alert${id}`).remove();
        }
    });
}
