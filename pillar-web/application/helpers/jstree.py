from pillarsdk import Node
from pillarsdk.exceptions import ForbiddenAccess
from pillarsdk.exceptions import ResourceNotFound
from flask.ext.login import current_user


from application import SystemUtility
def jstree_parse_node(node, children=None):
    """Generate JStree node from node object"""
    node_type = node.node_type
    # Define better the node type
    if node_type == 'asset':
        node_type = node.properties.content_type
    parsed_node = dict(
        id="n_{0}".format(node._id),
        text=node.name,
        type=node_type,
        children=False)
    # Append children property only if it is a directory type
    if node_type in ['group', 'storage', 'group_texture']:
        parsed_node['children'] = True

    return parsed_node


def jstree_get_children(node_id, project_id=None):
    api = SystemUtility.attract_api()
    children_list = []
    lookup = {
        'projection': {
            'name': 1, 'parent': 1, 'node_type': 1, 'properties.order': 1,
            'properties.status': 1, 'properties.content_type': 1, 'user': 1,
            'project': 1},
        'sort': 'properties.order'}
    if node_id:
        if node_id.startswith('n_'):
            node_id = node_id.split('_')[1]
        lookup['where'] = '{"parent": "%s"}' % node_id
    elif project_id:
        lookup['where'] = '{"project": "%s", "parent" : {"$exists": false}}' % project_id

    try:
        children = Node.all(lookup, api=api)
        for child in children['_items']:
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
    """Give a node, traverse the tree bottom to top and expand the relevant
    branches.

    :param node: the base node, where tree building starts
    """
    api = SystemUtility.attract_api()
    # Parse the node and mark it as selected
    child_node = jstree_parse_node(node)
    child_node['state'] = dict(selected=True)
    # Get the current node again (with parent data)
    try:
        parent = Node.find(node.parent, api=api)
        # Define the child node of the tree (usually an asset)
    except ResourceNotFound:
        # If not found, we might be on the top level, in which case we skip the
        # while loop and use child_node
        parent = None
    except ForbiddenAccess:
        parent = None
    while parent:
        # Store the child in a new var
        tmp_child = child_node
        # Get the parent's parent
        parent_parent = jstree_parse_node(parent)
        # Get the parent's children (this will also include child_node)
        parent_children = jstree_get_children(parent_parent['id'])
        # Remove the child with matching id with the tmp_child
        parent_children = [x for x in parent_children
                           if x['id'] != tmp_child['id']]
        # Append the tmp_child
        parent_children.append(tmp_child)
        parent_parent.pop('children', None)
        # Overwrite children_node with the current parent
        child_node = parent_parent
        # Set the node to open so that jstree actually displays the nodes
        child_node['state'] = dict(opened=True)
        # Push in the computed children into the parent
        child_node['children'] = parent_children
        # If we have a parent
        if parent.parent:
            try:
                parent = Node.find(parent.parent, {
                    'projection': {
                        'name': 1, 'parent': 1, 'project': 1, 'node_type': 1},
                    }, api=api)
            except ResourceNotFound:
                parent = None
        else:
            parent = None
    # Get top level nodes for the project
    project_children = jstree_get_children(None, node.project)
    nodes_list = [x for x in project_children if x['id'] != child_node['id']]
    nodes_list.append(child_node)
    return nodes_list

