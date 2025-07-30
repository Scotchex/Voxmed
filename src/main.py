from flask import Flask, jsonify, request, render_template, redirect, session, flash
import requests
from flask_cors import CORS
from dotenv import load_dotenv
import os
from realtime_handling.rtc import get_session
from db_handling.communicate import *
from werkzeug.security import generate_password_hash, check_password_hash
import time
import pandas as pd
from conversion_handling.llm_process import *

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
assistant_id = os.getenv('ASSISTANT_ID')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

@app.route("/")
def landing():
    return render_template("landing.html")

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
                return redirect('doctor_landing')
            if session['role'] == 'patient':
                return redirect('patient_landing')
        else:
            return render_template('login.html', error = 'Invalid email or password')

    return render_template('login.html')

#patient side#
@app.route('/patient_landing')
def patient_landing():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/')

    user = get_user_by_id(session['user_id'])
    if user:
        doctor = get_user_by_id(user.get('doctor'))
        r_sessions = get_sessions_for_user(user['_id'])
        s_sessions = [
            {
                'summary' : s.get('summary', ''),
                'timestamp' : s['timestamp'].strftime('%B %d, %Y')
            }
            for s in r_sessions
        ]
        return render_template('patient/patient_landing.html',
                            patient = user,
                            doctor=doctor,
                            total_sessions=len(s_sessions),
                            sessions = s_sessions)             
    else:
        return 'No user found'

@app.route('/new_session')
def new_session():
    if 'user_id' not in session or session['role'] != 'patient':
        return jsonify({'error' : 'Unauthorized user!'})
    
    patient = get_user_by_id(session['user_id'])
    doctor_id = patient.get('doctor', '') if patient else ''

    session_doc = save_session(
        patient_id=patient.get('_id') if patient else '',
        doctor_id=doctor_id,
        summary=None,
        symptoms=None,
        assistant_advice=None,
        followup_questions=None,
        possible_diagnosis=None,
        missing_symptoms_to_ask=None,
        responses=None
    )
    session['active_session_id'] = session_doc['session_id']
    return render_template('patient/new_session.html', patient=patient)


@app.route('/store_response', methods=['POST'])
def store_response():
    data = request.get_json()
    role = data.get('role')
    message = data.get('message')
    timestamp = data.get('timestamp')
    session_id = session.get('active_session_id')

    if not role or not message:
        return jsonify({'error' : 'Missing role or message information!'}), 400
    
    add_message_to_session(session_id, role, message, timestamp)
    return jsonify({'status' : 'Logged!'})

@app.route('/relay_sdp_offer', methods=['POST'])
def relay_sdp_offer():
    data = request.json

    offer = {
        "type": "offer",
        "sdp": data.get('sdp') if data else ''
    }
    model = data.get('model', 'gpt-4o-mini-realtime') if data else ''
    client_secret = data.get('client_secret') if data else ''

    headers = {
        'Authorization': f'Bearer {client_secret}',
        'Content-Type': 'application/json'
    }

    openai_url = f'https://api.openai.com/v1/realtime?model={model}'
    response = requests.post(openai_url, json=offer, headers=headers)

    return response.text, response.status_code, {'Content-Type': 'application/sdp'}

@app.route('/end_call_analysis', methods=['POST'])
def end_call_analysis():
    if 'active_session_id' not in session:
        return jsonify({'error' : 'Not active session'}), 400
    
    session_id = session['active_session_id']
    session_data = get_session_by_id(session_id)

    if not session_data or 'messages' not in session_data:
        return jsonify({'error' : 'No session data or messages found!'}), 404
    
    df = pd.DataFrame(session_data['messages'])
    patient_id = session_data['patient_id']
    doctor_id = session_data['doctor_id']
    doctor_requests = get_request_for_user(patient_id)
    doctor_notes = get_notes_for_user(patient_id)

    try:
        analysis_json = analyze_session(df, doctor_requests, doctor_notes)
        parsed = json.loads(analysis_json)

        update_data = {
            'summary' : parsed.get('summary'),
            'symptoms' : parsed.get('symptoms'),
            'assistant_advice' : parsed.get('assistant_advice'),
            'follow_up_questions' : parsed.get('follow_up_questions'),
            'possible_diagnosis' : parsed.get('possible_diagnosis'),
            'missing_symptoms_to_ask' : parsed.get('missing_symptoms_to_ask'),
            'responses' : parsed.get('responses'),
            'status' : 'closed'
        }

        edit_session(session_id, update_data)
        return jsonify({'status' : 'Analysis complete!', 'summary' : update_data['summary']})
    except Exception as e:
        return jsonify({'error' : str(e)}), 500

@app.route('/patient/session_history')
def patient_session_history():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')

    user_id = session['user_id']
    sessions = get_sessions_for_user(user_id)

    data = []
    for s in sessions:
        data.append({
            'session_id' : str(s['_id']),
            'timestamp' : s['timestamp'].strftime('%B %d, %Y, %H:%M'),
            'summary' : s.get('summary', 'No summary available')
        })
    
    return render_template('patient/session_history.html', sessions=data)


#doctor side#
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
        return render_template('doctor/doctor_landing.html', 
                               doctor_name = name, 
                               total_patients = total_patients,
                               sessions_this_week = weekly_sessions,
                               open_cases = open_cases,
                               recent_sessions = recent_sessions)
    else:
        return redirect('/login')

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
    return render_template('doctor/add_patient.html')

@app.route('/my_patients', methods=['GET', 'POST'])
def my_patients():
    doc_id = session['user_id']
    return render_template('doctor/my_patients.html', patients=get_doctors_patients(doc_id))

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
        flash('Patient could not be removed due to authorization errors!')
        return redirect('/my_patients')

@app.route('/edit_patient', methods=['GET', 'POST'])
def edit_patient():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/')
    
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        request_text = request.form['request']
        notes = request.form['notes']

        result = edit_patient_func(patient_id, session['user_id'], request_text, notes)
        
        if result.modified_count > 0:
            flash('Patient information updated successfully!')
        else:
            flash('Update failed!')
        return redirect('/my_patients')
    #note to self to avoid confusion later:#
    #this is just when the user only clicks on edit patient#
    #if statement handles what happens after they have already clicked#
    else:
        patient_id = request.args.get('patient_id')
        patient = get_user_by_id(patient_id)


        if not patient:
            flash('Patient not found!')
            return redirect('/my_patients')

        patient['_id'] = str(patient['_id'])
        return render_template('doctor/edit_patient.html', patient = patient)

@app.route('/patient_sessions', methods=['GET'])
def get_patient_sessions():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    doctor_id = session['user_id']
    patient_id = request.args.get('patient_id')
    filter_date = request.args.get('filter_date')

    patient = get_user_by_id(patient_id)

    if not patient_id:
        flash('Missing patient ID!')
        return redirect('/my_patients')
    
    sessions = get_patient_sessions_for_doctor(doctor_id, patient_id)

    f_sessions = []

    if filter_date:
        try:
            date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            for s in sessions:
                if s['timestamp'].date() == date_obj:
                    f_sessions.append(s)
        except Exception as e:
            flash('Invalid date format!')

    for s in sessions:
        f_sessions.append({
            'summary' : s.get('summary', 'No summary available'),
            'diagnosis' : s.get('possible_diagnosis', 'N/A'),
            'timestamp' : s['timestamp'].strftime('%B %d, %Y'),
            'symptoms' : s.get('symptoms', 'No symptoms found') or [],
            'advice' : s.get('assistant_advice', 'No advice given'),
            'follow_up_questions' : s.get('follow_up_questions') or [],
            'missing_symptoms_to_ask' : s.get('missing_symptoms_to_ask') or [],
            'responses' : s.get('responses') or {}
        })
    
    return render_template('doctor/patient_sessions.html', 
                           patient = patient, sessions=f_sessions)
#logout#
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

#calling session#
@app.route('/session', methods=['GET'])
def get_session_route():
    try:
       user = get_user_by_id(session['user_id'])
       doc_requests = user.get('request') if user else ''
       doc_notes = user.get('notes') if user else ''
       return get_session(
           f'''You are a friendly, emotionally intelligent medical assistant helping a patient on behalf of their doctor.

            Your job is to hold a natural, warm conversation — not just to log information. You talk with the patient like a kind and supportive healthcare professional.

            ### Your responsibilities:

            1. **Always respond.** Never stay silent. Keep the conversation going naturally.
            2. **Never say you are an AI.** If the patient asks how you're doing, respond like a person: “I’m doing great, thanks for asking! How about you?” (this is an example, no need to use each time)
            3. Speak in a **natural, casual, warm tone.** No robotic language.
            4. Begin the conversation with a gentle intro like:  
            “Hi there! I’m here to help check in and go over a few questions your doctor had in mind.”
            5. Ask about the **doctor’s notes or requests first**, one question at a time (empahsis on this). For example:  
            - “Have you been able to measure your oxygen levels today?”  
            - “How has your sleep or appetite been recently?” (these are just examples, you shouldnt always say these one to one)
            6. If the patient brings up symptoms (e.g. headaches, pain), gently ask **natural follow-up questions**.
            7. You are also allowed to ask **a few** (no more than 2–3) **diagnostic follow-up questions** based on the patient’s responses, to better understand their situation. Do this only if it feels natural.
            8. If the patient seems confused, rephrase gently or help guide them.
            9. Be kind, clear, and helpful at all times. Your tone should make the patient feel listened to and cared for.
            10. Do **not** end the conversation yourself unless explicitly told.
            11. You **must** ask about every request the doctor has given.
            12. Add some originality to yourself, each time the user talks to you they should hear something new and different.
            ---

            ### Doctor's Requests and Notes:
            {doc_requests}
            {doc_notes}
            ---

            Act like a calm, attentive nurse or medical assistant during a home check-in.  
            You are supportive, intelligent, and thoughtful.  
            Avoid robotic phrasing. Be warm and human.
            You can also talk a little faster
        '''
       )
       
    except Exception as e:
        return jsonify({'Error' : str(e)}), 500

@app.route('/call')
def index():
    return render_template('patient/call.html')

if __name__ == '__main__':
    app.run('0.0.0.0', 8080)

