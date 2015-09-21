from math import ceil
from flask import url_for
from flask import request
from flask import abort
from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk import File
from pillarsdk.users import User
from pillarsdk.organizations import Organization
from application import SystemUtility


class Pagination(object):
    """Pagination snippet coming from http://flask.pocoo.org/snippets/44/
    """

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def percentage(items, total):
    if total == 0: return 0.0
    return float(items) * 100 / float(total)


class UserProxy(object):
    """This class looks up a username and matches it either to an organization
    or to than an actual user and returns the basic information.
    Note that this is not proper proxy, but the name makes sense currently."""

    def __init__(self, name):
        self.api = SystemUtility.attract_api()
        # Check if organization exists
        user = Organization.find_first({
            'where': '{"url" : "%s"}' % (name),
            }, api=self.api)
        if user:
            self.is_organization = True
            self.name = user.name
            self.url = user.url
            self.description = user.description
        else:
            # Check if user exists
            user = User.find_first({
                'where': '{"username" : "%s"}' % (name),
                }, api=self.api)
            if user:
                self.is_organization = False
                self.name = user.first_name
                self.url = user.username
            else: return abort(404)
        self._id = user._id

    def projects(self):
        """Get list of project for the user"""
        # Find node_type project id (this could become static)
        node_type = NodeType.find_first({
            'where': '{"name" : "project"}',
            }, api=self.api)
        if not node_type: return abort(404)

        # Define key for querying for the project
        if self.is_organization:
            user_path = 'properties.organization'
        else:
            user_path = 'user'

        # Query for the project
        # TODO currently, this system is weak since we rely on the user property
        # of a node when searching for a project using the user it. This allows
        # us to find a project that belongs to an organization also by requesting
        # the user that originally created the node. This can be fixed by
        # introducing a 'user' property in the project node type.

        projects = Node.all({
            'where': '{"node_type" : "%s", "%s": "%s"}'\
                % (node_type._id, user_path, self._id),
            }, api=self.api)

        for project in projects._items:
            if project.properties.picture_square:
                # Collect the picture square file object
                project.properties.picture_square = File.find(
                    project.properties.picture_square, api=self.api)
            if project.properties.picture_header:
                # Collect the picture header file object
                project.properties.picture_header = File.find(
                    project.properties.picture_header, api=self.api)
        return projects

    def project(self, project_name):
        """Get single project for one user. The project is searched by looking
        up project directly associated with that user or organization."""
        # Find node_type project id (this could become static)
        node_type = NodeType.find_first({
            'where': '{"name" : "project"}',
            }, api=self.api)
        if not node_type: return abort(404)

        # Define key for querying for the project
        if self.is_organization:
            user_path = 'properties.organization'
        else:
            user_path = 'user'

        project_node = Node.find_first({
        'where': '{"node_type" : "%s", "properties.url" : "%s", "%s": "%s"}'\
            % (node_type._id, project_name, user_path, self._id),
        }, api=self.api)
        if not project_node: return abort(404)
        return project_node


    def __str__(self):
        return "<{0}>".format(self.name)
