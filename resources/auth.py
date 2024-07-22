from flask import jsonify, request, make_response
from flask_restx import Resource, fields, Namespace
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from models.user import get_user_by_username, check_password, get_user_by_email, create_user, get_user_by_mobile, get_temp_user_by_id, confirm_user
from utils.validators import is_valid_email, is_valid_phone
from config.database import users_collection
import requests

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
        required_fields = ['username', 'password', 'email', 'mobile', 'first_name', 'last_name','age']
        
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

        user = create_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            mobile=data['mobile'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=int(data['age'])
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

        if user and check_password(user['Password'], password):
            access_token = create_access_token(identity=username)
            return {"msg": "Login successful", "access_token": access_token,"isAdmin": user["isAdmin"]}, 200
        else:
            return {"msg": "Bad username or password"}, 401

user_ns = Namespace('user', description='User operations')
confirmuser = user_ns.model('Confirm', {
    'username': fields.String(required=True, description='The username')
})

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
                "username": user['Username'],
                "email": user['Email'],
                "mobile": user['Mobile'],
                "first_name": user['First_name'],
                "last_name": user['Last_name'],
                "User_status":user["isVerified"]
            }, 200
        else:
            return {"msg": "User not found"}, 404

@user_ns.route('/confirm')
class ConfirmUser(Resource):
    @jwt_required()
    @user_ns.expect(confirmuser)
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
            user = get_user_by_username(data['username'])
            if not user:
                return {"msg": "Temporary user not found"}, 404

            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return {"msg": "Authorization token missing"}, 400
            user["isVerified"]="accepted"
            users_collection.update_one({'Username': data['username']}, {'$set': user})

            return {"msg": "User confirmed successfully"}, 200


        except Exception as e:
            return {"msg": str(e)}, 500

@user_ns.route('/reject')
class RejectUser(Resource):
    @jwt_required()
    @user_ns.expect(confirmuser)
    @user_ns.response(200, 'User Rejected successfully')
    @user_ns.response(404, 'User not found')    
    def post(self):
        try:
            if not request.is_json:
                return {"msg": "Missing JSON in request"}, 400

            data = request.json
            required_fields = ['username']
            if not all(field in data for field in required_fields):
                return {"msg": "Missing required fields"}, 400
            user = get_user_by_username(data['username'])
            if not user:
                return {"msg": "Temporary user not found"}, 404

            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return {"msg": "Authorization token missing"}, 400
            user["isVerified"]="rejected"
            users_collection.update_one({'Username': data['username']}, {'$set': user})

            return {"msg": "User confirmed successfully"}, 200


        except Exception as e:
            return {"msg": str(e)}, 500


@user_ns.route('/tempusers')
class fetchtempuser(Resource):
    @jwt_required()
    @user_ns.response(200, 'User confirmed successfully')
    @user_ns.response(404, 'User not found')
    def get(self):
        try:
            temp_users = list(users_collection.find({}, {'_id': 0}))
            return make_response(jsonify(temp_users), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)   