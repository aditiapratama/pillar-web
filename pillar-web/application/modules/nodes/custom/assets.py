import os
import hashlib
import time
import shutil
from flask import request
from flask import jsonify
from flask.ext.login import login_required
from flask.ext.login import current_user
from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk import File
from application import app
from application.modules.nodes import nodes
from application import SystemUtility


@nodes.route('/assets/create', methods=['POST'])
@login_required
def assets_create():
    name = request.form['name']
    parent_id = request.form.get('parent_id')
    # Detect filetype by extension (improve by detectin real file type)
    root, ext = os.path.splitext(name)
    if ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
        filetype = 'image'
    elif ext in ['.blend', '.txt', '.zip']:
        filetype = 'file'
    elif ext in ['.mov', '.avi', '.mp4', '.m4v']:
        filetype = 'video'
    else:
        filetype = 'file'
    # Hash name based on file name, user id and current timestamp
    hash_name = name + str(current_user.objectid) + str(round(time.time()))
    link = hashlib.sha1(hash_name).hexdigest()
    link = os.path.join(link[:2], link + ext)

    api = SystemUtility.attract_api()
    node_type = NodeType.find_first({
        'where': '{"name" : "asset"}',
        }, api=api)
    # We will create the Node object later on, after creating the file object
    node_asset_props = dict(
        name=name,
        #description=a.description,
        #picture=picture,
        user=current_user.objectid,
        node_type=node_type._id,
        #parent=node_parent,
        properties=dict(
            content_type=filetype,
            #file=a.link[4:],
            status='processing'))

    src_dir_path = os.path.join(app.config['UPLOAD_DIR'], str(current_user.objectid))

    # Move the file in designated location
    destination_dir = os.path.join(app.config['SHARED_DIR'], link[:2])
    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    # (TODO) Check if filename already exsits
    src_file_path = os.path.join(src_dir_path, name)
    dst_file_path = os.path.join(destination_dir, link[3:])
    # (TODO) Thread this operation

    shutil.copy(src_file_path, dst_file_path)

    if filetype == 'file':
        mime_type = 'application'
    else:
        mime_type = filetype
    content_type = "{0}/{1}".format(mime_type, ext.replace(".", ""))

    node_file = File({
        'name': link,
        'filename': name,
        'user': current_user.objectid,
        'backend': 'cdnsun',
        'md5': '',
        'content_type': content_type,
        'length': 0
        })

    node_file.create(api=api)

    node_asset_props['properties']['file'] = node_file._id
    if parent_id:
        node_asset_props['parent'] = parent_id
    node_asset = Node(node_asset_props)
    node_asset.create(api=api)

    return jsonify(
        link=link,
        name=name,
        filetype=filetype,
        asset_id=node_asset._id)


