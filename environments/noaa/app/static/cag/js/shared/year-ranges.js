import MinMaxDateDao from './dao/MinMaxDateDao.js';
import { cag, scope, section, basePeriods } from '../globals.js';
import Util from '../utils/util.js';
import noUiSlider from '../../assets/noUiSlider-15.8.1/nouislider.min.module.js';

const { city: isCity } = Util.scope.is;

const locWithContext = Util.location.withContext(scope, section);
const {
    alaska: isAlaska,
    hawaii: isHawaii
} = locWithContext.is;

let isFirstInit = true;
let lastLocation = null;
let lastParameter = null;

export function initYearRange(location = null, parameter = null) {
    // Historical selector order and year dropdown from the saved CAG page.
    if (section === "mapping") {
        const el=document.getElementById("year"); const chosen=el.value || cag.variables.year;
        el.innerHTML=Array.from({length:132},(_,i)=>`<option value="${2026-i}">${2026-i}</option>`).join(""); el.value=chosen; return;
    }

    const isContextChange = !isFirstInit && (lastLocation !== location || lastParameter !== parameter);
    lastLocation = location;
    lastParameter = parameter;

    const dateDao = new MinMaxDateDao();

    const scopeKey = scope === 'global' ? 'global' : 'national';
    const firstDate = dateDao.getFirstDate(scopeKey);
    const lastDate = dateDao.getLastDate(scopeKey);
    const firstYear = Number(String(firstDate).slice(0, 4));
    const lastYear = Number(String(lastDate).slice(0, 4));

    const minDate = dateDao.getMinDate(scope, section, parameter, location);
    const maxDate = dateDao.getMaxDate(scope, parameter);
    const minYear = Number(String(minDate).slice(0, 4));
    const maxYear = Number(String(maxDate).slice(0, 4));

    // Helper to force values within the new valid range
    const clamp = (val, min, max) => Math.max(min, Math.min(max, Number(val)));

    const getSelectedYear = (inputId, globalVar, porBound) => {
        const inputElem = document.getElementById(inputId);
        if (!inputElem) return globalVar;

        // On initial load, use URL variables or HTML defaults
        if (isFirstInit) return inputElem.value || globalVar;

        // If user manually touched input, keep their selection
        if (inputElem.dataset.userModified === 'true') return inputElem.value;

        // If location/parameter changed and user hasn't locked a custom value, snap to POR
        if (isContextChange) return porBound;

        // Otherwise (e.g., chart click updated UI without changing location), respect current value
        return inputElem.value || globalVar;
    };

    const defaulBasePeriod = getDefaultBasePeriod(scope, location, parameter);
    const { begyear: defaultBegBaseYear, endyear: defaultEndBaseYear } = defaulBasePeriod;

    if (section === 'time-series') {
        const periodSlider = document.getElementById('period-slider');

        let selectedBegYear = getSelectedYear('begyear', cag.variables.begyear, minYear);
        let selectedEndYear = getSelectedYear('endyear', cag.variables.endyear, maxYear);

        // Clamp bounds before sending to slider
        selectedBegYear = clamp(selectedBegYear, minYear, maxYear);
        selectedEndYear = clamp(selectedEndYear, minYear, maxYear);

        initYearSlider(periodSlider, firstYear, lastYear, minYear, maxYear, [selectedBegYear, selectedEndYear], true, ['begyear', 'endyear']);
        sliderListener(periodSlider, ['begyear', 'endyear'], minYear, maxYear);

        const basePeriodSlider = document.getElementById('base-period-slider');

        // 3rd argument: if untouched by the user, snap to defaultBegBaseYear / defaultEndBaseYear
        let rawBegBaseYear = getSelectedYear('begbaseyear', cag.variables.begBaseYear, defaultBegBaseYear);
        let rawEndBaseYear = getSelectedYear('endbaseyear', cag.variables.endBaseYear, defaultEndBaseYear);

        // Clamp bounds before sending to slider
        const selectedBegBaseYear = clamp(rawBegBaseYear, minYear, maxYear);
        const selectedEndBaseYear = clamp(rawEndBaseYear, minYear, maxYear);

        initYearSlider(basePeriodSlider, firstYear, lastYear, minYear, maxYear, [selectedBegBaseYear, selectedEndBaseYear], true, ['begbaseyear', 'endbaseyear']);
        sliderListener(basePeriodSlider, ['begbaseyear', 'endbaseyear'], minYear, maxYear);

        // Check if the slider should be disabled upon creation
        const basePrdCheckbox = document.getElementById('base_prd');
        if (basePrdCheckbox && !basePrdCheckbox.checked) {
            basePeriodSlider.setAttribute('disabled', true);
            basePeriodSlider.querySelectorAll('.noUi-handle').forEach(handle => handle.setAttribute('tabindex', '-1'));
        }

        if (document.getElementById('base-period-slider')) {
            const didReset = setDefaultBasePeriod(location, parameter, minYear, maxYear, rawBegBaseYear, rawEndBaseYear);

            if (!didReset) {
                const begInput = document.getElementById('begbaseyear');
                const endInput = document.getElementById('endbaseyear');
                if (begInput && parseInt(begInput.value, 10) !== selectedBegBaseYear) {
                    begInput.value = selectedBegBaseYear;
                    setTimeout(() => begInput.dispatchEvent(new Event('change', { bubbles: true })), 0);
                }
                if (endInput && parseInt(endInput.value, 10) !== selectedEndBaseYear) {
                    endInput.value = selectedEndBaseYear;
                    setTimeout(() => endInput.dispatchEvent(new Event('change', { bubbles: true })), 0);
                }
            }
        }

        const trendPeriodSlider = document.getElementById('trend-period-slider');

        let selectedBegTrendYear = getSelectedYear('begtrendyear', cag.variables.begtrendyear, minYear);
        let selectedEndTrendYear = getSelectedYear('endtrendyear', cag.variables.endtrendyear, maxYear);

        selectedBegTrendYear = clamp(selectedBegTrendYear, minYear, maxYear);
        selectedEndTrendYear = clamp(selectedEndTrendYear, minYear, maxYear);

        // Clamp bounds before sending to slider
        selectedBegTrendYear = clamp(selectedBegTrendYear, minYear, maxYear);
        selectedEndTrendYear = clamp(selectedEndTrendYear, minYear, maxYear);

        initYearSlider(trendPeriodSlider, firstYear, lastYear, minYear, maxYear, [selectedBegTrendYear, selectedEndTrendYear], true, ['begtrendyear', 'endtrendyear']);
        sliderListener(trendPeriodSlider, ['begtrendyear', 'endtrendyear'], minYear, maxYear);

        const trendCheckbox = document.getElementById('trend');
        if (trendCheckbox && !trendCheckbox.checked) {
            trendPeriodSlider.setAttribute('disabled', true);
            trendPeriodSlider.querySelectorAll('.noUi-handle').forEach(handle => handle.setAttribute('tabindex', '-1'));
        }
    } else {
        const yearSlider = document.getElementById('single-year-slider');

        let rawSelectedYear = getSelectedYear('year', cag.variables.year, maxYear);

        // Clamp bounds before sending to slider
        let selectedYear = clamp(rawSelectedYear, minYear, maxYear);

        // If the value had to be clamped, sync it back to the input and broadcast the change
        if (Number(rawSelectedYear) !== selectedYear && document.getElementById('year')) {
            const inputElem = document.getElementById('year');
            inputElem.value = selectedYear;

            // Dispatch for external listeners
            setTimeout(() => {
                inputElem.dispatchEvent(new Event('change', { bubbles: true }));
            }, 0);
        }

        initYearSlider(yearSlider, firstYear, lastYear, minYear, maxYear, [selectedYear], false, ['year']);
        sliderListener(yearSlider, ['year'], minYear, maxYear);
    }

    isFirstInit = false;
}

function sliderListener(sliderElem, inputIds, minYear, maxYear) {
    if (!sliderElem || !sliderElem.noUiSlider) return;

    // Track user intent continuously while dragging
    sliderElem.noUiSlider.on('slide', function () {
        inputIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.dataset.userModified = 'true';
        });
    });

    // Update hidden text boxes visually (DO NOT dispatch change here!)
    sliderElem.noUiSlider.on('update', function (values) {
        inputIds.forEach((id, index) => {
            const inputElem = document.getElementById(id);
            if (inputElem) {
                inputElem.value = Math.round(values[index]);
            }
        });
    });

    // Fire application update exactly ONCE when drag drops OR track is tapped
    sliderElem.noUiSlider.on('change', function () {
        inputIds.forEach((id) => {
            const inputElem = document.getElementById(id);
            if (inputElem) {
                // Ensure track taps register as intentional user modifications
                inputElem.dataset.userModified = 'true';
                inputElem.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    });

    // Update slider on manual year input text change
    inputIds.forEach((id, index) => {
        const inputElem = document.getElementById(id);
        if (inputElem) {
            if (minYear !== undefined) inputElem.min = minYear;
            if (maxYear !== undefined) inputElem.max = maxYear;

            // Fires on every keystroke
            inputElem.addEventListener('input', function () {
                this.dataset.userModified = 'true';

                let newValue = parseInt(this.value, 10);

                if (newValue >= minYear && newValue <= maxYear) {
                    if (inputIds.length === 2) {
                        let newSliderValues = [null, null];
                        newSliderValues[index] = newValue;
                        sliderElem.noUiSlider.set(newSliderValues);
                    } else {
                        sliderElem.noUiSlider.set(newValue);
                    }
                }
            });

            // FALLBACK: Fires when clicking away or hitting Enter
            inputElem.addEventListener('change', function () {
                this.dataset.userModified = 'true';

                let newValue = parseInt(this.value, 10);

                if (inputIds.length === 2) {
                    let newSliderValues = [null, null];
                    newSliderValues[index] = newValue;
                    sliderElem.noUiSlider.set(newSliderValues);
                } else {
                    sliderElem.noUiSlider.set(newValue);
                }
            });
        }
    });
}

export function initYearSlider(sliderElem, firstYear, lastYear, minYear, maxYear, startPositions, isDual = false, inputIds = []) {
    if (!sliderElem) return;

    if (sliderElem.noUiSlider) {
        sliderElem.noUiSlider.destroy();
    }

    const paddingLeft = minYear - firstYear;
    const paddingRight = lastYear - maxYear;
    const tooltipFormat = { to: value => String(Math.round(value)) };

    noUiSlider.create(sliderElem, {
        start: startPositions,
        connect: isDual ? true : 'lower',
        step: 1,
        range: { min: firstYear, max: lastYear },

        padding: [paddingLeft, paddingRight],

        tooltips: isDual ? [tooltipFormat, tooltipFormat] : [tooltipFormat],
        format: {
            to: value => Math.round(value),
            from: value => Number(value)
        },
        pips: {
            mode: 'count',
            values: 6,
            density: 3,
            format: {
                to: value => String(Math.round(value))
            }
        }
    });

    // ARIA Labels (for Screen Readers)
    const handles = sliderElem.querySelectorAll('.noUi-handle');
    if (handles.length === 2) {
        handles[0].setAttribute('aria-label', 'Start Year');
        handles[1].setAttribute('aria-label', 'End Year');
    } else if (handles.length === 1) {
        handles[0].setAttribute('aria-label', 'Selected Year');
    }

    const applyTooltipStyles = () => {
        const isSmallSlider = sliderElem.id === 'base-period-slider' || sliderElem.id === 'trend-period-slider';
        const topOffset = isSmallSlider ? '28px' : '38px';

        sliderElem.querySelectorAll('.noUi-tooltip').forEach(tt => {
            tt.style.setProperty('font-size', '0.75rem', 'important');
            tt.style.setProperty('line-height', '1', 'important');
            tt.style.setProperty('padding', '4px 6px', 'important');
            tt.style.setProperty('background', '#00569c', 'important');
            tt.style.setProperty('color', 'white', 'important');
            tt.style.setProperty('border', '1px solid #162e51', 'important');
            tt.style.setProperty('border-radius', '4px', 'important');
            tt.style.setProperty('opacity', '1', 'important');
            tt.style.setProperty('box-shadow', '0 2px 4px rgba(0,0,0,0.3)', 'important');
            tt.style.setProperty('position', 'absolute', 'important');
            tt.style.setProperty('bottom', 'auto', 'important');
            tt.style.setProperty('top', topOffset, 'important');
            tt.style.setProperty('left', '50%', 'important');
            tt.style.setProperty('transform', 'translate(-50%, 0)', 'important');
            tt.style.setProperty('z-index', '100', 'important');
            tt.style.setProperty('display', 'block', 'important');
        });
    };

    applyTooltipStyles();

    sliderElem.noUiSlider.on('update', applyTooltipStyles);

    // MASTER CLICK INTERCEPTOR (Uses capture phase 'true' to beat library logic)
    sliderElem.addEventListener('pointerdown', function(e) {
        if (sliderElem.hasAttribute('disabled')) return;

        // Let handles (dragging) and pips (custom clicks) work normally
        if (e.target.closest('.noUi-handle') || e.target.closest('.noUi-value') || e.target.closest('.noUi-marker')) {
            return;
        }

        const base = sliderElem.querySelector('.noUi-base');
        if (!base) return;

        const rect = base.getBoundingClientRect();

        // Ignore clicks completely outside the actual track width
        if (e.clientX < rect.left || e.clientX > rect.right) return;

        // Calculate exact year
        const pct = (e.clientX - rect.left) / rect.width;
        const clickedYear = Math.round(firstYear + ((lastYear - firstYear) * pct));

        // If click is in valid range, force the update
        if (clickedYear >= minYear && clickedYear <= maxYear) {

            // Stop the library from swallowing or reverting the click
            e.stopPropagation();
            e.preventDefault();

            if (isDual) {
                const currentValues = sliderElem.noUiSlider.get().map(Number);
                const dist1 = Math.abs(currentValues[0] - clickedYear);
                const dist2 = Math.abs(currentValues[1] - clickedYear);

                if (dist1 <= dist2) {
                    sliderElem.noUiSlider.set([clickedYear, null]);
                } else {
                    sliderElem.noUiSlider.set([null, clickedYear]);
                }
            } else {
                sliderElem.noUiSlider.set(clickedYear);
            }

            // Update inputs and broadcast change
            setTimeout(() => {
                inputIds.forEach(id => {
                    const inputElem = document.getElementById(id);
                    if (inputElem) {
                        inputElem.dataset.userModified = 'true';
                        inputElem.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
            }, 0);
        }
    }, true); // <- The 'true' here is the secret sauce (Capture Phase)

    styleDisabledPips(sliderElem, minYear, maxYear, firstYear, lastYear, isDual, inputIds);

    const totalRange = lastYear - firstYear;
    const leftPct = ((minYear - firstYear) / totalRange) * 100;
    const rightPct = 100 - (((lastYear - maxYear) / totalRange) * 100);

    // Apply a linear gradient: Disabled color -> Enabled color -> Disabled color
    sliderElem.style.background = `linear-gradient(to right,
        #ededed 0%, #ededed ${leftPct}%,
        #c6cace ${leftPct}%, #c6cace ${rightPct}%,
        #ededed ${rightPct}%, #ededed 100%)`;

    return sliderElem.noUiSlider;
}

function styleDisabledPips(sliderElem, minYear, maxYear, firstYear, lastYear, isDual, inputIds) {
    // Make the container transparent to clicks so the track underneath works
    const pipsContainer = sliderElem.querySelector('.noUi-pips');
    if (pipsContainer) {
        pipsContainer.style.pointerEvents = 'none';
    }

    // Helper function to re-enable clicks on specific elements and bind the update logic
    const makeInteractive = (elem, pipVal) => {
        elem.style.pointerEvents = 'auto';

        if (pipVal >= minYear && pipVal <= maxYear) {
            elem.style.cursor = 'pointer';

            elem.onclick = function () {
                if (sliderElem.hasAttribute('disabled')) return;

                if (isDual) {
                    const currentValues = sliderElem.noUiSlider.get().map(Number);
                    const distanceToHandle1 = Math.abs(currentValues[0] - pipVal);
                    const distanceToHandle2 = Math.abs(currentValues[1] - pipVal);

                    if (distanceToHandle1 <= distanceToHandle2) {
                        sliderElem.noUiSlider.set([pipVal, null]);
                    } else {
                        sliderElem.noUiSlider.set([null, pipVal]);
                    }
                } else {
                    sliderElem.noUiSlider.set(pipVal);
                }

                // Programmatically trigger our custom 'change' pipeline directly on the DOM inputs
                setTimeout(() => {
                    inputIds.forEach(id => {
                        const inputElem = document.getElementById(id);
                        if (inputElem) {
                            inputElem.dataset.userModified = 'true';
                            inputElem.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    });
                }, 0);
            };
        } else {
            elem.style.cursor = 'not-allowed';
            elem.onclick = null;
        }
    };

    // Style and bind text labels (.noUi-value)
    sliderElem.querySelectorAll('.noUi-value').forEach(pip => {
        const pipVal = Number(pip.getAttribute('data-value'));

        if (pipVal < minYear || pipVal > maxYear) {
            pip.classList.add('disabled-pip');
        } else {
            pip.classList.remove('disabled-pip');
        }

        makeInteractive(pip, pipVal);
    });

    // Style and bind tick marks (.noUi-marker)
    sliderElem.querySelectorAll('.noUi-marker').forEach(marker => {
        const pctLeft = parseFloat(marker.style.left);
        const pipVal = Math.round(firstYear + ((lastYear - firstYear) * (pctLeft / 100)));

        if (pipVal < minYear || pipVal > maxYear) {
            marker.classList.add('disabled-marker');
        } else {
            marker.classList.remove('disabled-marker');
        }

        makeInteractive(marker, pipVal);
    });
}

export function updateSliderBounds(sliderElem, newMin, newMax, newStartPositions) {
    if (!sliderElem || !sliderElem.noUiSlider) return;

    sliderElem.noUiSlider.updateOptions({
        range: { min: newMin, max: newMax },
        start: newStartPositions,
        pips: {
            mode: 'count',
            values: 6,
            density: 3,
            format: {
                to: value => String(Math.round(value))
            }
        }
    });
}

function getDefaultBasePeriod(scope, location, parameter) {
    let key, scopeKey;
    if (scope === 'global') {
        scopeKey = 'global';
        key = parameter === 'pcp' ? 'pcp' : (location === 'coords' ? 'gridded' : 'globe');
    } else {
        scopeKey = 'national';
        key = isCity(scope) ? 'city' :
              isAlaska(location) ? 'alaska' :
              isHawaii(location) ? 'hawaii' :
              'conus';
    }

    return basePeriods[scopeKey][key];
}

function setDefaultBasePeriod(location, parameter, dataStartYear, dataEndYear, intendedBegBase, intendedEndBase) {
    const baseSliderElem = document.getElementById('base-period-slider');
    if (!baseSliderElem || !baseSliderElem.noUiSlider) return false; // Return false here

    const selectedBegBaseYear = parseInt(intendedBegBase, 10);
    const selectedEndBaseYear = parseInt(intendedEndBase, 10);
    const minValidYear = parseInt(dataStartYear, 10);
    const maxValidYear = parseInt(dataEndYear, 10);

    const defaultBasePeriod = getDefaultBasePeriod(scope, location, parameter);
    const { begyear: defaultBegBaseYear, endyear: defaultEndBaseYear } = defaultBasePeriod;

    // If out of bounds, snap SLIDER to default
    if (selectedBegBaseYear < minValidYear || selectedEndBaseYear > maxValidYear) {
        baseSliderElem.noUiSlider.set([defaultBegBaseYear, defaultEndBaseYear]);

        const begInput = document.getElementById('begbaseyear');
        const endInput = document.getElementById('endbaseyear');

        if (begInput) {
            begInput.value = defaultBegBaseYear;
            delete begInput.dataset.userModified;
        }
        if (endInput) {
            endInput.value = defaultEndBaseYear;
            delete endInput.dataset.userModified;
        }

        setTimeout(() => {
            if (begInput) begInput.dispatchEvent(new Event('change', { bubbles: true }));
            if (endInput) endInput.dispatchEvent(new Event('change', { bubbles: true }));
        }, 0);

        return true;
    }

    return false;
}