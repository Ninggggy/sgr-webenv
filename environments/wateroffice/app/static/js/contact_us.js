(function($, window, wb){
'use strict';

const LINK = {
  en: 'https://weather.gc.ca/mainmenu/water_contact_us_e.html',
  fr: 'https://meteo.gc.ca/mainmenu/water_contact_us_f.html'
};

$('a[href*="water_contact_us"]').on('click', function(e){
  e.stopPropagation();
  e.preventDefault();

  const href = $(this).attr('href');
  const searchParams = new URLSearchParams(href.split('?')[1]);
  let tab = searchParams.get('tab');
  tab = (tab !== null && tab.match(/^[1-9]$/) !== null) ? `?tab=${tab}` : '';

  let $form = $(`<form action="${LINK[$('html').attr('lang')]}${tab}" method="POST" style="display: none;">
    <input type="hidden" name="hiddenreferer" value="${window.location.href}">
    <input type="hidden" name="SubmitWater" value="water">
  </form>`);
  $form.attr('target', '_blank');

  $('html').append($form);
  $form.submit();
  $form.remove();
});

})(jQuery, window, wb);
