import os
import json
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Initialize Google Sheets client
def get_sheets_client():
    creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    creds_dict = json.loads(creds_json)
    
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

@app.route("/")
def home():
    return "Hello from Render!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook received:", data)
    
    try:
        # Get Google Sheets client
        client = get_sheets_client()
        
        # Open your sheet by ID
        sheet = client.open_by_key('1yGBz02r5zD_wW5aD5SnwXrwJr-Dq2f5P8ytlEgHlp2w').sheet1
        
        # Extract relevant data from webhook
        conversation_data = data.get('data', {})
        transcript = conversation_data.get('transcript', [])
        
        # Build transcript text
        transcript_text = ""
        for turn in transcript:
            role = turn.get('role', 'unknown')
            message = turn.get('message', '')
            transcript_text += f"{role}: {message}\n\n"
        
        # Get summary and metadata
        analysis = conversation_data.get('analysis', {})
        summary = analysis.get('transcript_summary', 'No summary')
        call_duration = conversation_data.get('metadata', {}).get('call_duration_secs', 0)
        
        # Add row to sheet
        row = [
            data.get('event_timestamp', ''),
            transcript_text.strip(),
            summary,
            call_duration
        ]
        sheet.append_row(row)
        
        print("Successfully wrote to Google Sheets!")
        
    except Exception as e:
        print(f"Error writing to Google Sheets: {e}")
    
    return jsonify({"status": "ok"}), 200
