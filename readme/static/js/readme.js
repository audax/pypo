$(document).ready(function() {
    "use strict";

    if (window.PYPO === undefined) {
        window.PYPO = {};
    }

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
        disabled: true,
        placement: 'auto',
        container: 'body',
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
        container: 'body',
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
            width: '256px',
            openOnEnter: false
        }
    });
    $('#id_enable_editable').click(function(e) {
        e.preventDefault();
        $(this).parent().toggleClass('active');
        $('.editable').editable('toggleDisabled');
    });
    $('.link_toolbox').click(function (e) {
        e.preventDefault();
        var $this = $(this);
        $this.closest('.item').toggleClass('active_item');
        $this.toggleClass('active');
    })

    var protocol_regexp = new RegExp("^https?://");

    var setup_item_form = function (url_field, tags_field) {
        tags_field.select2({
            tags: window.PYPO.tags,
            width: '100%',
            tokenSeparators: [","],
            openOnEnter: false,
            selectOnBlur: true
        });

        url_field.blur(function() {
            var $this = $(this);
            var value = $this.val();
            if (!protocol_regexp.test(value)) {
                $this.val('http://'+value);
            }
        })
    }

    if ($('#id_url').length === 1) {
        setup_item_form($('#id_url'), $('#id_tags'));
    }

    $('#id_add_form').popover({
        html : true,
        placement: 'bottom',
        container: '#add_item_popover',
        title: 'Add a new link',
        content: function() {
            return $("#add_item_popover_content").html();
        }
    }).on('shown.bs.popover', function () {
        setup_item_form($('.popover-content input[name="url"]'), $('.popover-content input[name="tags"]'));
        $('#id_add_form').parent().addClass('active');
    }).on('hidden.bs.popover', function() {
        $('#id_add_form').parent().removeClass('active');
    });
});

