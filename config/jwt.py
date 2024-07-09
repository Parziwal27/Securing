from datetime import timedelta
from flask_jwt_extended import JWTManager

def configure_jwt(app):
    app.config['JWT_SECRET_KEY'] = "50a61b16c0e469f1e44585d4b76bbebb178e5a0b00c2854befc9fc8e5b81de41" # Use environment variable in production
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    return JWTManager(app)