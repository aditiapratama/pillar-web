function deleteFile(fileField, newFileId) {
    if (newFileId) {
        fileField.val(newFileId);
    } else {
        fileField.val('');
    }
}


$(function () {
    // $('.file_delete').click(function(e){
    $('body').unbind('click');
    $('body').on('click', '.file_delete', function(e) {
        e.preventDefault();
        var field_name = '#' + $(this).data('field-name');
        var file_field = $(field_name);
        deleteFile(file_field);
        $(this).parent().parent().hide();
        $(this).parent().parent().prev().hide();
    });

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
                statusBarSet('info', 'Uploading File...', 'pi-upload-cloud');
                $('.button-save').addClass('disabled');
                $('li.button-save a#item_save').html('<i class="pi-spin spin"></i> Uploading...');
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
                $('body input.fileupload, #files-action-add').addClass('notallowed');
            },
            done: function (e, data) {
                $('body input.fileupload, #files-action-add').removeClass('notallowed');

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

                // Ugly workaround: If the asset has the default name, name it as the file
                if ($('.form-group.name .form-control').val() == 'New asset') {
                    var filename = data.files[0].name;
                    $('.form-group.name .form-control').val(filename);
                    $('.node-edit-title').html(filename);
                }

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
