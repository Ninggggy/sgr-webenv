function skipToMain(skip) {
    if (typeof skip !== 'string' || $('#' + skip).length === 0) {
        skip = 'main-content';
    }

    $('html, body').animate({ scrollTop: $('#' + skip).offset().top }, 100);
    if (!$('#' + skip).is(":focusable")) {
        $('#' + skip).attr("tabindex", 0);
    }
    $('#' + skip).focus();

    history.pushState(
        null,
        null,
        (window.location.href.indexOf('#') === -1 ?
            window.location.href + '#' + skip
            :
            window.location.href.replace(/#.*$/, '#' + skip)
        )
    );

    return false;
}