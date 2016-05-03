function deleteFile(fileField, newFileId) {
    newFileId = newFileId || null;
    var fileId = fileField.val();
    var url = '/files/delete/' + fileId;
    $.post(url, function(data){}).success(function(dataResponse){
        // Notify of successful request
        //- statusBarSet('success', 'Original File Removed Successfully');
        // If we provide the id of a previously uploaded file, add it here
        if (newFileId) {
            fileField.val(newFileId);
        } else {
            fileField.val('');
        }
    });
}

$('.file_delete').click(function(e){
    e.preventDefault();
    var field_name = '#' + $(this).data('field-name');
    var file_field = $(field_name);
    deleteFile(file_field);
    $('.node-preview-thumbnail').hide();
});



$(function () {
    function inject_project_id_into_url(index, element) {
        // console.log('Injecting ', ProjectUtils.projectId(), ' into ', element);
        var url = element.getAttribute('data-url');
        url = url.replace('{project_id}', ProjectUtils.projectId());
        element.setAttribute('data-url', url);
        // console.log('The new element is', element);
    }

    var fieldUpload = '';
    $('.fileupload')
        .each(inject_project_id_into_url)
        .on('click', function(e) {
        $('.fileupload').fileupload({
            dataType: 'json',
            replaceFileInput:false,
            dropZone: $(this),
            formData: {},
            beforeSend: function(xhr, data) {
                var token = this.fileInput.attr('data-token');
                xhr.setRequestHeader('Authorization', 'basic ' + btoa(token + ':'));
                statusBarSet('info', 'Uploading File', 'pi-upload-cloud');
                $('.button-save').addClass('disabled');
                $('li.button-save a#item_save').html('<i class="pi-spin spin"></i> Uploading');
            },
            add: function(e, data) {
                var uploadErrors = [];
                // Load regex if available (like /^image\/(gif|jpe?g|png)$/i;)
                var acceptFileTypes = new RegExp($(this).data('file-format'));
                if(data.originalFiles[0]['type'].length && !acceptFileTypes.test(data.originalFiles[0]['type'])) {
                    uploadErrors.push('Not an accepted file type');
                }
                // Limit upload size to 1GB
                if(data.originalFiles[0]['size'] && data.originalFiles[0]['size'] > 1262485504) {
                    uploadErrors.push('Filesize is too big');
                }
                if(uploadErrors.length > 0) {
                    $(this).parent().parent().addClass('error');
                    $(this).after(uploadErrors.join("\n"));
                } else {
                    $(this).parent().parent().removeClass('error');
                    data.submit();
                }
            },
            progressall: function (e, data) {
                // Update progressbar during upload
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $(this).next().find('.form-upload-progress-bar').css(
                    {'width': progress + '%', 'display': 'block'}
                    ).removeClass('progress-error').addClass('progress-active');
            },
            done: function (e, data) {

                if (data.result.status !== 'ok') {
                    if (console)
                        console.log('FIXME, do error handling for non-ok status', data.result);
                    return;
                }

                // Ensure the form refers to the correct Pillar file ID.
                var pillar_file_id = data.result.file_id;
                var field_name = '#' + $(this).attr('data-field-name');

                if ($(field_name).val()) {
                    $('.node-preview-thumbnail').hide();
                    deleteFile($(field_name), pillar_file_id);
                }
                $(field_name).val(pillar_file_id);

                // var previewThumbnail = fieldUpload.prev().prev();
                //
                // $(previewThumbnail).attr('src', data.data.link);
                // $('.node-preview-thumbnail').show();

                statusBarSet('success', 'File Uploaded Successfully', 'pi-check');

                $('.button-save').removeClass('disabled');
                $('li.button-save a#item_save').html('<i class="pi-check"></i> Save Changes');
                $('.progress-active').removeClass('progress-active progress-error');
                $('.fileupload').fileupload('destroy');
            },
            fail: function (e, data) {
                statusBarSet(data.textStatus, 'Upload error: ' + data.errorThrown, 'pi-attention', 8000);
                $('.progress-active').addClass('progress-error').removeClass('progress-active');
            }
        });
    });
});
