import os
from flask import Flask, jsonify
from app.models import db
from app.routes import api
from app.config import config
from sqlalchemy import inspect   # ✅ เพิ่มบรรทัดนี้
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Flask Todo API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'todos': '/api/todos'
            }
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    # ✅ Create tables safely within context
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        if 'todos' not in existing_tables:
            db.create_all()

    # ✅ Global exception handler
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions gracefully"""
        with app.app_context():
            db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    

    return app
