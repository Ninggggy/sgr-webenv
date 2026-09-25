export async function getGlobalNote(contentDir, section) {
    const notesElement = document.getElementById('form-notes');
    if (!notesElement) return;

    const cleanDir = contentDir.replace(/[^\w\-\/]/g, '');
    
    const fetchJson = async (fileName) => {
        const response = await fetch(`${cleanDir}/metadata/${fileName}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    };

    try {
        const [notesData, basePeriodsData] = await Promise.all([
            fetchJson('notes.json'),
            fetchJson('base-periods.json')
        ]);

        const { global: notes } = notesData;
        const { global: periods } = basePeriodsData;

        let text = section === 'mapping' ? notes.mapping : notes.default;

        if (text && text.length > 0) {
            const placeholders = {
                'GLOBAL_GRIDDED_BEGYEAR': periods.gridded.begyear,
                'GLOBAL_GRIDDED_ENDYEAR': periods.gridded.endyear,
                'GLOBAL_PCP_BEGYEAR': periods.pcp.begyear,
                'GLOBAL_PCP_ENDYEAR': periods.pcp.endyear,
                'GLOBAL_GLOBE_BEGYEAR': periods.globe.begyear,
                'GLOBAL_GLOBE_ENDYEAR': periods.globe.endyear
            };

            for (const [key, value] of Object.entries(placeholders)) {
                text = text.replace(new RegExp(`{{_${key}_}}`, 'g'), parseInt(value, 10));
            }

            notesElement.innerHTML = formattedMarkdown(text);
        } else {
            notesElement.remove();
        }

    } catch (error) {
        console.error('Failed to load global note:', error);
        notesElement.remove();
    }
}

export async function getUsNote(contentDir, scope, section) {
    const notesElement = document.getElementById('form-notes');
    if (!notesElement) return;

    const cleanDir = contentDir.replace(/[^\w\-\/]/g, '');
    const url = `${cleanDir}/metadata/notes.json`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const { us: usNotes } = await response.json();
        const noteArr = [];

        const scopeKeyMapping = {
            county: 'county',
            city: 'city',
            statewide: 'statewideDivisional',
            divisional: 'statewideDivisional',
            regional: 'regional'
        };

        const primaryKey = scopeKeyMapping[scope];
        if (primaryKey && primaryKey in usNotes) {
            noteArr.push(usNotes[primaryKey]);
        }

        const isCity = scope === 'city';
        const isMapping = section === 'mapping';
        const isTimeSeries = section === 'time-series';

        if (isCity && isMapping && 'cityMappingRanks' in usNotes) {
            noteArr.push(usNotes.cityMappingRanks);
        }

        if (!isCity && 'multiMonthPalmers' in usNotes) {
            noteArr.push(usNotes.multiMonthPalmers);
        }

        if (!isCity && (isMapping || isTimeSeries) && 'bulkDownload' in usNotes) {
            noteArr.push(usNotes.bulkDownload);
        }

        if (noteArr.length > 0) {
            const text = `Please note, ${noteArr.join(' ')}`;
            notesElement.innerHTML = formattedMarkdown(text);
        } else {
            notesElement.remove();
        }

    } catch (error) {
        console.error('Error handling US note:', error);
        notesElement.remove();
    }
}

function formattedMarkdown(text) {
    // sanitize text
    const sanitizerNode = document.createElement('div');
    sanitizerNode.textContent = text; // escapes any rogue HTML strings
    let safeString = sanitizerNode.innerHTML;

    // **text** --> <strong>text</strong>
    safeString = safeString.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // *text* --> <em>text</em>
    safeString = safeString.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // [text](url) --> <a href="url">text</a>
    safeString = safeString.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

    return safeString;
}

function htmlEncode(str) {
    return String(str).replace(
        /[^\w. ]/gi,
        function (c) {
            return '&#' + c.charCodeAt(0) + ';';
        }
    );
}