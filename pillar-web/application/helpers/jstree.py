from pillarsdk import Node
from pillarsdk.exceptions import ForbiddenAccess
from pillarsdk.exceptions import ResourceNotFound
from flask.ext.login import current_user


from application import SystemUtility
def jstree_parse_node(node, children=None):
    """Generate JStree node from node object"""
    node_type = node.node_type
    if node_type == 'asset':
        node_type = node.properties.content_type
    return dict(
        id="n_{0}".format(node._id),
        text=node.name,
        type=node_type,
        children=True)


def jstree_get_children(node_id):
    api = SystemUtility.attract_api()
    children_list = []

    if node_id.startswith('n_'):
        node_id = node_id.split('_')[1]
    try:
        children = Node.all({
            'projection': '{"name": 1, "parent": 1, "node_type": 1, \
                "properties.order": 1, "properties.status": 1, \
                "properties.content_type": 1, "user": 1, "project": 1}',
            'where': '{"parent": "%s"}' % node_id,
            'sort': 'properties.order'}, api=api)
        for child in children._items:
            # Skip nodes of type comment
            if child.node_type not in ['comment', 'post']:
                if child.properties.status == 'published':
                    children_list.append(jstree_parse_node(child))
                elif child.node_type == 'blog':
                    children_list.append(jstree_parse_node(child))
                elif current_user.is_authenticated() and child.user == current_user.objectid:
                    children_list.append(jstree_parse_node(child))
    except ForbiddenAccess:
        pass
    return children_list


def jstree_build_children(node):
    return dict(
        id="n_{0}".format(node._id),
        text=node.name,
        type=node.node_type,
        children=jstree_get_children(node._id)
    )


def jstree_build_from_node(node):
    api = SystemUtility.attract_api()
    open_nodes = [jstree_parse_node(node)]
    # Get the current node again (with parent data)
    try:
        parent = Node.find(node.parent, {
            'projection': '{"project":1 ,"name": 1, "parent": 1',
            }, api=api)
    except ResourceNotFound:
        parent = None
    except ForbiddenAccess:
        parent = None
    while (parent):
        open_nodes.append(jstree_parse_node(parent))
        # If we have a parent
        if parent.parent:
            try:
                parent = Node.find(parent.parent, {
                    'projection': '{"name":1, "parent":1, "project": 1}',
                    }, api=api)
            except ResourceNotFound:
                parent = None
        else:
            parent = None
    open_nodes.reverse()
    #open_nodes.pop(0)

    nodes_list = []

    for node in jstree_get_children(open_nodes[0]['id']):
        # Nodes at the root of the project
        node_dict = {
            'id': node['id'],
            'text': node['text'],
            'type': node['type'],
            'children': True
        }
        if len(open_nodes) > 1:
            # Opening and selecting the tree nodes according to the landing place
            if node['id'] == open_nodes[1]['id']:
                current_dict = node_dict
                current_dict['state'] = {'opened': True}
                current_dict['children'] = jstree_get_children(node['id'])
                # Iterate on open_nodes until the end
                for n in open_nodes[2:]:
                    for c in current_dict['children']:
                        if n['id'] == c['id']:
                            current_dict = c
                            break
                    current_dict['state'] = {'opened': True}
                    current_dict['children'] = jstree_get_children(n['id'])

                # if landing_asset_id:
                #     current_dict['children'] = aux_product_tree_node(open_nodes[-1])
                #     for asset in current_dict['children']:
                #         if int(asset['id'][1:])==landing_asset_id:
                #             asset.update(state=dict(selected=True))

        nodes_list.append(node_dict)
    return nodes_list
