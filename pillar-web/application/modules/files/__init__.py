import PIL
from PIL import Image
import simplejson
import traceback

from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import abort
from flask import send_from_directory
from werkzeug import secure_filename

#from application.controllers.admin import *

import os
# from pillarsdk import Node
from pillarsdk import File
# from pillarsdk import NodeType

from flask import jsonify
from flask import Blueprint
from flask import request
from flask import render_template

# from flask import render_template

from application import app
from application import SystemUtility
# from application.helpers import percentage

from flask.ext.login import current_user
from flask.ext.login import login_required

from datetime import datetime

# Name of the Blueprint
files = Blueprint('files', __name__)

RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

import hashlib


def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()


@files.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Custom files entry point
    """
    rfiles = []
    backend = app.config['STORAGE_BACKEND']
    api = SystemUtility.attract_api()
    user = current_user.objectid
    node_picture = File()

    for file_ in request.files:
        filestorage = request.files[file_]

        # Save file on AttractWeb Storage
        picture_path = os.path.join(
            app.config['UPLOAD_DIR'], filestorage.filename)
        filestorage.save(picture_path)

        picture_file_file = open(picture_path, 'rb')
        if backend == 'pillar':
            hash_ = hashfile(picture_file_file, hashlib.md5())
            name = "{0}{1}".format(hash_,
                                   os.path.splitext(picture_path)[1])
        picture_file_file.close()

        file_check = node_picture.all(
            {"where": "path=='{0}'".format(name)}, api=api)
        file_check = file_check['_items']

        if len(file_check) == 0:
            prop = {}
            prop['name'] = filestorage.filename
            prop['description'] = "File {0}".format(filestorage.filename)
            prop['user'] = user
            prop['content_type'] = filestorage.content_type
            # TODO Fix length value
            prop['length'] = filestorage.content_length
            prop['md5'] = hash_
            prop['filename'] = filestorage.filename
            prop['backend'] = backend
            if backend in ["pillar"]:
                prop['path'] = name
            node_picture.post(prop, api=api)
            prop['_id'] = node_picture['_id']
            if backend == 'pillar':
                node_picture.post_file(picture_path, name, api=api)
                node_picture.build_previews(name, api=api)

            url = "{0}/file_storage/file/{1}".format(
                app.config['ATTRACT_SERVER_ENDPOINT'], prop['path'])
            rfiles.append( {
                "id": prop['_id'],
                "name": prop['filename'],
                "size": prop['length'],
                "url": url,
                "thumbnailUrl": url,
                "deleteUrl": url,
                "deleteType": "DELETE"
            })
        else:
            url = "{0}/file_storage/file/{1}".format(
                app.config['ATTRACT_SERVER_ENDPOINT'], file_check[0]['path'])
            rfiles.append( {
                "id": file_check[0]['_id'],
                "name": file_check[0]['filename'],
                "size": file_check[0]['length'],
                "url": url,
                "thumbnailUrl": url,
                "deleteUrl": url,
                "deleteType": "DELETE"
            })

    return jsonify(dict(files=rfiles))


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
        if self.type != None:
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
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


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
        print request.files
        file = request.files['file']
        #pprint (vars(objectvalue))

        if file:
            filename = secure_filename(file.filename)
            filename = gen_file_name(filename)
            mimetype = file.content_type
            if not allowed_file(file.filename):
                result = uploadfile(name=filename, type=mimetype, size=0,
                                    not_allowed_msg="Filetype not allowed")
            else:
                # save file to disk
                uploaded_file_path = os.path.join(get_dir('uploads'), filename)
                file.save(uploaded_file_path)

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


