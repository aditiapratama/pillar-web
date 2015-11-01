import os
import hashlib
import time
import shutil
from flask import request
from flask import jsonify
from flask import session
from flask.ext.login import login_required
from flask.ext.login import current_user
from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk import File
from application import app
from application import SystemUtility
from application.modules.nodes import nodes
from application.modules.files import process_and_create_file


@nodes.route('/assets/create', methods=['POST'])
@login_required
def assets_create():
    project_id = session['current_project_id']
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

    if filetype == 'file':
        mime_type_base = 'application'
    else:
        mime_type_base = filetype
    mime_type = "{0}/{1}".format(mime_type_base, ext.replace(".", ""))
    node_file = node_file = process_and_create_file(project_id, name, 0, mime_type)

    node_asset_props['properties']['file'] = node_file._id
    if parent_id:
        node_asset_props['parent'] = parent_id
    node_asset = Node(node_asset_props)
    node_asset.create(api=api)

    return jsonify(
        #link=link,
        name=name,
        filetype=filetype,
        asset_id=node_asset._id)
