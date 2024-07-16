from config.database import users_collection, temp_users_collection
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

def get_user_by_username(username):
    return users_collection.find_one({'username': username})

def get_user_by_email(email):
    return users_collection.find_one({'email': email})

def get_user_by_mobile(mobile):
    return users_collection.find_one({'mobile': mobile})

def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)

def create_temporary_user(username, password, email, mobile, first_name, last_name, age):
    hashed_password = generate_password_hash(password)
    temp_user = {
        'username': username,
        'password': hashed_password,
        'email': email,
        'mobile': mobile,
        'first_name': first_name,
        'last_name': last_name,
        'age': age
    }
    result = temp_users_collection.insert_one(temp_user)
    return get_temp_user_by_id(username)

def get_temp_user_by_id(user_id):
    user = temp_users_collection.find_one({'username': user_id})
    if user:
        user['_id'] = str(user['_id'])
    return user

def confirm_user(temp_user):
    users_collection.insert_one({
        'username': temp_user['username'],
        'password': temp_user['password'],
        'email': temp_user['email'],
        'mobile': temp_user['mobile'],
        'first_name': temp_user['first_name'],
        'last_name': temp_user['last_name'],
        'age': temp_user['age']
    })
    temp_users_collection.delete_one({'_id': ObjectId(temp_user['_id'])})
