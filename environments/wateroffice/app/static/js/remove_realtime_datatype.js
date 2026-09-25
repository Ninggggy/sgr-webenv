(function($, window, wb){
'use strict';

var
$dataType = $('#data-type'),
$station = $('#station'),
realTime = $.parseJSON($dataType.attr('data-attribute'));

if(realTime[$station.val()] === 'N'){
  $dataType.children('[value="Real-Time"]').remove();
}

$station.on('change', function(){
  var
  currentStation = this.value,
  $realTime = $dataType.children('[value="Real-Time"]');

  if(realTime[currentStation] === 'N' && $realTime.length !== 0){
    $realTime.remove();
  }else if(realTime[currentStation] === 'Y' && $realTime.length == 0) {
    $dataType.append('<option value="Real-Time">Real-Time</option>');
  }
});

})(jQuery, window, wb);
