import { scopes, sections } from '../globals.js';

export function setBreadcrumb(path, scope, section) {
    if (!(scope in scopes) || !(section in sections)) {
        return false;
    }

    const scopeName = scopes[scope];
    const sectionName = sections[section];

    path = String(path).replace(/[^a-zA-Z\-\/]/g, '');

    $('.app-breadcrumb-item:last-of-type').remove();
    $('.app-breadcrumbs').append(`
        <li class="app-breadcrumb-item"><a href="${path}/">Climate at a Glance</a></li>
        <li class="app-breadcrumb-item">
            <a href="${path}/${scope}/${section}">
                ${scopeName} ${sectionName}
            </a>
        </li>
    `);
    $('.product-name h1').text(`Climate at a Glance ${scopeName} ${sectionName}`);
}