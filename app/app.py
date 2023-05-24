from quart import Quart
from app.config import DevelopmentConfig, ProductionConfig  # Import the config you want to use
from app.views import views
from app.api import api


def create_app():
    app = Quart(__name__)
    app.config.from_object(ProductionConfig)

    # Register blueprints
    app.register_blueprint(views)
    app.register_blueprint(api, url_prefix='/api')

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)