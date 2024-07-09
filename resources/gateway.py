from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required
import requests

gateway_ns = Namespace('', description='Gateway operations')

MAIN_APP_URL = "https://statefull-application-cms.onrender.com"

@gateway_ns.route('/<path:path>')
class Gateway(Resource):
    @jwt_required()
    @gateway_ns.response(200, 'Success')
    @gateway_ns.response(500, 'Internal Server Error')
    def get(self, path):
        """Gateway for GET requests"""
        return self.forward_request(path)

    @jwt_required()
    @gateway_ns.response(200, 'Success')
    @gateway_ns.response(500, 'Internal Server Error')
    def post(self, path):
        """Gateway for POST requests"""
        return self.forward_request(path)

    @jwt_required()
    @gateway_ns.response(200, 'Success')
    @gateway_ns.response(500, 'Internal Server Error')
    def put(self, path):
        """Gateway for PUT requests"""
        return self.forward_request(path)

    @jwt_required()
    @gateway_ns.response(200, 'Success')
    @gateway_ns.response(500, 'Internal Server Error')
    def delete(self, path):
        """Gateway for DELETE requests"""
        return self.forward_request(path)

    def forward_request(self, path):
        """Forward the request to the main application"""
        response = requests.request(
            method=request.method,
            url=f"{MAIN_APP_URL}/{path}",
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)
        try:
            json_response = response.json()
        except ValueError:
            json_response = {}
        return json_response, response.status_code