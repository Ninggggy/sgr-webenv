export function valuesTableSorter(tableSelector, section) {
    const $table = $(tableSelector);

    $table.tablesorter({
        // This tells tablesorter to only treat the "leaf" header cells as sortable
        // It ignores the parent colspan headers automatically.
        selectorHeaders: '> thead tr:last-child th, > thead tr:first-child th[rowspan]',

        textExtraction: function(node) {
            const $node = $(node);
            const sortVal = $node.data('sortval');
            
            // 1. Use data attribute if present (fastest/most accurate)
            if (sortVal !== undefined && sortVal !== null) {
                return sortVal;
            }

            // 2. Fallback to text cleaning
            let txt = $node.text().trim();
            if (txt && !/^[a-zA-Z]/.test(txt)) {
                return txt.replace('--', '').replace(/[^-\.\d]/g, '');
            }
            return txt;
        },

        // Force the numeric parser globally for safety (Optional)
        headerTemplate: '{content}',

        // Use the built-in zebra widget
        widgets: ['zebra', 'columns'],
        widgetOptions: {
            zebra: ["even", "odd"]
        },

        emptyTo: 'bottom',
        theme: 'none',
        sortReset: true,
        sortRestart: true,
        sortInitialOrder: 'desc',

        // Default sort: first column
        sortList: [[0, section === 'mapping' ? 0 : 1]]
    });
}

export function citiesTableSorter(tableSelector){
    $(tableSelector).tablesorter({
        textExtraction: function(node) {
            var txt;
            if ($(node).data('sortval')) {
                txt = $(node).data('sortval')
            } else {
                txt = $(node).text();
                if (!txt.match(/^[a-zA-Z]/)){
                    txt = txt.
                        replace('--', '').
                        replace(new RegExp(/[^-\.\d]/g), '');
                }
            }
            return txt;
        },
        emptyTo     : 'bottom',
        theme       : 'none',
        widgets     : ['columns'],
        sortReset   : true,
        sortRestart : true,
        // initial sort on the second column in ascending order
        sortList: [[1,0]]
    });
}
