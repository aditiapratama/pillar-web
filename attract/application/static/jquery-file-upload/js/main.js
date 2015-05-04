/*
 * jQuery File Upload Plugin JS Example 8.9.1
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/MIT
 */

/* global $, window */

var upload_file_to = '';
var upload_multiple_files = false;

function set_upload_parameters(upload_to, multiple) {
    upload_file_to = upload_to;
    upload_multiple_files = multiple;
    clear_upload_files();
    if (multiple) {
        $("#file_upload_input").attr("multiple", "");
    } else {
        $("#file_upload_input").removeAttr("multiple");
    }
}

function clear_upload_files() {
    var table = $("#file_uploader_table")[0];
    while (table.firstChild) {
        table.removeChild(table.firstChild);
    }
}

$(function () {
    'use strict';

    var formName = '';

    // Initialize the jQuery File Upload widget:
    $('#fileupload').fileupload({
        // Uncomment the following to send cross-domain cookies:
        //xhrFields: {withCredentials: true},
        //disableImageResize: false,
        //imageMaxWidth: 80,
        url: '/files/'
    });

    // Enable iframe cross-domain access via redirect option:
    $('#fileupload').fileupload(
        'option',
        'redirect',
        window.location.href.replace(
            /\/[^\/]*$/,
            '/cors/result.html?%s'
        )
    );

    var sendToForm = function(e, data) {
        for (var file_id in data.result.files) {
            var file = data.result.files[file_id];

            $('#'+upload_file_to).append(new Option(file.name, file.id, true, true));
        }
    }
    $('#fileupload').bind('fileuploaddone', sendToForm);


    var addToForm = function(e, data) {
        if (upload_multiple_files) {
            return;
        }
        var table = $("#file_uploader_table")[0];
        while (table.firstChild) {
            table.removeChild(table.firstChild);
        }
    }
    $('#fileupload').bind('fileuploadadd', addToForm);


    // Load existing files:
    $('#fileupload').addClass('fileupload-processing');
    $.ajax({
        // Uncomment the following to send cross-domain cookies:
        //xhrFields: {withCredentials: true},
        url: $('#fileupload').fileupload('option', 'url'),
        dataType: 'json',
        context: $('#fileupload')[0]
    }).always(function () {
        $(this).removeClass('fileupload-processing');
    }).done(function (result) {
        $(this).fileupload('option', 'done')
            .call(this, $.Event('done'), {result: result});
    });

});
