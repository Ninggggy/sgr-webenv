const notes = {
    'tie': {
        'symbol': '*',
        'text': 'Tie in ranking'
    },
    'insufficient-variability': {
        'symbol': '**',
        'text': 'Ties &gt;10% of the record'
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('#designations');
    if (!container) return; // nothing to do

    // Ensure container is a <ul>
    let ul;
    if (container.tagName.toLowerCase() !== 'ul') {
        ul = document.createElement('ul');
        const cn = container.className;
        // move children into new UL
        while (container.firstChild) {
            ul.appendChild(container.firstChild);
        }
        container.replaceWith(ul);
        ul.id = 'designations';
        ul.className = cn;
    } else {
        ul = container;
    }
    ul.innerHTML = '';

    // Ensure UL has .hidden
    ul.classList.add('hidden', 'small', 'italic', 'dk-gray-txt');

    // Build LI elements for each note
    for (const [key, attr] of Object.entries(notes)) {
        let li = ul.querySelector(`#${key}-designation`);
        if (!li) {
            li = document.createElement('li');
            li.id = `${key}-designation`;
            ul.appendChild(li);
        }
        li.classList.add('hidden');
        li.innerHTML = `
            <span class="designation-symbol inline-block right">${attr.symbol}</span>
            ${attr.text}
        `;
    }
});

export function setDesignation(numTies = 0, isInsufficient = false, scope = '', returnType = 'rank') {
    if (scope === 'city' || returnType !== 'rank' || numTies === 0) {
        return '';
    }

    const className = `${isInsufficient ? 'insufficient-variability' : 'tie'}`;
    const marker = notes[className].symbol;

    return `<span class="designation ${className}">${marker}</span>`;
}
