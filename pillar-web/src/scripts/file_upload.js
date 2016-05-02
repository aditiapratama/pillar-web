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
    var fieldUpload = '';
    $('.fileupload').on('click', function(e) {
        $('.fileupload').fileupload({
            dataType: 'json',
            acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
            replaceFileInput:false,
            dropZone: $(this),
            formData: {},
            progressall: function (e, data) {
                // Update progressbar during upload
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $(this).next().find('.form-upload-progress-bar').css(
                    {'width': progress + '%', 'display': 'block'}
                    ).removeClass('progress-error').addClass('progress-active');

                fieldUpload = $(this);
            },
            done: function (e, data) {
                // Get the first file upload result (we only need one)
                var fileData = data.result.files[0];
                // Create a file object on the server and retrieve its id
                statusBarSet('info', 'Uploading File', 'pi-upload-cloud');

                $('.button-save').addClass('disabled');
                $('li.button-save a#item_save').html('<i class="pi-spin spin"></i> Uploading Preview');
                var payload = {
                    name: fileData.name,
                    size: fileData.size,
                    type: fileData.type,
                    field_name: fieldUpload.attr('data-field-name'),
                    project_id: ProjectUtils.projectId()
                };
                $.post("/files/create", payload)
                .done(function(data) {
                    if (data.status === 'success') {
                        // If successful, add id to the picture hidden field
                        var field_name = '#' + data.data.field_name;
                        if ($(field_name).val()){
                            $('.node-preview-thumbnail').hide();
                            deleteFile($(field_name), data.data.id);
                        } else {
                            $(field_name).val(data.data.id);
                        }

                        var previewThumbnail = fieldUpload.prev().prev();

                        $(previewThumbnail).attr('src', data.data.link);
                        $('.node-preview-thumbnail').show();
                        statusBarSet('success', 'File Uploaded Successfully', 'pi-check');

                        $('.button-save').removeClass('disabled');
                        $('li.button-save a#item_save').html('<i class="pi-check"></i> Save Changes');
                        $('.progress-active').removeClass('progress-active progress-error');
                        $('.fileupload').fileupload('destroy');
                    }
                    }).fail(function(data) {
                        statusBarSet(data.textStatus, 'Upload error: ' + data.errorThrown, 'pi-attention', 8000);
                    });

            },
            fail: function (e, data) {
                statusBarSet(data.textStatus, 'Upload error: ' + data.errorThrown, 'pi-attention', 8000);
                $('.progress-active').addClass('progress-error').removeClass('progress-active');
            }
        });
    });
});
