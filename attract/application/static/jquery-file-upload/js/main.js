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

$(function () {
    'use strict';

    var formName = '';

    console.log("Initializing");
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
            $('#picture').append(new Option(file.name, file.id, true, true));
            $('#attachments').append(new Option(file.name, file.id, true, true));
        }
    }
    $('#fileupload').bind('fileuploaddone', sendToForm);

    var checkFiles = function (e, data) {
        if (data.files.length > 1) {
            return false;
        }
    }
    $('#fileupload').bind('fileuploadsend', checkFiles);

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
