from application import app
from application.modules.nodes import index
from flask.ext.login import login_required

@app.route("/")
@login_required
def homepage():
    """Very minimal setup that returns the nodes index view"""
    return index()
