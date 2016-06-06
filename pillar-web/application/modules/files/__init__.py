import os
import hashlib
import time
import shutil
import PIL
from PIL import Image
import simplejson
import traceback
from datetime import datetime
from werkzeug import secure_filename
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import abort
from flask import send_from_directory
from flask import jsonify
from flask import Blueprint
from flask import request
from flask import render_template
from flask.ext.login import current_user
from flask.ext.login import login_required
from pillarsdk import File
from pillarsdk.exceptions import ResourceNotFound
from application import app
from application import system_util

# Name of the Blueprint
files = Blueprint('files', __name__)


@files.route('/upload')
@login_required
def index_upload():
    if 'embed' in request.args:
        return render_template('upload_embed.html')
    else:
        return render_template('upload.html')


class uploadfile():
    def __init__(self, name, type=None, size=None, not_allowed_msg=''):
        self.name = name
        self.type = type
        self.size = size
        self.not_allowed_msg = not_allowed_msg
        self.url = "/files/upload/data/%s" % name
        self.thumbnail_url = "/files/upload/thumbnail/%s" % name
        self.delete_url = "/files/upload/delete/%s" % name
        self.delete_type = "DELETE"
        self.create_url = "/files/upload/create/%s" % name

    def is_image(self):
        fileName, fileExtension = os.path.splitext(self.name.lower())

        if fileExtension in ['.jpg', '.png', '.jpeg', '.bmp']:
            return True

        return False


    def get_file(self):
        if self.type is not None:
            # POST an image
            if self.type.startswith('image'):
                return {"name": self.name,
                        "type": self.type,
                        "size": self.size,
                        "url": self.url,
                        "thumbnailUrl": self.thumbnail_url,
                        "deleteUrl": self.delete_url,
                        "deleteType": self.delete_type,
                        "createUrl": self.create_url}

            # POST an normal file
            elif self.not_allowed_msg == '':
                return {"name": self.name,
                        "type": self.type,
                        "size": self.size,
                        "url": self.url,
                        "deleteUrl": self.delete_url,
                        "deleteType": self.delete_type,
                        "createUrl": self.create_url}

            # File type is not allowed
            else:
                return {"error": self.not_allowed_msg,
                        "name": self.name,
                        "type": self.type,
                        "size": self.size,}

        # GET image from disk
        elif self.is_image():
            return {"name": self.name,
                    "size": self.size,
                    "url": self.url,
                    "thumbnailUrl": self.thumbnail_url,
                    "deleteUrl": self.delete_url,
                    "deleteType": self.delete_type,
                    "createUrl": self.create_url}

        # GET normal file from disk
        else:
            return {"name": self.name,
                    "size": self.size,
                    "url": self.url,
                    "deleteUrl": self.delete_url,
                    "deleteType": self.delete_type,
                    "createUrl": self.create_url}


def allowed_file(filename):
    allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    if allowed_extensions:
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in allowed_extensions
    else:
        return True


def gen_file_name(filename):
    """If file was exist already, rename it and return a new name
    """
    i = 1
    while os.path.exists(os.path.join(app.config['UPLOAD_DIR'], filename)):
        name, extension = os.path.splitext(filename)
        filename = '%s_%s%s' % (name, str(i), extension)
        i = i + 1

    return filename


def get_dir(directory_name): # user uploads, thumbnails
    user_uploads = os.path.join(app.config['UPLOAD_DIR'], str(current_user.objectid))
    if directory_name == 'uploads':
        if not os.path.isdir(user_uploads):
            os.makedirs(user_uploads)
        return user_uploads
    elif directory_name == 'thumbnails':
        user_thumbnails = os.path.join(user_uploads, 'thumbnails')
        if not os.path.isdir(user_thumbnails):
            os.makedirs(user_thumbnails)
        return user_thumbnails
    else:
        return None


def create_thumbnail(image):
    try:
        basewidth = 80
        img = Image.open(os.path.join(get_dir('uploads'), image))
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
        img.save(os.path.join(get_dir('thumbnails'), image))
        return True
    except:
        print traceback.format_exc()
        return False


@files.route('/upload/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file_object = request.files['file']
        #pprint (vars(objectvalue))

        if file_object:
            filename = secure_filename(file_object.filename)
            filename = gen_file_name(filename)
            mimetype = file_object.content_type
            if not allowed_file(file_object.filename):
                result = uploadfile(name=filename, type=mimetype, size=0,
                                    not_allowed_msg="Filetype not allowed")
            else:
                # save file to disk
                uploaded_file_path = os.path.join(get_dir('uploads'), filename)
                file_object.save(uploaded_file_path)

                # create thumbnail after saving
                if mimetype.startswith('image'):
                    create_thumbnail(filename)

                # get file size after saving
                size = os.path.getsize(uploaded_file_path)

                # return json for js call back
                result = uploadfile(name=filename, type=mimetype, size=size)

            return simplejson.dumps({"files": [result.get_file()]})

    if request.method == 'GET':
        # get all file in ./data directory
        user_uploads = get_dir('uploads')
        files = [f for f in os.listdir(user_uploads) if os.path.isfile(
            os.path.join(user_uploads, f)) and f not in app.config['IGNORED_FILES']]

        file_display = []

        for f in files:
            size = os.path.getsize(os.path.join(user_uploads, f))
            file_saved = uploadfile(name=f, size=size)
            file_display.append(file_saved.get_file())

        return simplejson.dumps({"files": file_display})

    return redirect(url_for('index'))


# serve static files
@files.route('/upload/thumbnail/<string:filename>', methods=['GET'])
def get_thumbnail(filename):
    return send_from_directory(get_dir('thumbnails'), filename=filename)


@files.route('/upload/data/<string:filename>', methods=['GET'])
def get_file(filename):
    return send_from_directory(get_dir('uploads'), filename=filename)


@files.route('/upload/delete/<string:filename>', methods=['DELETE'])
def delete(filename):
    file_path = os.path.join(get_dir('uploads'), filename)
    file_thumb_path = os.path.join(get_dir('thumbnails'), filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)

            if os.path.exists(file_thumb_path):
                os.remove(file_thumb_path)

            return simplejson.dumps({filename: 'True'})
        except:
            return simplejson.dumps({filename: 'False'})
    else:
        return abort(404)


def process_and_create_file(project_id, name, length, mime_type):
    """Base function that handles the hashing of a file name and the creation of
    a record in the files collection. This function is use in the nodes module
    on assets_create.

    :type project_id: string
    :param bucket_name: The project id, uset to fetch the gcs bucket.

    :type name: string
    :param subdir: The the filename (currently used to build the path).

    :type length: int
    :param subdir: Filesize in bit (in case we start the upload from the js
        interface, we get the size for free, otherwise at the moment we
        hardcode it to 0)

    :type mime_type: string
    :param subdir: MIME type used do display/preview the file accordingly

    """

    root, ext = os.path.splitext(name)
     # Hash name based on file name, user id and current timestamp
    hash_name = name + str(current_user.objectid) + str(round(time.time()))
    link = hashlib.sha1(hash_name).hexdigest()
    link = os.path.join(link[:2], link + ext)

    src_dir_path = os.path.join(app.config['UPLOAD_DIR'], str(current_user.objectid))

    # Move the file in designated location
    destination_dir = os.path.join(app.config['SHARED_DIR'], link[:2])
    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    # (TODO) Check if filename already exsits
    src_file_path = os.path.join(src_dir_path, name)
    dst_file_path = os.path.join(destination_dir, link[3:])
    # (TODO) Thread this operation

    shutil.move(src_file_path, dst_file_path)

    api = system_util.pillar_api()
    file_item = File({
        'name': link[3:],
        'filename': name,
        'user': current_user.objectid,
        'backend': 'gcs',
        'md5': '',
        'content_type': mime_type,
        'length': length,
        'project': project_id
        })
    file_item.create(api=api)
    return file_item


@files.route('/create', methods=['POST'])
def create():
    """Endpoint hit by the automatic upload of a picture, currently used in the
    edit node form. Some sanity checks are already done in the fronted, but
    additional checks can be implemented here.
    """
    name = request.form['name']
    size = request.form['size']
    content_type = request.form['type']
    field_name = request.form['field_name']
    project_id = request.form['project_id']
    file_item = process_and_create_file(project_id, name, size, content_type)
    api = system_util.pillar_api()
    f = File.find(file_item['_id'], api=api)
    thumbnail_link = f.thumbnail('s', api=api)

    return jsonify(status='success', data=dict(id=file_item._id,
        link=thumbnail_link, field_name=field_name))


@files.route('/delete/<item_id>', methods=['POST'])
def item_delete(item_id):
    """We run this when updating a preview picture (after succesfully uploading
    a new one).
    """
    api = system_util.pillar_api()
    try:
        file_item = File.find(item_id, api=api)
        file_item.delete(api=api)
        message = 'File deleted'
    except ResourceNotFound:
        message = 'File not found'
    return jsonify(status='success', data=dict(message=message))
