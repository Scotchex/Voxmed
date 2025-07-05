from flask import Flask, jsonify, request, render_template
import requests
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
# assistant_id = os.getenv('ASSISTANT_ID') #

def get_session(prompt:str='You are a helpful agent'):
    url = "https://api.openai.com/v1/realtime/sessions"

    payload = {
        'model': 'gpt-4o-realtime-preview-2024-12-17',
        'modalities': ['audio', 'text'],
        'instructions' : prompt,
        'voice' : 'sage'
    }

    headers = {
        'Authorization' : f'Bearer {openai_api_key}',
        'Content-Type' : 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    return response.json()