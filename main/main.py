from flask import Flask, jsonify, request, render_template, redirect, session, flash
import requests
from flask_cors import CORS
from dotenv import load_dotenv
import os
from realtime_handling.rtc import get_session
from db_handling.communicate import *
from werkzeug.security import generate_password_hash, check_password_hash
import time

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
assistant_id = os.getenv('ASSISTANT_ID')
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route('/call')
def index():
    return render_template('call.html')

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password_raw = request.form.get('password')
        role = request.form.get('role')
        #hashing the password#
        hashed_password = generate_password_hash(str(password_raw), method='pbkdf2:sha256', salt_length=16)
        create_user(name, email, hashed_password, role)
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user_by_email(email)
        
        if user and check_password_hash(user['password'], str(password)):
            session['user_id'] = user['_id']
            session['role'] = user['role']
            if session['role'] == 'doctor':
                return redirect('/doctor_landing')
        else:
            return render_template('login.html', error = 'Invalid email or password')

    return render_template('login.html')

@app.route('/patient_landing')
def patient_landing():
    return 'a'

@app.route('/doctor_landing')
def doctor_landing():
    if 'user_id' not in session:
        return redirect('/')
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    patients = get_doctors_patients(user_id)
    recent_sessions = get_recent_sessions_for_doctor(user_id)
    total_patients = len(patients)
    weekly_sessions = len(get_sessions_this_week_for_doctor(user_id))
    open_cases = count_open_cases_for_doctor(user_id)
    
    if user:
        name = user['name']
        return render_template('doctor_landing.html', 
                               doctor_name = name, 
                               total_patients = total_patients,
                               sessions_this_week = weekly_sessions,
                               open_cases = open_cases,
                               recent_sessions = recent_sessions)
    else:
        return redirect('/login')


@app.route('/session', methods=['GET'])
def get_session_route():
    try:
       return get_session()
    except Exception as e:
        return jsonify({'Error' : str(e)}), 500

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        doc_request = request.form.get('request')
        notes = request.form.get('notes')
        patient = get_user_by_email(email)
        doc_id = session['user_id']
        if patient and patient['role'] == 'patient' and patient.get('doctor') != doc_id:
            add_doctor(patient['_id'], doctor_id=doc_id)
            add_request(patient['_id'], str(doc_request))
            add_notes(patient['_id'], str(notes))
            
            flash('Successfully added patient!')
            return redirect('/add_patient')
        elif patient and patient['doctor'] == doc_id:
            flash('Patient is already added to account!')
            return redirect('/add_patient')
        else:
            flash('Patient does not exist!')
            return redirect('/add_patient')
    return render_template('add_patient.html')

@app.route('/my_patients', methods=['GET', 'POST'])
def my_patients():
    doc_id = session['user_id']
    return render_template('my_patients.html', patients=get_doctors_patients(doc_id))

@app.route('/remove_patient', methods=['POST'])
def remove_patient():
    doc_id = session['user_id']
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    patient_id = request.form.get('patient_id')
    if not patient_id:
        return 'Missing patient ID', 400
    
    result = remove_doctor(patient_id, doc_id)
    
    if result.modified_count == 1:
        flash('Patient removed!')
        return redirect('/my_patients')
    else:
        flash('Patient could not be removed due to unauthorization errors!')
        return redirect('/my_patients')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')
if __name__ == '__main__':
    app.run('0.0.0.0', 8080)