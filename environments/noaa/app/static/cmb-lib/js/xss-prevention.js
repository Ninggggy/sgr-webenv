/**
 * How to prevent XSS client-side in JavaScript
 * https://portswigger.net/web-security/cross-site-scripting/preventing#how-to-prevent-xss-in-php
 */

/**
 * To escape user input in an HTML context in JavaScript, you need your own HTML encoder because JavaScript doesn't
 * provide an API to encode HTML. Here is some example JavaScript code that converts a string to HTML entities:
 * 
 * HTML Encoder use:
 * <script>document.body.innerHTML = htmlEncode(untrustedValue)</script>
 */
function htmlEncode(str) {
    return String(str).replace(
        /[^\w. ]/gi, 
        function (c) {
            return '&#' + c.charCodeAt(0) + ';';
        }
    );
}

/**
 * Escape HTML use:
 * <script>document.body.innerHTML = escapeHtml(untrustedValue)</script>
 */
function escapeHtml(str) {
    let escaped = document.createElement('textarea');
    escaped.textContent = str;
    return escaped.innerHTML;
}

function sanitizeHTML(str) {
    return str.replace(/[&<>"']/g, function(match) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[match];
    });
}

/**
 * If your input is inside a JavaScript string, you need an encoder that performs Unicode escaping.
 * 
 * Unicode-encoder use:
 * <script>document.write('<script>x="' + jsEscape(untrustedValue) + '";<\/script>')</script>
 */
function jsEscape (str) {
    return String(str).replace(
        /[^\w. ]/gi,
        function (c) {
            return '\\u' + ('0000' + c.charCodeAt(0).toString(16)).slice(-4);
        }
    );
}

function sanitizeUrl (url) {
    let tempElement = document.createElement('a');
    tempElement.href = url;

    if (tempElement.protocol === 'https:' || tempElement.protocol === 'http:') {
        return url;
    } else {
        return '';
    }
}
