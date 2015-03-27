from application import app
from application.modules.nodes import index

@app.route("/")
def homepage():
    """Very minimal setup that returns the nodes index view"""
    return index()
