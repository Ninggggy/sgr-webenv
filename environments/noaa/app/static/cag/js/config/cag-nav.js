import { base, scopes, sections, section, scope } from '../globals.js';

export function setupNav() {
    $(document).ready(function(){
        $('.skip-to-main').click(function(){
            skipToMain('section-title');
            return false;
        })

        getNav(base, scopes, scope, sections, section);
        navFunction();
    });

    function getNav(base, scopes, scope, sections, section) {
        const nav = document.createElement('nav');
        nav.id = 'cag-nav';

        const scopesList = document.createElement('ul');
        scopesList.id = 'scopes';
        scopesList.className = 'tabs';
        scopesList.setAttribute('role', 'combobox');

        const homeItem = document.createElement('li');
        homeItem.id = 'scope-home';

        const homeLink = document.createElement('a');
        homeLink.id = 'home-link';
        homeLink.title = 'Climate at a Glance Home';
        homeLink.href = `${base}/${scope}`;
        homeLink.innerHTML = `<i class="fa-solid fa-house"></i>`;
        homeItem.appendChild(homeLink);

        scopesList.appendChild(homeItem);

        for (const [scopeKey, scopeName] of Object.entries(scopes)) {
            const scopeItem = document.createElement('li');
            const scopeLink = document.createElement('a');

            const scopeShortName = {
                Global: 'Globe',
                National: 'Nation',
                Regional: 'Region',
                Statewide: 'State',
                Divisional: 'Division',
            }[scopeName] || scopeName;

            scopeItem.id = `scope-${scopeKey}`;
            scopeItem.setAttribute('aria-controls', `${scopeKey}-nav`);
            if (scopeKey === scope) {
                scopeItem.className = 'selected';
            }

            scopeLink.className = 'scope-item';
            scopeLink.dataset.scope = scopeKey;
            scopeLink.href = `${base}/${scopeKey}`;
            scopeLink.title = scopeName;
            scopeLink.innerHTML = `${scopeShortName} <i class="click-icon small fa-solid fa-angle-down"></i>`;

            scopeItem.appendChild(scopeLink);

            if (scopeKey !== scope) {
                const sectionMenu = getSectionMenu(base, section, scopeKey, scope, scopeName, sections, false);
                scopeItem.appendChild(sectionMenu);
            }

            scopesList.appendChild(scopeItem);
        }

        const finalSectionMenu = getSectionMenu(base, section, scope, scope, scopes[scope], sections, true);
        nav.appendChild(scopesList);
        nav.appendChild(finalSectionMenu);

        $('#page-content').prepend(nav.outerHTML);
        navFunction();
    }

    function getSectionMenu(base, selectedSection, scope, selectedScope, scopeName, sections, selected) {
        const sectionMenu = document.createElement('ul');
        sectionMenu.id = `${scope}-nav`;
        sectionMenu.setAttribute('aria-label', `${scope}-nav`);
        sectionMenu.setAttribute('role', 'listbox');
        sectionMenu.className = `${selected ? 'tabs selected-' : ''}section-menu${scope === selectedScope ? ' selected-scope' : ''}`;

        for (const [sectionKey, sectionName] of Object.entries(sections)) {
            if (sectionKey === 'data-info' || sectionKey === 'background') {
                continue;
            }

            const sectionItem = document.createElement('li');
            const sectionLink = document.createElement('a');

            sectionItem.id = `${scope}-${sectionKey}`;
            sectionItem.setAttribute('aria-labelledby', `${scope}-nav`);
            if (scope === selectedScope && sectionKey === selectedSection) {
                sectionItem.className = 'selected';
            }

            sectionLink.title = `${scopeName} ${sectionName}`;
            sectionLink.href = `${base}/${scope}/${sectionKey}`;
            sectionLink.dataset.section = sectionKey;

            if (scope === selectedScope && sectionKey === 'data-info') {
                sectionLink.setAttribute('data-bs-toggle', 'modal');
                sectionLink.setAttribute('data-bs-target', '#info');
            }

            sectionLink.textContent = `${scopeName} ${sectionName}`;
            sectionItem.appendChild(sectionLink);
            sectionMenu.appendChild(sectionItem);
        }

        return sectionMenu;
    }

    function navFunction(){
        // if off menu click, close all section menus
        $(window).click(function() {
            closeSectionMenus();
        });

        // don't follow selected section link
        $('.section-menu > li.selected > a').click(function(){
            //closeSectionMenus();
            return false;
        });

        $('nav#cag-nav #scopes li > a.scope-item').unbind().click(function(){
            if (
                $(this).parent('li').hasClass('selected') ||
                $('#' + $(this).data('scope') + '-nav').is(':visible')
            ) {
                // if clicked scope's section menu is:visible, close it
                closeSectionMenus();
                $(this).parent('li').attr('aria-expanded', false);
            } else {
                // display clicked scope's section menu
                closeSectionMenus();
                $('#' + $(this).data('scope') + '-nav').addClass('selected');
                $('#' + $(this).data('scope') + '-nav').show();
                $('#scope-' + $(this).data('scope') + ' i.fa-solid').removeClass('fa-angle-down');
                $('#scope-' + $(this).data('scope') + ' i.fa-solid').addClass('fa-angle-up');
                $(this).parent('li').attr('aria-expanded', true);
            }

            return false;
        });
    }

    function closeSectionMenus(){
        $('.section-menu').hide();
        $('.section-menu').removeClass('selected');
        $('#scopes li i.fa-solid').removeClass('fa-angle-up');
        $('#scopes li i.fa-solid').addClass('fa-angle-down');
    }
}