from flask import Flask
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from flask_restx import Api
from config.jwt import configure_jwt
from config.limiter import configure_limiter
from resources.auth import auth_ns, user_ns
from resources.gateway import gateway_ns

app = Flask(__name__)
CORS(app)
metrics = PrometheusMetrics(app)

authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'Add a JWT with **Bearer &lt;JWT&gt;**'
    }
}

api = Api(app, version='1.0', title='Claims Management API', description='A simple Claims Management API', 
          authorizations=authorizations, security='Bearer Auth')

# Setup JWT
jwt = configure_jwt(app)

# Setup rate limiting
limiter = configure_limiter(app)

# Register namespaces
api.add_namespace(auth_ns)
api.add_namespace(gateway_ns)
api.add_namespace(user_ns, path='/api/user')

@app.route('/metrics')
def metrics_endpoint():
    return metrics.export()

if __name__ == '__main__':
    app.run(debug=True)