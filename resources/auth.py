from flask import request
from flask_restx import Resource, fields, Namespace
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from models.user import create_user, get_user_by_username, check_password, get_user_by_email, create_temporary_user
from utils.validators import is_valid_email,is_valid_phone
auth_ns = Namespace('auth', description='User authentication operations')

register_model = auth_ns.model('Register', {
    'username': fields.String(required=True, description='The username'),
    'password': fields.String(required=True, description='The password'),
    'email': fields.String(required=True, description='The email address'),
    'mobile': fields.String(required=True, description='The mobile number'),
    'first_name': fields.String(required=True, description='The first name'),
    'last_name': fields.String(required=True, description='The last name')
})

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='The username'),
    'password': fields.String(required=True, description='The password')
})

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    @auth_ns.response(201, 'User registered successfully')
    @auth_ns.response(400, 'Bad request')
    def post(self):
        """Register a new user"""
        if not request.is_json:
            return {"msg": "Missing JSON in request"}, 400

        data = request.json
        required_fields = ['username', 'password', 'email', 'mobile', 'first_name', 'last_name', "Age"]
        
        if not all(field in data for field in required_fields):
            return {"msg": "Missing required fields"}, 400
        if not is_valid_email(data['email']):
            return {"msg":"Enter a valid Email"}, 400
        if not is_valid_phone(data["mobile"]):
            return {"msg":"Enter a valid mobile number"}
        if get_user_by_username(data['username']):
            return {"msg": "Username already exists"}, 400
        if get_user_by_email(data["email"]):
            return{"msg":"Email already registered"}, 400

        
        user = create_temporary_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            mobile=data['mobile'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data["age"]
        )

        return {"msg": "User registered successfully", "user_id": str(user['_id'])}, 201
 
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful')
    @auth_ns.response(400, 'Missing JSON in request')
    @auth_ns.response(401, 'Bad username or password')
    def post(self):
        """Login a user and return an access token"""
        if not request.is_json:
            return {"msg": "Missing JSON in request"}, 400

        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if not username or not password:
            return {"msg": "Missing username or password"}, 400

        user = get_user_by_username(username)

        if user and check_password(user['password'], password):
            # Generate an access token (optional)
            access_token = create_access_token(identity=username)
            return {"msg": "Login successful", "access_token": access_token}, 200
        else:
            return {"msg": "Bad username or password"}, 401

user_ns = Namespace('user', description='User operations')

@user_ns.route('/details')
class UserDetails(Resource):
    @jwt_required()
    @user_ns.response(200, 'User details retrieved successfully')
    @user_ns.response(404, 'User not found')
    def get(self):
        """Get user details"""
        current_user = get_jwt_identity()
        user = get_user_by_username(current_user)
        
        if user:
            return {
                "username": user['username'],
                "email": user['email'],
                "mobile": user['mobile'],
                "first_name": user['first_name'],
                "last_name": user['last_name']
            }, 200
        else:
            return {"msg": "User not found"}, 404