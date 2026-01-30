from .routes import query_bp,response_bp,watcher_bp
from .imports import *

def getRecieve_app():
    """Flask app factory."""
    app = Flask(__name__,)
    CORS(app, resources={r"*": {"origins": "*"}})  
    app.register_blueprint(query_bp)
    app.register_blueprint(response_bp)
    app.register_blueprint(watcher_bp)
    return app

