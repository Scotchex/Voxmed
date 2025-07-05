from openai import OpenAI
import pandas as pd
import json
import os
#1.73 for 5ish instances#this is for me#

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
client = OpenAI()

def analyze_session(df:pd.DataFrame, doctor_requests, doctor_notes):
    conversation_csv = df.to_csv(index=False)
    prompt = f"""
        You are an AI medical assistant reviewing a medical conversation between a patient and an assistant. 
        Below is the transcript in CSV format, with columns: timestamp, role (either 'user' or 'assistant'), and message.
        {conversation_csv}
        Below are the requests of the doctor.
        {doctor_requests}
        Below are the notes of the doctor (this is an optional field, might be empty)
        {doctor_notes}
        Your job is to extract clinically useful information to help the doctor quickly understand what was discussed and what was missed.

        Return the following fields in JSON format:

        1. "summary": Briefly summarize the patient's concerns and symptoms.
        2. "symptoms": List the symptoms clearly mentioned by the patient.
        3. "assistant_advice": Any advice or preliminary interpretation offered by the assistant.
        4. "follow_up_questions": What follow-up questions should a doctor ask to complete the case?
        5. "possible_diagnosis": What condition(s) could this be, based on the conversation?
        6. "missing_symptoms_to_ask": What symptoms were not asked or confirmed, but are medically relevant based on the context?
        7. "responses": This is most important.
        - Find any specific requests from the doctor or assistant like:
            - "measure blood pressure"
            - "check oxygen saturation"
            - "track when symptoms occur"
        - For each, indicate:
            - the exact request (this will only come from the role with assistant, never user),
            - whether the patient responded (status: 'answered' or 'missing'),
            - the patient's exact response taken from the transcript (if the O2 level was 94 this would be "My O2 level is 94% as of now"),
            - the exact value the patient gave (if the O2 level was 94% this would be a dictionary with key o2 and value 94)

        Return in this JSON format:

        {{
        "summary": "...",
        "symptoms": ["..."],
        "assistant_advice": "...",
        "follow_up_questions": ["..."],
        "possible_diagnosis": "...",
        "missing_symptoms_to_ask": ["..."],
        "responses": [
            {{
            "request": "...",
            "patient_response": "...",
            "value:" "...", (here if there is no numerical value, you should put a two or three word description of what the patient said)
            "status": "answered"
            }},
            ...
        ]
        }}

    """

    response = client.responses.create(
        model = 'gpt-4.1',
        input=prompt
    )
    
    return response.output_text