(function($, window, wb){
'use strict';

var
// The list of radio buttons that are associated with the textboxes/dropdowns
association = {
  '#station-name' : '#station-name-search',
  '#station-number' : '#station-number-search',
  '#province' : '#province-search',
  '#basin' : '#basin-search',
  '#north-degrees' : '#coordinate-search',
  '#north-minutes' : '#coordinate-search',
  '#north-seconds' : '#coordinate-search',
  '#south-degrees' : '#coordinate-search',
  '#south-minutes' : '#coordinate-search',
  '#south-seconds' : '#coordinate-search',
  '#east-degrees' : '#coordinate-search',
  '#east-minutes' : '#coordinate-search',
  '#east-seconds' : '#coordinate-search',
  '#west-degrees' : '#coordinate-search',
  '#west-minutes' : '#coordinate-search',
  '#west-seconds' : '#coordinate-search',
},
// Create the element event string based on the ids in the association object
eventElements = function(){
  var
  elements = [],
  elementString;

  $.each(association, function(k, v){
    elements.push(k);
  });

  elementString = elements.join(', ');

  return elementString;
},
// May contain the radio button id if the user clicks a radio button before WET is done loading
radio = '',
// Check the associated radio button, or the radio button itself
// This is for if the user focuses an element before WET is done loading
checkRadioButton = function(){
  var
  $focused = $(':focus');

  if(typeof $focused.attr('id') !== 'undefined'){
    $(association['#' + $focused.attr('id')]).prop('checked', true);
  }else if(radio !== ''){
    $(radio).prop('checked', true);
  }
};

// Check the associated radio button when the element is focused
$(document).on('focus', eventElements(), function(e){
  $(association['#' + $(this).attr('id')]).prop('checked', true);
});

// When WET components are done loading
$(document).on('wb-ready.wb', function(e){
  checkRadioButton();
});

// This occurs after the HTML is done loading (onload) but before wb-ready.wb
// Get the id of the radio button that was selected
$(document).on('change', '[name="search_type"]', function(e){
  radio = '#' + $('[name="search_type"]:checked').attr('id');
});

})(jQuery, window, wb);
