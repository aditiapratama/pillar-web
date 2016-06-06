import json
from pillarsdk import utils
from pillarsdk.users import User
from pillarsdk.organizations import Organization

from flask import Blueprint
from flask import render_template
from flask import flash
from flask import session
from flask import redirect
from flask import request
from flask import url_for

from application.helpers import Pagination
from application import system_util

organizations = Blueprint('organizations', __name__)


@organizations.route("/")
def index():
    """Generic function to list all nodes
    """
    # Pagination index
    page = request.args.get('page', 1)
    max_results = 50

    api = system_util.pillar_api()

    organizations = Organization.all({
        'max_results': max_results,
        'page': page}, api=api)

    # Build the pagination object
    pagination = Pagination(int(page), max_results, organizations._meta.total)

    template = 'organizations/index.html'

    return render_template(
        template,
        title='organizations',
        organizations=organizations,
        pagination=pagination)

@organizations.route("/add")
def add():
    return 'ok'

@organizations.route("/<org_id>/view")
def view(org_id):
    return 'ok'

@organizations.route("/<org_id>/edit")
def edit(org_id):
    return 'ok'
