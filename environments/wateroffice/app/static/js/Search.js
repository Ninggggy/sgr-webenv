(function($, window, wb){
'use strict';

/**
 * Validation for result form submission.
 */
$('input[name="view_report"], input[name="download"], input[name="save_list"], input[name="map_location"]').on('click', function(e){
  var $this = $(this);

  error.clear();
  validate.checkbox();
  validate.resultsType();
  validate.stationCount($this.attr('name'));

  if(Object.size(error.messages) > 0){
    error.create();

    $.each(error.messages, function(key, value){
      error.add(key, value);
    });

    e.preventDefault();
    e.stopPropagation();
  }
});

var
$check = $('input[type="checkbox"][name="check[]"]'),
$hiddenCheck = $('input[type="hidden"][name="check[]"]'),
validate = {
  checkbox : function(){
    var checkRegex = /^(\d{2}([A-Z]{2}\d{3}|[A-Z]{3}\d{2}),\d+(,(\d{4})?){2},(Flow|Level|Flow and Level|Concentration|Concentration,Instantaneous|Concentration,Instantaneous,Instantaneous|Instantaneous,Instantaneous|Instantaneous,Instantaneous,Instantaneous|Loads,Concentration,Instantaneous,Instantaneous,Instantaneous,Instantaneous|Loads,Concentration,Instantaneous,Instantaneous|Loads,Concentration,Instantaneous,Instantaneous,Instantaneous|Instantaneous|Loads,Concentration|Concentration,Instantaneous|Loads,Concentration,Instantaneous)?)$/;

    $check.each(function(){
      var $this = $(this);

      if($(this).is(':checked') && $this.attr('value').match(checkRegex) === null){
        error.messages.check = t('Error! Unexpected and/or incorrect data has been entered.');
        return false;
      }
    });
  },
  resultsType : function(){
    var resultsTypeRegex = /^(real_time|historical|statistics|sediment)$/;

    if($('input[type="hidden"][name="results_type"]').attr('value').match(resultsTypeRegex) === null){
      error.messages.results_type = t('Error! Unexpected and/or incorrect data has been entered.');
    }
  },
  stationCount : function(button){
    var checked = 0;

    $check.each(function(){
      if($(this).is(':checked')){
        checked++;
      }
    });

    $hiddenCheck.each(function(){
      checked++;
    });

    if(checked === 0){
      if(button === 'save_list'){
        error.messages.check = t('Please select at least one station before you click Save List.');
      }else{
        error.messages.check = t('Please select at least one station.');
      }
    }else if(checked > 50){
      error.messages.check = t('You\'ve selected more than 50 stations. Please deselect some of them.');
    }
  }
},
error = {
  messages : {},
  create : function(){
    $('h1#wb-cont').after('<div class="alert alert-warning"><div><ul class="errors"></ul></div></div>');
  },
  add : function(name, message){
    $('h1#wb-cont + div.alert div ul.errors').append('<li data-name="' + name + '">' + message + '</li>');
  },
  clear : function(){
    $('h1#wb-cont + div.alert').remove();
    error.messages = {};
  }
};

Object.size = function(obj){
  var size = 0,
    key;

  for(key in obj){
    if(obj.hasOwnProperty(key)) size++;
  }

  return size;
};

/**
 * set details elements to closed for xs screens
 */
var changeDetailsState = function(){
  var $html = $('html');

  if($html.hasClass('xsmallview') === true || $html.hasClass('xxsmallview') === true){
    $('.xsmallview main details, .xxsmallview main details').each(function(i){
      var $this = $(this);

      if($this.parent().hasClass('tabpanels') === false){
        $this.removeAttr('open');
      }
    });
  }else{
    $('.smallview main details, .mediumview main details, .largeview main details').each(function(i){
      var $this = $(this);

      if($this.parent().hasClass('tabpanels') === false){
        $this.attr('open', 'open');
      }
    });
  }
};

$(document).on('wb-ready.wb win-rsz-width.wb', function(e){
  changeDetailsState();
});

changeDetailsState();

})(jQuery, window, wb);
