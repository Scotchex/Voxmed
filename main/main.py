from flask import Flask, jsonify, request, render_template
import requests
from flask_cors import CORS
from dotenv import load_dotenv
import os
from realtime_handling.rtc import get_session

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
assistant_id = os.getenv('ASSISTANT_ID')
app = Flask(__name__)

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
        password = request.form.get('password')

        print(f'Name: {name}, Email: {email}, Password: {password}') #just placeholder for now

        return jsonify({'message':"user successfully created"}) #db logic afterwards
    return render_template('signup.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        #do database stuff#
        print(email, password)
    return render_template('login.html')
@app.route('/session', methods=['GET'])
def session():
    try:
       return get_session()
    except Exception as e:
        return jsonify({'Error' : str(e)}), 500
    
if __name__ == '__main__':
    app.run('0.0.0.0', 8080)