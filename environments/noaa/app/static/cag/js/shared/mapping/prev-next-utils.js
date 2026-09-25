export function buildLinkHtml(direction, title, year, month, href) {
    const icon = direction === "next" ? "right" : "left";
    return `
        <a title="${title}" data-year="${year}" data-month="${month}" href="${href}">
            <i class="fas fa-chevron-circle-${icon}" aria-hidden="true"></i>
        </a>
    `;
}

export function renderPrevNext(direction, dateInfo, href, clickHandler) {
    const selector = `#${direction}`;
    if (!dateInfo) {
        $(selector).hide();
        return;
    }
    const { title, year, month } = dateInfo;
    const html = buildLinkHtml(direction, title, year, month, href);
    const $el = $(selector);
    $el.html(html).show();
    $el.find("a").click(clickHandler);
}

/**
 * Factory to create a prev/next click handler.
 * 
 * @param {Function} onFillMonths - function to refresh month options (global/us specific)
 * @param {Function} onUpdate - function to submit/update data (global/us specific)
 */
export function makePrevNextClick(onFillMonths, onUpdate) {
    return function () {
        cag.variables.formChanged = true;

        cag.variables.year = $(this).data("year");
        if (cag.variables.year != $("#year").val()) {
            $("#year").val(cag.variables.year);
            onFillMonths();
        } else {
            $("#year").val(cag.variables.year);
        }

        cag.variables.month = $(this).data("month");
        $("#month").val(cag.variables.month);

        onUpdate();
        return false;
    };
}

/**
 * Generic Prev/Next engine.
 */
export function computeAndRenderPrevNext({ direction, compute, hrefBuilder, clickHandler }) {
    const isPrev = direction === "prev";
    const result = compute(isPrev);

    if (!result || !result.valid) {
        renderPrevNext(direction, null);
        return;
    }

    const { year, month, title, dateStr } = result;
    const href = hrefBuilder(dateStr, year, month);
    renderPrevNext(direction, { title, year, month }, href, clickHandler);
}
