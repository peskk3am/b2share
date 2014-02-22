$(function() {
    $('select').change( function() {
        var value = $(this).val();
        if (value == 'other') {
           $(this.name+"_input").show();
        }
    });
});

