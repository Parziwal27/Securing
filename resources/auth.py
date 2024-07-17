from flask import jsonify, request, make_response
from flask_restx import Resource, fields, Namespace
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from models.user import get_user_by_username, check_password, get_user_by_email, create_temporary_user, get_user_by_mobile, get_temp_user_by_id, confirm_user
from utils.validators import is_valid_email, is_valid_phone
from config.database import temp_users_collection

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
        required_fields = ['username', 'password', 'email', 'mobile', 'first_name', 'last_name']
        
        if not all(field in data for field in required_fields):
            return {"msg": "Missing required fields"}, 400
        if not is_valid_email(data['email']):
            return {"msg": "Enter a valid Email"}, 400
        if not is_valid_phone(data["mobile"]):
            return {"msg": "Enter a valid mobile number"}
        if get_user_by_username(data['username']):
            return {"msg": "Username already exists"}, 400
        if get_user_by_mobile(data['mobile']):
            return {"msg": "Number already exists"}, 400
        if get_user_by_email(data["email"]):
            return {"msg": "Email already registered"}, 400
        if int(data['age'])<18:
            return {"msg":"Underage"}, 400

        user = create_temporary_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            mobile=data['mobile'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age']
        )

        if user:
            return {"msg": "User registered successfully", "user_id": str(user['_id'])}, 201
        else:
            return {"msg": "Error registering user"}, 500

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
        if not user:
            return {"msg": "User not found"}, 404

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

@user_ns.route('/confirm')
class ConfirmUser(Resource):
    @user_ns.response(200, 'User confirmed successfully')
    @user_ns.response(404, 'User not found')
    def post(self):
        

        try:
            if not request.is_json:
                return {"msg": "Missing JSON in request"}, 400

            data = request.json
            required_fields = ['username']
            if not all(field in data for field in required_fields):
                return {"msg": "Missing required fields"}, 400
            temp_user = get_temp_user_by_id(data['username'])
            if not temp_user:
                return {"msg": "Temporary user not found"}, 404
            
            access_token = create_access_token(identity=temp_user['username'])
            placeholder_response = post_placeholder({
                "name": temp_user['first_name'] + " " + temp_user['last_name'],
                "age": temp_user['age'],
                "policies": []
            },access_token)
            if placeholder_response.status_code == 201:
                confirm_user(temp_user)
                return {"msg": "User confirmed successfully and placeholder created"}, 200
            else:
                return {"msg": "User confirmed, but failed to create placeholder"}, 500
        except Exception as e:
            return {"msg": str(e)}, 500

def post_placeholder(data,token):
    """Post data to the placeholder endpoint"""
    import requests
    url = 'https://statefull-application-cms.onrender.com/api/policyholder'
    headers = {'Content-Type': 'application/json','Authorization': f'Bearer {token}'}
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error posting to placeholder: {str(e)}")
        print(f"Response content: {e.response.content if e.response else 'No response'}")
        return None
@user_ns.route('/tempusers')
class fetchtempuser(Resource):
    @jwt_required()
    @user_ns.response(200, 'User confirmed successfully')
    @user_ns.response(404, 'User not found')
    def get(self):
        try:
            temp_users = list(temp_users_collection.find({}, {'_id': 0}))
            return make_response(jsonify(temp_users), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)   