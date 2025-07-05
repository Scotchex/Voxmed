from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from datetime import datetime
import os
from pymongo.results import UpdateResult
from datetime import datetime, timedelta

load_dotenv()
uri = os.getenv('MONGODB_URI')

client = MongoClient(uri)
#setting up the database#
db = client['Voxmed']
user_collection = db['users']
sessions_collection = db['sessions']

#users functions#
def create_user(name, email, password, role):
    existing = user_collection.find_one({'email': email})
    if existing == True:
        return {'success' : False, 'message' : 'Email already registered'}
    
    user = {
        'name' : name, 
        'email' : email,
        'password' : password, #need to hash this on flask
        'role' : role
    }

    result = user_collection.insert_one(user)
    return {'success' : True, 'user_id' : str(result.inserted_id)}

def get_user_by_email(email): #this is for doctor search use
    user = user_collection.find_one({'email' : email})
    if user:
        user['_id'] = str(user['_id'])
    return user

def get_user_by_id(user_id):
    try:
        user = user_collection.find_one({'_id' : ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
        return user
    except:
        return None

def get_all_patients():
    patients_cursor = user_collection.find({'role' : 'patient'})
    patients = []

    for patient in patients_cursor:
        patients.append({
            '_id' : str(patient['_id']),
            'name' : patient.get('name'),
            'email' : patient.get('email')
        })
        
    return patients

def get_doctors_patients(doctor_id):
    patients_cursor = user_collection.find({
        'role' : 'patient',
        'doctor' : doctor_id
    })
    patients = []

    for patient in patients_cursor:
        patients.append({
            '_id' : str(patient['_id']),
            'name' : patient.get('name'),
            'email' : patient.get('email'),
            'request' : patient.get('request')

        })

    return patients

def add_doctor(patient_id, doctor_id):
    result = user_collection.update_one(
        {'_id' : ObjectId(patient_id), 'role' : 'patient'},
        {'$set' : {'doctor' : doctor_id}}
    )
    return result.modified_count > 0

def add_request(patient_id, request):
    result = user_collection.update_one(
        {'_id' : ObjectId(patient_id), 'role' : 'patient'},
        {'$set' : {'request' : request}}
    )
    return result.modified_count > 0

def add_notes(patient_id, notes):
    result = user_collection.update_one(
        {'_id' : ObjectId(patient_id), 'role' : 'patient'},
        {'$set' : {'notes' : notes}}
    )
    return result.modified_count > 0

def get_recent_sessions_for_doctor(doctor_id, limit=5):
    sessions = sessions_collection.find(
        {'doctor_id': ObjectId(doctor_id)}
    ).sort('timestamp', -1).limit(limit)

    return [
        {
            '_id': str(s['_id']),
            'patient_id': str(s['patient_id']),
            'transcript': s.get('transcript', ''),
            'diagnosis': s.get('diagnosis', 'N/A'),
            'timestamp': s['timestamp'].strftime('%B %d, %Y'),
        }
        for s in sessions
    ]

def remove_doctor(user_id, doctor_id) -> UpdateResult:
    result = user_collection.update_one(
        {'_id' : ObjectId(user_id), 
         'role' : 'patient', 
         'doctor' : doctor_id},
         {'$unset' : {'doctor' : ""}}
    )
    return result

def edit_patient_func(user_id, doctor_id, request_text, notes):
    result = user_collection.update_one(
        {'_id' : ObjectId(user_id), 'doctor' : doctor_id},
        {'$set' : {'request' : request_text, 'notes' : notes}}
    )
    return result
#sessions functions#
def save_session(patient_id, doctor_id, transcript, summary, possible_diagnosis=None, status='open'):
    session_data = {
        'patient_id' : ObjectId(patient_id),
        'doctor_id' : ObjectId(doctor_id),
        'transcript' : transcript,
        'diagnosis' : possible_diagnosis,
        'timestamp' : datetime.now(),
        'status' : status,
        'summary' : summary
    }

    result = sessions_collection.insert_one(session_data)
    return {'success' : True, 'session_id' : str(result.inserted_id)}

def get_sessions_for_doctor(doctor_id):
    sessions = sessions_collection.find({'doctor_id' : ObjectId(doctor_id)})
    return [{**s, '_id' : str(s['_id'])} for s in sessions]

def get_sessions_this_week_for_doctor(doctor_id):
    one_week_ago = datetime.now() - timedelta(days=7)
    sessions = sessions_collection.find({
        'doctor_id': ObjectId(doctor_id),
        'timestamp': {'$gte': one_week_ago}
    })

    return [{**s, '_id': str(s['_id'])} for s in sessions]

def count_open_cases_for_doctor(doctor_id):
    return sessions_collection.count_documents({
        'doctor_id': ObjectId(doctor_id),
        'status': 'open'
    })

def get_sessions_for_user(user_id):
    sessions = sessions_collection.find({'user_id' : ObjectId(user_id)})
    return [{**s, '_id' : str(s['_id'])} for s in sessions]

