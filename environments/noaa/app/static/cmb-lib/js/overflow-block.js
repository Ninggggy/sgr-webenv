document.addEventListener('DOMContentLoaded', function(){
    overflowBlock();

    const target = document.getElementById('page-content');

    if (target) {
        const observer = new MutationObserver(overflowDebounce(mutations => {
            if (document.querySelectorAll('.overflow-block').length > 0) {
                overflowBlock();
            }
        }, 200));

        observer.observe(target, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class']
        });
    } else {
        console.warn('#page-content element not found.');
    }
});

function overflowBlock() {
    const overflowBlocks = document.querySelectorAll('.overflow-block');

    overflowBlocks.forEach(block => {
        // Wrap existing content of .overflow-block in .overflow-block-inner (if not already wrapped)
        let inner = block.querySelector('.overflow-block-inner');
        if (!inner) {
            inner = document.createElement('div');
            inner.classList.add('overflow-block-inner');
            while (block.firstChild) {
                inner.appendChild(block.firstChild);
            }
            block.appendChild(inner);
        }
        // Ensure the inner container scrolls.
        inner.style.overflow = 'auto';
        inner.style.webkitOverflowScrolling = 'touch';

        // Helper: Fade in a shadow element.
        function fadeInShadow(shadow) {
            // Cancel any pending fade-out by resetting opacity.
            shadow.style.opacity = '0';
            // Force reflow so the browser registers the starting opacity.
            shadow.offsetWidth;
            shadow.style.opacity = '1';
        }

        // Helper: Fade out a shadow element and remove it after transition.
        function fadeOutAndRemoveShadow(shadow) {
            shadow.style.opacity = '0';
            shadow.addEventListener('transitionend', function handler() {
                shadow.removeEventListener('transitionend', handler);
                if (shadow.parentNode) {
                    shadow.parentNode.removeChild(shadow);
                }
            });
        }

        function updateShadows() {
            const leftOverflow   = inner.scrollLeft > 0;
            const rightOverflow  = inner.scrollLeft + inner.clientWidth < inner.scrollWidth;
            const topOverflow    = inner.scrollTop > 0;
            const bottomOverflow = inner.scrollTop + inner.clientHeight < inner.scrollHeight;

            updateShadow('left', leftOverflow);
            updateShadow('right', rightOverflow);
            updateShadow('top', topOverflow);
            updateShadow('bottom', bottomOverflow);
        }
        function updateShadow(side, overflow){
            let shadow = block.querySelector(`.shadow-${side}`);
            if (overflow) {
                if (!shadow) {
                    shadow = document.createElement('div');
                    shadow.classList.add('overflow-block-shadow', `shadow-${side}`);
                    shadow.style.opacity = '0';
                    block.appendChild(shadow);
                    fadeInShadow(shadow);
                } else {
                    fadeInShadow(shadow);
                }
            } else if (shadow) {
                fadeOutAndRemoveShadow(shadow);
            }
        }

        // Create one debounced version of updateShadows.
        const debouncedUpdateShadows = overflowDebounce(updateShadows, 200);

        // Update shadows when scrolling.
        inner.addEventListener('scroll', updateShadows);
        // Update shadows on window resize.
        window.addEventListener('resize', debouncedUpdateShadows);
        // Update shadows when content changes
        const observer = new MutationObserver(() => {
            debouncedUpdateShadows();
        });
        observer.observe(inner, { childList: true, subtree: true, attributes: true });
        updateShadows();
    });
}

function overflowDebounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}
