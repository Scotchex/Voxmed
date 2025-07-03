from flask import Flask, jsonify, request, render_template, redirect, session
import requests
from flask_cors import CORS
from dotenv import load_dotenv
import os
from realtime_handling.rtc import get_session
from db_handling.communicate import *
from werkzeug.security import generate_password_hash, check_password_hash

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
            return redirect('/doctor_landing')
        else:
            return render_template('login.html', error = 'Invalid email or password')

    return render_template('login.html')

@app.route('/patient_landing')
def patient_landing():
    return 'a'

@app.route('/doctor_landing')
def doctor_landing():
    return render_template('doctor_landing.html')
@app.route('/session', methods=['GET'])
def get_session_route():
    try:
       return get_session()
    except Exception as e:
        return jsonify({'Error' : str(e)}), 500
    
if __name__ == '__main__':
    app.run('0.0.0.0', 8080)