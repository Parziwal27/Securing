from flask import request
from flask_restx import Resource, fields, Namespace
from flask_jwt_extended import create_access_token
from models.user import create_temporary_user, get_user_by_username, check_password, get_user_by_email, confirm_user, get_temp_user_by_id
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

verification_model = auth_ns.model('Verification', {
    'user_id': fields.String(required=True, description='The temporary user ID'),
    'token': fields.String(required=True, description='The verification token')
})

initiate_verification_model = auth_ns.model('InitiateVerification', {
    'user_id': fields.String(required=True, description='The temporary user ID')
})

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    @auth_ns.response(201, 'User registration initiated')
    @auth_ns.response(400, 'Bad request')
    def post(self):
        """Initiate user registration"""
        if not request.is_json:
            return {"msg": "Missing JSON in request"}, 400

        data = request.json
        required_fields = ['username', 'password', 'email', 'mobile', 'first_name', 'last_name']
        
        if not all(field in data for field in required_fields):
            return {"msg": "Missing required fields"}, 400

        if get_user_by_username(data['username']):
            return {"msg": "Username already exists"}, 400

        if get_user_by_email(data['email']):
            return {"msg": "Email already exists"}, 400

        if not is_valid_email(data['email']):
            return {"msg": "Invalid email address"}, 400

        if not is_valid_phone(data['mobile']):
            return {"msg": "Invalid phone number"}, 400

        temp_user = create_temporary_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            mobile=data['mobile'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )

        # Initiate mobile number verification
        send_verification_sms(temp_user['mobile'])

        return {"msg": "Registration initiated. Use the user_id to verify your mobile number.", "user_id": str(temp_user['_id'])}, 201

@auth_ns.route('/initiate-mobile-verification')
class InitiateMobileVerification(Resource):
    @auth_ns.expect(initiate_verification_model)
    @auth_ns.response(200, 'Verification SMS sent')
    @auth_ns.response(400, 'Bad request')
    def post(self):
        """Initiate mobile verification"""
        user_id = request.json.get('user_id')
        temp_user = get_temp_user_by_id(user_id)
        if not temp_user:
            return {"msg": "Invalid user ID"}, 400
        
        send_verification_sms(temp_user['mobile'])
        return {"msg": "Verification SMS sent. Check your phone for the verification code."}, 200

@auth_ns.route('/verify/mobile')
class VerifyMobile(Resource):
    @auth_ns.expect(verification_model)
    @auth_ns.response(200, 'Mobile number verified successfully')
    @auth_ns.response(400, 'Invalid token or user ID')
    def post(self):
        """Verify user's mobile number"""
        user_id = request.json.get('user_id')
        token = request.json.get('token')
        if not user_id or not token:
            return {"msg": "Missing user ID or token"}, 400

        temp_user = get_temp_user_by_id(user_id)
        if not temp_user:
            return {"msg": "Invalid user ID"}, 400

        if verify_mobile_token(temp_user, token):
            confirm_user(temp_user)
            return {"msg": "Mobile number verified successfully. User registration complete."}, 200
        else:
            return {"msg": "Invalid or expired token"}, 400

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
            access_token = create_access_token(identity=username)
            return {"access_token": access_token}, 200
        else:
            return {"msg": "Bad username or password"}, 401
