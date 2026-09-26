// for debugging
function getAttributes($node) {
    $.each($node[0].attributes, function(index, attribute) {
        console.log(attribute.name + ':' + attribute.value);
    });
}

function cursor_wait() {
    document.body.style.cursor = 'wait';
}

function cursor_auto() {
    document.body.style.cursor = 'auto';
}

window.onload = hideAllMenus;
//used in unirule (hamap and prosite) and in pratt, e.g. https://hamap.expasy.org/hamap_scan_userman.html
function showMenu(menuNumber) {
    hideAllMenus();
    if (document.getElementById('menu' + menuNumber)) {
        document.getElementById('menu' + menuNumber).style.display = 'block';
    }
}
//used in unirule (hamap and prosite) and in pratt, e.g. https://hamap.expasy.org/hamap_scan_userman.html
function hideAllMenus() {
    for (var i = 1;i <= 10;i++) {
        if (document.getElementById('menu' + i)) {
            document.getElementById('menu' + i).style.display = 'none';
        }
    }
}

// does not work if put after it is used in document
// used each time ':regex' appears
// used in pratt.js, scanprosite.js, nicesite.js and graphical_view.js
jQuery.expr[':'].regex = function(elem, index, match) {
    var matchParams = match[3].split(','), validLabels = /^(data|css):/, attr = {
        method: matchParams[0].match(validLabels) ? matchParams[0].split(':')[0]
            : 'attr',
        property: matchParams.shift().replace(validLabels, '')
    }, regexFlags = 'ig', regex = new RegExp(matchParams.join('').replace(
        /^\s+|\s+$/g, ''), regexFlags);
    return regex.test(jQuery(elem)[attr.method](attr.property));
}

// for menu items that have a sub-menu e.g "Proteomes" in https://hamap.expasy.org/
// if the sub-menus are shown the link of the main item that has a sub-menu is deactivated
// "sub-menus shown" means that for menu items that have a sub-menu, on mouseover of the menu item triggers the display of its sub-menu
// "sub-menus hidden" means that for menu items that have a sub-menu, sub-menus are not displayed


// window width < 600px
// menu-2-items e.g. https://web.expasy.org/variant_pages/
// -1/2 row with logo and optionally title 
// -1/2 row with menu
// -sub-menus shown
// menu-3-items e.g. https://web.expasy.org/translate/
// -1/2 row with logo and optionally title (title for https://web.expasy.org/translate/)
// -1/2 row with menu
// -sub-menus hidden
// menu-4-items e.g. https://web.expasy.org/glycomod/
// -1/2 row with logo and optionally title (title for https://web.expasy.org/glycomod/)
// -1/2 row with menu
// -sub-menus hidden
// menu-5-items nothing
// menu-6-items - cello only: https://www.cellosaurus.org/
// -1/2 row with cello logo and expasy logo
// -1/2 row with menu - Exception: only 4/6 menu items are shown
// -sub-menus hidden
// menu-6-items - not cello e.g. https://enzyme.expasy.org/
// -1/2 row with logo and optionally title (title for enzyme)
// -1/2 row with menu
// -sub-menus hidden
// menu-7-items e.g. https://world-2dpage.expasy.org/
// -1/2 row with logo and optionally title (title for world-2dpage)
// -1/2 row with menu
// -sub-menus hidden
// menu-8-items e.g. https://prosite.expasy.org/
// -1/2 row with logo and optionally title (no title for prosite)
// -1/2 row with menu
// -sub-menus hidden
// menu-9-items e.g. https://hamap.expasy.org/
// -1/2 row with logo and optionally title (no title for hamap)
// -1/2 row with menu
// -sub-menus hidden

// window width >= 600px: changes
// menu-6-items - cello only: https://www.cellosaurus.org/
// width of the row holding the menu is changed from "auto" to "2rem"

// window width >= 900px
//menu-3-items e.g. https://web.expasy.org/translate/
//-sub-menus shown
//menu-4-items e.g. https://web.expasy.org/glycomod/
//-sub-menus shown
//menu-6-items - cello only: https://www.cellosaurus.org/
//-all menu items are shown 
//-sub-menus shown

//window width >= 1200px
//menu-6-items - cello only: https://www.cellosaurus.org/
//-1/1 row of width 2rem with cello logo, menu and expasy logo
// menu-6-items - not cello e.g. https://enzyme.expasy.org/
// -menu row has its width changed from "auto" to "3rem"
// -sub-menus shown
//menu-7-items e.g. https://world-2dpage.expasy.org/
//-logo becomes spread on both rows (some bit on the same row as title and some bit on the same row as menu)
//menu-8-items e.g. https://prosite.expasy.org/
//-menu row has its width changed from "auto" to "3rem"
//-sub-menus shown
//menu-9-items e.g. https://hamap.expasy.org/
//-menu row has its width changed from "auto" to "3rem"
//-sub-menus shown

//window width >= 1500px
//menu-8-items e.g. https://prosite.expasy.org/
//-1/1 row of width 7rem with logo and menu
//menu-9-items e.g. https://hamap.expasy.org/
//-1/1 row of width 7rem with logo and menu

$(document).ready(function() {
    $("nav.header-elmt > ul > li").children("ul").hide();
    $(".help").hide();

    $("ul.menu-2-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto 3rem");
    $("nav.header-elmt > ul.menu-2-items > li:has(ul)").mouseover(function() {
        $(this).children("ul").show();
    });
    $("nav.header-elmt > ul.menu-2-items > li:has(ul)").mouseleave(function() {
        $(this).children("ul").hide();
    });
    $("nav.header-elmt > ul.menu-2-items > li:has(ul) > a").each(function() {
        $(this).removeAttr("href");
    });

    $(".button_help").click(function() {
        if ($(this).nextAll('.help:first').attr('class') == "help") {
            // $('.help').not($(this).nextAll(".help:first")).slideUp("slow");
            $(this).nextAll(".help:first").slideToggle("slow");
        } else {
            // $('.help').not($(this).parent().nextAll('.help:first')).slideUp('slow');
            // $(this).parent().nextAll('.help:first').slideToggle('slow');
        }
    });

    // for instance if user enters ' B1LI10 ' in a textarea
    // trims to 'B1LI10' and replaces in the textarea in question
    // textarea
    $("textarea").change(function(event) {
        $(this).val($.trim($(this).val()));
    });
});

$(window).on("load resize", function() {
    /* necessary to set height inbetween ~725 px and 900 px so that main does not overflow footer?! */
    if (window.matchMedia("(min-width: 900px)").matches) {
        $("body.cello > .footer-grid").css("height", "auto");
    }
    else if (window.matchMedia("(min-width: 600px)").matches) {
        $("body.cello > .footer-grid").css("height", "8rem");
    }
    else {
        $("body.cello > .footer-grid").css("height", "auto");
    }


    if (window.matchMedia("(min-width: 1200px)").matches) {
        $("body.cello > .footer-grid .footer-elmt:nth-child(2)").css("grid-template-columns", "1fr 1fr 1fr 1fr");
    }
    else if (window.matchMedia("(min-width: 600px)").matches) {
        $("body.cello > .footer-grid .footer-elmt:nth-child(2)").css("grid-template-columns", "1fr 1fr");
    }
    else {
        $("body.cello > .footer-grid .footer-elmt:nth-child(2)").css("grid-template-columns", "1fr");
    }


    if (window.matchMedia("(min-width: 600px)").matches) {
        $("body.cello > header.header-grid").css("grid-template-rows", "auto 2rem");
    }
    else {
        $("body.cello > header.header-grid").css("grid-template-rows", "auto auto");
    }

    if (window.matchMedia("(min-width: 900px)").matches) {
        $("ul.menu-3-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto 3rem");
        $("ul.menu-4-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto 3rem");

        // "Browse" and "Tools" are hidden on smaller screens		
        $("body.cello nav.header-elmt > ul.menu-6-items > li").show();

        $("nav.header-elmt > ul.menu-3-items > li:has(ul)").mouseover(function() {
            $(this).children("ul").show();
        });
        $("nav.header-elmt > ul.menu-3-items > li:has(ul)").mouseleave(function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-4-items > li:has(ul)").mouseover(function() {
            $(this).children("ul").show();
        });
        $("nav.header-elmt > ul.menu-4-items > li:has(ul)").mouseleave(function() {
            $(this).children("ul").hide();
        });
        $("body.cello nav.header-elmt > ul.menu-6-items > li:has(ul)").mouseover(function() {
            $(this).children("ul").show();
        });
        $("body.cello nav.header-elmt > ul.menu-6-items > li:has(ul)").mouseleave(function() {
            $(this).children("ul").hide();
        });

        $("nav.header-elmt > ul.menu-3-items > li:has(ul) > a").attr("disabled", "disabled").on("click", function() {
            return false;
        });
        $("nav.header-elmt > ul.menu-4-items > li:has(ul) > a").attr("disabled", "disabled").on("click", function() {
            return false;
        });
        $("body.cello nav.header-elmt > ul.menu-6-items > li:has(ul) > a").attr("disabled", "disabled").on("click", function() {
            return false;
        });
    }
    else {
        $("ul.menu-3-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
        $("ul.menu-4-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");

        $("nav.header-elmt > ul.menu-3-items > li:has(ul)").on("mouseover mouseleave", function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-4-items > li:has(ul)").on("mouseover mouseleave", function() {
            $(this).children("ul").hide();
        });

        // necessary for "Help" which is shown on small screens        
        $("body.cello nav.header-elmt > ul.menu-6-items > li:has(ul)").on("mouseover mouseleave", function() {
            $(this).children("ul").hide();
        });

        // Hide menu items with sub-menus except for "Help" (Hide "Browse" and "Tools")        
        $("body.cello nav.header-elmt > ul.menu-6-items > li:nth-child(2)").hide();
        $("body.cello nav.header-elmt > ul.menu-6-items > li:nth-child(3)").hide();

        $("nav.header-elmt > ul.menu-3-items > li:has(ul) > a").removeAttr("disabled").off("click");
        $("nav.header-elmt > ul.menu-4-items > li:has(ul) > a").removeAttr("disabled").off("click");
        $("body.cello nav.header-elmt > ul.menu-6-items > li:has(ul) > a").removeAttr("disabled").off("click");
    }

    if (window.matchMedia("(min-width: 1200px)").matches) {
        $("body.cello > header.header-grid").css("grid-template-rows", "2rem");
        $("body:not('.cello') ul.menu-6-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto 3rem");
        $("ul.menu-7-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto 3rem");
        $("body:not('.cello') nav.header-elmt > ul.menu-6-items > li:has(ul)").mouseover(function() {
            $(this).children("ul").show();
        });
        $("body:not('.cello') nav.header-elmt > ul.menu-6-items > li:has(ul)").mouseleave(function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-7-items > li:has(ul)").mouseover(function() {
            $(this).children("ul").show();
        });
        $("nav.header-elmt > ul.menu-7-items > li:has(ul)").mouseleave(function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-8-items > li:has(ul)").mouseover(function() {
            $(this).children("ul").show();
        });
        $("nav.header-elmt > ul.menu-8-items > li:has(ul)").mouseleave(function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-9-items > li:has(ul)").mouseover(function() {
            $(this).children("ul").show();
        });
        $("nav.header-elmt > ul.menu-9-items > li:has(ul)").mouseleave(function() {
            $(this).children("ul").hide();
        });
        $("body:not('.cello') nav.header-elmt > ul.menu-6-items > li:has(ul) > a").attr("disabled", "disabled").on("click", function() {
            return false;
        });
        $("nav.header-elmt > ul.menu-7-items > li:has(ul) > a").attr("disabled", "disabled").on("click", function() {
            return false;
        });
        $("nav.header-elmt > ul.menu-8-items > li:has(ul) > a").attr("disabled", "disabled").on("click", function() {
            return false;
        });
        $("nav.header-elmt > ul.menu-9-items > li:has(ul) > a").attr("disabled", "disabled").on("click", function() {
            return false;
        });
    }
    else {
        $("body:not('.cello') ul.menu-6-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
        $("ul.menu-7-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
        $("body:not('.cello') nav.header-elmt > ul.menu-6-items > li:has(ul)").on("mouseover mouseleave", function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-7-items > li:has(ul)").on("mouseover mouseleave", function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-8-items > li:has(ul)").on("mouseover mouseleave", function() {
            $(this).children("ul").hide();
        });
        $("nav.header-elmt > ul.menu-9-items > li:has(ul)").on("mouseover mouseleave", function() {
            $(this).children("ul").hide();
        });
        $("body:not('.cello') nav.header-elmt > ul.menu-6-items > li:has(ul) > a").removeAttr("disabled").off("click");
        $("nav.header-elmt > ul.menu-7-items > li:has(ul) > a").removeAttr("disabled").off("click");
        $("nav.header-elmt > ul.menu-8-items > li:has(ul) > a").removeAttr("disabled").off("click");
        $("nav.header-elmt > ul.menu-9-items > li:has(ul) > a").removeAttr("disabled").off("click");
    }

    // ul.menu-8-items => prosite (no title) and ul.menu-9-items => hamap (no title)
    // sub-menus are shown starting at width 1200px
    // ul.menu-8-items logo is on first row and menu is on the second row
    // starting at width 1500px: both logo and menu are on the same row
    if (window.matchMedia("(min-width: 1500px)").matches) {
        $("ul.menu-8-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "7rem");
        $("ul.menu-9-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "7rem");
    }
    else if (window.matchMedia("(min-width: 1200px)").matches) {
        $("ul.menu-8-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto 3rem");
        $("ul.menu-9-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto 3rem");
    }
    else {
        $("ul.menu-8-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
        $("ul.menu-9-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
    }

});

$(window).bind("beforeprint", function() {
    $("ul.menu-2-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
    $("ul.menu-3-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
    $("ul.menu-4-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
    $("body:not('.cello') ul.menu-6-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
    $("body.cello > header.header-grid").css("grid-template-rows", "auto auto");
    $("ul.menu-7-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
    $("ul.menu-8-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
    $("ul.menu-9-items").parent("nav.header-elmt").parent("header.header-grid").css("grid-template-rows", "auto auto");
});
