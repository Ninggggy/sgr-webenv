export async function buildReturnOptions(returnTypes, selectedType, scope, parameter) {
    const container = document.getElementById('return');
    if (!container) throw new Error('Return Type container does not exist');

    const selected = selectedType ??
        (scope === 'global' && parameter === 'tavg' ? 'anomaly' : Object.keys(returnTypes)[0]);

    const html = Object.entries({value: "Value", anomaly: "Anomaly", rank: "Rank", mean: "Mean", pctavg: "% of Average"}).map(([key, label]) => {
        const displayLabel = label;
        const checked = key === selected ? ' checked="checked"' : '';

        return `
        <span>
            <input type="radio" id="${key}" class="return-selection" name="return" value="${key}" aria-labelledby="return"${checked}>
            <label class="btn return-selection-label" title="${label}" for="${key}">${displayLabel}</label>
        </span>`;
    }).join('');

    container.innerHTML = html;
}