(function($, window, wb){
'use strict';

var $parameter1 = $('#y1-type');
function disableY1Checkboxes() {
        $('#max1').prop('disabled', ($parameter1.val()!=46 && $parameter1.val()!=47));
        $('#min1').prop('disabled', ($parameter1.val()!=46 && $parameter1.val()!=47));
        $('#mean1').prop('disabled', ($parameter1.val()!=46 && $parameter1.val()!=47));
        $('#median1').prop('disabled', ($parameter1.val()!=46 && $parameter1.val()!=47));
        $('#upper1').prop('disabled', ($parameter1.val()!=46 && $parameter1.val()!=47));
        $('#lower1').prop('disabled', ($parameter1.val()!=46 && $parameter1.val()!=47));
}
$parameter1.on('change', disableY1Checkboxes);
disableY1Checkboxes();

var $parameter2 = $('#y2-type');
function disableY2Checkboxes() {
        $('#max2').prop('disabled', ($parameter2.val()!=46 && $parameter2.val()!=47));
        $('#min2').prop('disabled', ($parameter2.val()!=46 && $parameter2.val()!=47));
        $('#mean2').prop('disabled', ($parameter2.val()!=46 && $parameter2.val()!=47));
        $('#median2').prop('disabled', ($parameter2.val()!=46 && $parameter2.val()!=47));
        $('#upper2').prop('disabled', ($parameter2.val()!=46 && $parameter2.val()!=47));
        $('#lower2').prop('disabled', ($parameter2.val()!=46 && $parameter2.val()!=47));
}
$parameter2.on('change', disableY2Checkboxes);
disableY2Checkboxes();

})(jQuery, window, wb);
