import os
# from attractsdk import Node
from attractsdk import File
# from attractsdk import NodeType

from flask import jsonify
from flask import Blueprint
from flask import request

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


@files.route("/", methods=['GET', 'POST'])
@login_required
def index():
    """Custom files entry point
    """
    rfiles = []
    backend = app.config['FILE_STORAGE_BACKEND']
    api = SystemUtility.attract_api()
    user = current_user.objectid
    node_picture = File()

    for file_ in request.files:
        filestorage = request.files[file_]

        # Save file on AttractiWeb Storage
        picture_path = os.path.join(
            app.config['FILE_STORAGE'], filestorage.filename)
        filestorage.save(picture_path)

        picture_file_file = open(picture_path, 'rb')
        if backend == 'attract':
            hash_ = hashfile(picture_file_file, hashlib.md5())
            name = "{0}{1}".format(hash_,
                                   os.path.splitext(picture_path)[1])
        picture_file_file.close()
        prop = {}
        prop['name'] = filestorage.filename
        prop['description'] = "File {0}".format(filestorage.filename)
        prop['user'] = user
        prop['contentType'] = filestorage.content_type
        prop['length'] = filestorage.content_length
        prop['uploadDate'] = datetime.strftime(
            datetime.now(), RFC1123_DATE_FORMAT)
        prop['md5'] = hash_
        prop['filename'] = filestorage.filename
        prop['backend'] = backend
        if backend in ["attract"]:
            prop['path'] = name
        node_picture.post(prop, api=api)
        prop['_id'] = node_picture['_id']
        if backend == 'attract':
            node_picture.post_file(picture_path, name, api=api)

        url = "{0}/file_server/file/{1}".format(app.config['ATTRACT_SERVER_ENDPOINT'], prop['path'])
        rfiles.append( {
            "id": prop['_id'],
            "name": prop['filename'],
            "size": prop['length'],
            "url": url,
            "thumbnailUrl": url,
            "deleteUrl": url,
            "deleteType": "DELETE"
        })

    # GET
    if False:
        pictures = node_picture.all({'max_results': 200, 'sort': '-uploadDate'}, api=api)
        for file_ in pictures['_items']:
            url = "{0}/file_server/file/{1}".format(app.config['ATTRACT_SERVER_ENDPOINT'], file_['path'])
            rfiles.append( {
                "id": file_['_id'],
                "name": file_['filename'],
                "size": file_['length'],
                "url": url,
                "thumbnailUrl": url,
                "deleteUrl": url,
                "deleteType": "DELETE"
            })

    return jsonify(dict(files=rfiles))
