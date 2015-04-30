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

    print (request.files)

    for file_ in request.files:
        filestorage = request.files[file_]

        # Save file on AttractiWeb Storage
        picture_path = os.path.join(
            app.config['FILE_STORAGE'], filestorage.filename)
        filestorage.save(picture_path)

        node_picture = File()

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
        prop['md5'] = ""
        prop['filename'] = filestorage.filename
        prop['backend'] = backend
        if backend in ["attract"]:
            prop['path'] = name
        # elif backend == "fs.files":
        #     prop['path'] = str(node_bfile['_id'])
        node_picture.post(prop, api=api)
        # node['picture'] = node_picture['_id']
        # Send file to Attract Server
        # if backend == "fs.files":
        #     node_bfile = attractsdk.binaryFile()
        #     node_bfile.post_file(picture_path, api=api)
        # elif backend == 'attract':
        if backend == 'attract':
            node_picture.post_file(picture_path, name, api=api)
        # return node

        url = "{0}/file_server/file/{1}".format(app.config['ATTRACT_SERVER_ENDPOINT'], name)

        rfiles.append( {
            "id": node_picture['_id'],
            "name": filestorage.filename,
            "size": filestorage.content_length,
            "url": url,
            "thumbnailUrl": url,
            "deleteUrl": url,
            "deleteType": "DELETE"
        })

    return jsonify(dict(files=rfiles))
