import { cag, base, scopes, sections, section } from '../globals.js';

export function initHome() {
    if (section === 'background') {
        $('html, body').stop().animate({'scrollTop': $("#background").offset().top}, 500, 'swing');
    }

    loadScopes();

    // Tutorial Videos
    const videoModal = document.getElementById('videoModal');
    const videoPlayer = document.getElementById('videoPlayer');
    const videoBtns = document.querySelectorAll('.video-btn');
    let lastUrl = window.location.href;

    // Enable buttons and bind clicks only after load
    window.addEventListener('load', () => {
        videoBtns.forEach(btn => {
            btn.classList.remove('disabled');

            btn.addEventListener('click', function () {
                const src = this.getAttribute('data-src');
                videoPlayer.querySelector('source').setAttribute('src', src);
                videoPlayer.load();
                videoPlayer.play();

                lastUrl = window.location.href;
                history.pushState({ modalOpen: true }, '', src);
            });
        });
    });

    // Stop video & restore URL when modal closes
    videoModal.addEventListener('hidden.bs.modal', function () {
        videoPlayer.pause();
        videoPlayer.currentTime = 0;
        videoPlayer.querySelector('source').setAttribute('src', '');
        history.pushState({}, '', lastUrl);
    });

    // Close modal if user presses Back
    window.addEventListener('popstate', (event) => {
        if (!event.state || !event.state.modalOpen) {
            const modal = bootstrap.Modal.getInstance(videoModal);
            if (modal) modal.hide();
        }
    });
}

function loadScopes() {
    $('#home-link a').attr('href', `${base}/`);
    Object.keys(scopes).forEach(sk => {
        $(`#scope-${sk} a`).attr('href', `${base}/${sk}`);
    });

    showScope(cag.variables.homeScope);

    $('#scopes li a:not(#home-link)').on('click', function(e) {
        e.preventDefault();

        const clickedScope = $(this).data('scope');

        if (clickedScope !== 'home') {
            cag.variables.homeScope = clickedScope;
        }

        const newPath = `${base}/${clickedScope !== 'home' ? clickedScope : ''}`;
        history.pushState(null, null, newPath);

        showScope(clickedScope);
    });
}

function showScope(homeScope) {
    $('#scopes li:not(#home-link)').removeClass('selected');
    $(`#scope-${homeScope}`).addClass('selected');

    $.each(sections, function(scopeSection, name){
        const title = `${scopes[homeScope]} ${sections[scopeSection]}`;
        const $scopeSection = $(`#${scopeSection}`);

        $scopeSection
            .attr('href', `${base}/${homeScope}/${scopeSection}`)
            .attr('title', title);
        $(`#${scopeSection}`).find('.card-description').text(title);
    });

    const dataInfoTitle = `${scopes[homeScope]} Data Info`;
    $('#data-info-toggle').attr({
        'href': `${base}/${homeScope}/data-info`,
        'title': dataInfoTitle
    });
    $('#data-info-description').text(dataInfoTitle);

    $('.background').removeClass('selected');
    $('#' + (homeScope === 'global' ? 'global' : 'us') + '-background').addClass('selected');
}
