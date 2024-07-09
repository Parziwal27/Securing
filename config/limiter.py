from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def configure_limiter(app):
    return Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["1000 per day", "500 per hour"]
    )