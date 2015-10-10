import hashlib
import urllib

from math import ceil
from flask import url_for
from flask import request
from pillarsdk import File


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


def attach_project_pictures(project, api):
    """Utility function that queries for file objects referenced in picture
    header and square. In eve we currently can't embed objects in nested
    properties, this is the reason why this exists.
    This function should be moved in the API, attached to a new Project object.
    """
    if project.properties.picture_square:
        # Collect the picture square file object
        project.properties.picture_square = File.find(
            project.properties.picture_square, api=api)
    if project.properties.picture_header:
        # Collect the picture header file object
        project.properties.picture_header = File.find(
            project.properties.picture_header, api=api)


def gravatar(email, size=64, consider_settings=True):
    parameters = {'s':str(size), 'd':'mm'}
    return "https://www.gravatar.com/avatar/" + \
        hashlib.md5(str(email)).hexdigest() + \
        "?" + urllib.urlencode(parameters)

