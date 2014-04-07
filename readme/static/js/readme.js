$(document).ready(function() {
    "use strict";
    var protocol_regexp = new RegExp("^https?://");

    $('[data-toggle=offcanvas]').click(function() {
        $('.row-offcanvas').toggleClass('active');
    });
    $('#id_url').blur(function() {
        var $this = $(this);
        var value = $this.val();
        if (!protocol_regexp.test(value)) {
            $this.val('http://'+value);
        }
    })
});

