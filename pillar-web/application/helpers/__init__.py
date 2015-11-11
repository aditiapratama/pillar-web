import hashlib
import urllib

from math import ceil
from flask import url_for
from flask import request
from flask.ext.login import current_user
from pillarsdk import File
from pillarsdk.exceptions import ResourceNotFound



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
        try:
            project.properties.picture_square = File.find(
                project.properties.picture_square, api=api)
        except ResourceNotFound:
            project.properties.picture_square = None
    if project.properties.picture_header:
        # Collect the picture header file object
        try:
            project.properties.picture_header = File.find(
                project.properties.picture_header, api=api)
        except ResourceNotFound:
            project.properties.picture_header = None


def gravatar(email, size=64, consider_settings=True):
    parameters = {'s':str(size), 'd':'mm'}
    return "https://www.gravatar.com/avatar/" + \
        hashlib.md5(str(email)).hexdigest() + \
        "?" + urllib.urlencode(parameters)


def pretty_date(time=False):
    """Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff <= 7:
        return str(day_diff) + " days ago"
    if day_diff <= 31:
        week_count = day_diff/7
        if week_count == 1:
            return str(week_count) + " week ago"
        else:
            return str(week_count) + " weeks ago"
    if day_diff <= 365:
        if day_diff < 32:
            return str(day_diff/30) + " month ago"
        else:
            return str(day_diff/30) + " month ago"
    return str(day_diff/365) + " years ago"


def current_user_is_authenticated():
    return current_user.is_authenticated()
