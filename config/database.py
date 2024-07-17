from pymongo import MongoClient
from urllib.parse import quote_plus

encoded_username = quote_plus('kumar231')
encoded_password = quote_plus('rBy6HBjdfYZoGxOV')

connection_string = f'mongodb+srv://{encoded_username}:{encoded_password}@cluster0.t64ui.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

client = MongoClient(connection_string)
db = client['insurance_claim_4']

users_collection = db['user']
