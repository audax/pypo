window.PYPO = {};
$(document).ready(function() {
    "use strict";

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });


    var protocol_regexp = new RegExp("^https?://");

    $('#id_url').blur(function() {
        var $this = $(this);
        var value = $this.val();
        if (!protocol_regexp.test(value)) {
            $this.val('http://'+value);
        }
    })
    $('[data-toggle="confirmation"]').popConfirm({
            title: 'Do you want to delete this item?',
            content: '',
            placement: 'bottom',
            yesBtn: '<i class="fa fa-check">Yes</i>',
            noBtn: '<i class="fa fa-times">No</i>',
            yesCallBack: function (self) {
                $.ajax({
                        url: self.data('item-api-url'),
                        success: function () {
                            self.closest('div.item').fadeOut();
                        },
                        type: 'DELETE'
                })
            }
    });
    var paramFunction = function (params) {
        var data = {};
        data['id'] = params.pk;
        data[params.name] = params.value;
        // emulate patch request, see
        // https://github.com/ariya/phantomjs/issues/11384
        return JSON.stringify(data);
    }
    var paramFunctionForTags = function (params) {
        params['name'] = 'tags';
        return paramFunction(params);
    }

    $('.editable').editable({
        placement: 'bottom',
        disabled: true,
        ajaxOptions: {
            type: 'POST',
            headers: {'X-HTTP-Method-Override': 'PATCH'},
            dataType: 'JSON',
            contentType: 'application/json'
        },
        params: paramFunction
    });

    $('.editable-tags').editable({
        placement: 'bottom',
        disabled: true,
        type: 'select2',
        ajaxOptions: {
            type: 'POST',
            headers: {'X-HTTP-Method-Override': 'PATCH'},
            dataType: 'JSON',
            contentType: 'application/json'
        },
        params: paramFunctionForTags,
        select2: {
            tags: window.PYPO.tags,
            tokenSeparators: [","],
            width: '100%',
            openOnEnter: false
        }
    });
    $('#id_enable_editable').click(function(e) {
        e.preventDefault();
        $(this).parent().toggleClass('active');
        $('.editable').editable('toggleDisabled');
    });
});

