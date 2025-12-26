# WaterLink Project Reference

## Project Overview

**Purpose:** Receives post-call webhook data from an ElevenLabs conversational AI agent and writes call transcript/metadata to a Google Sheet for logging and analysis.

**Use Case:** Burns & McDonnell construction projects - a voice AI agent that handles community liaison calls from citizens with questions or concerns about local construction projects. The agent collects caller concerns and promises follow-up within 48 hours via the project website.

**Status:** Active and operational

---

## Architecture

```
Caller → #250 Platform → Twilio → ElevenLabs Agent → (call ends) → Webhook → PythonAnywhere Flask App → Google Sheets
```

**Data Flow:**
1. Caller dials #250 and says "Construction" keyword (or calls 10-digit number from signage)
2. #250 platform routes call to Twilio number connected to ElevenLabs agent
3. ElevenLabs agent handles the conversation
4. When call ends, ElevenLabs sends POST request to webhook with transcript data
5. Flask app processes the webhook and appends data to Google Sheet

---

## Hosting & URLs

| Component | Location |
|-----------|----------|
| **Webhook Endpoint** | https://mobiledave.pythonanywhere.com/webhook |
| **Hosting Platform** | PythonAnywhere (Free Beginner tier) |
| **Flask App Location** | `/home/MobileDave/mysite/flask_app.py` |
| **WSGI Config** | `/var/www/mobiledave_pythonanywhere_com_wsgi.py` |

**Note:** Migrated from Render.com (which cost $20/month after free tier spin-down issues) to PythonAnywhere's free tier in December 2024.

**Maintenance Requirement:** Log into PythonAnywhere and click "Run until 3 months from today" button at least once every 3 months. They'll send email reminder one week before site would be disabled.

---

## GitHub Repository

**Repo:** `mobiledave/waterlink`

**Files in repo:**
- `app.py` - Original Flask application (used for Render deployment)
- `requirements.txt` - Python dependencies
- `Procfile` - Gunicorn configuration (for Render)

**Note:** The PythonAnywhere deployment uses `flask_app.py` directly on PythonAnywhere rather than deploying from GitHub.

---

## Google Cloud Configuration

**Project:** `natural-nimbus-478023-u7`

**Service Account:**
- **Name:** waterlink
- **Email:** `waterlink@natural-nimbus-478023-u7.iam.gserviceaccount.com`
- **Purpose:** Authenticates Flask app to write to Google Sheets

**Credentials:** Service account JSON is stored in the WSGI configuration file as an environment variable (`GOOGLE_APPLICATION_CREDENTIALS_JSON`).

---

## Google Sheets

**Sheet ID:** `15KZHfBebHCWkmajKKONxJdN1zL0Wl2Q9ZVdk_J8f9oo`

**URL:** https://docs.google.com/spreadsheets/d/15KZHfBebHCWkmajKKONxJdN1zL0Wl2Q9ZVdk_J8f9oo/edit

**Sharing:** Sheet must be shared with Editor access to: `waterlink@natural-nimbus-478023-u7.iam.gserviceaccount.com`

**Columns Written:**
1. **Timestamp** - Unix timestamp (seconds since epoch). Note: Displays as raw number; use formula `=A2/86400 + DATE(1970,1,1)` in adjacent column and format as Date time to convert.
2. **Transcript** - Full conversation transcript with role labels (agent/user)
3. **Summary** - AI-generated call summary from ElevenLabs analysis
4. **Call Duration** - Duration in seconds

---

## ElevenLabs Configuration

**Agent ID:** `agent_0001k9sz4v4me5jb289nde9nwp69`

**Agent Identity/Prompt:** Community liaison assistant for Burns & McDonnell construction projects. Handles questions/concerns from local residents about active construction projects.

**Key behaviors:**
- Professional yet warm and empathetic tone
- Collects caller's concern/question
- Offers contact options (return call, email, or check project website)
- Promises project manager review within 48 hours
- Reference website: burnsconstructionproject.com

**Post-Call Webhook:**
- **Webhook Name:** PythonAnywhere-Waterlink
- **URL:** https://mobiledave.pythonanywhere.com/webhook
- **Auth Method:** HMAC
- **Webhook Secret:** `wsec_b12fe99ff08e769415f9d5d9a8fe34802f253a989eae96726721e85f1a10921f`

**Location in ElevenLabs:** Agents Platform → Security tab → Post-call webhook

---

## Code Reference

### flask_app.py (PythonAnywhere)

```python
import os
import json
import hmac
import hashlib
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Verify HMAC signature from ElevenLabs
def verify_signature(payload, signature):
    secret = os.environ.get('WEBHOOK_SECRET', '')
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# Initialize Google Sheets client
def get_sheets_client():
    creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    creds_dict = json.loads(creds_json)
    
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

@app.route("/")
def home():
    return "Hello from PythonAnywhere!"

@app.route("/webhook", methods=["POST"])
def webhook():
    # Verify HMAC signature
    signature = request.headers.get('X-Eleven-Signature', '')
    if signature and not verify_signature(request.data, signature):
        print("Invalid signature")
        return jsonify({"error": "Invalid signature"}), 401
    
    data = request.json
    print("Webhook received:", data)
    
    try:
        # Get Google Sheets client
        print("Authenticating with Google...")
        client = get_sheets_client()
        print("Authentication successful!")
        
        # Open sheet by ID
        sheet_id = '15KZHfBebHCWkmajKKONxJdN1zL0Wl2Q9ZVdk_J8f9oo'
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.sheet1
        
        # Extract data from webhook
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
        print(f"Error writing to Google Sheets: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    return jsonify({"status": "ok"}), 200
```

### WSGI Configuration (excerpt structure)

```python
import sys
import os

# Set environment variables
os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON'] = '''{...service account JSON...}'''
os.environ['WEBHOOK_SECRET'] = 'wsec_b12fe99ff08e769415f9d5d9a8fe34802f253a989eae96726721e85f1a10921f'

# Add project to path
project_home = '/home/MobileDave/mysite'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from flask_app import app as application
```

---

## Dependencies

**Python packages (in requirements.txt):**
```
Flask==2.3.3
gunicorn==21.2.0
gspread==5.12.0
google-auth==2.23.4
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **404 error on Google Sheets** | Sheet not shared with service account. Add `waterlink@natural-nimbus-478023-u7.iam.gserviceaccount.com` as Editor. |
| **405 Method Not Allowed** | ElevenLabs webhook URL missing `/webhook` path. Must be `https://mobiledave.pythonanywhere.com/webhook` |
| **401 Invalid signature** | HMAC secret mismatch. Verify `WEBHOOK_SECRET` in WSGI config matches ElevenLabs webhook secret. |
| **Site disabled** | Haven't logged into PythonAnywhere in 3 months. Log in and click "Run until 3 months from today". |
| **Timestamp not readable** | Unix timestamps display as raw numbers. Add formula column: `=A2/86400 + DATE(1970,1,1)` and format as Date time. |

### Checking Logs

**PythonAnywhere logs:**
- Go to Web tab → click on log file links (Error log, Server log)
- Look for "Webhook received:" entries and any error messages

### Testing the Webhook

1. Make a test call to the ElevenLabs agent
2. Have a brief conversation
3. End the call
4. Wait 30-60 seconds for ElevenLabs to process
5. Check Google Sheet for new row
6. Check PythonAnywhere logs if no row appears

---

## Deferred Enhancements

1. **Timestamp formatting** - Modify flask_app.py to convert Unix timestamp to readable date/time string before writing to sheet (eliminates need for formula column)

2. **Dynamic project variables** - Use ElevenLabs dynamic variables to pass different project website URLs per construction project (`{{project_website_url}}`)

---

## Related Links

- **PythonAnywhere Dashboard:** https://www.pythonanywhere.com/user/MobileDave/
- **GitHub Repo:** https://github.com/mobiledave/waterlink
- **Google Cloud Console:** https://console.cloud.google.com/
- **ElevenLabs:** https://elevenlabs.io/

---

## Version History

| Date | Change |
|------|--------|
| Nov 2024 | Initial build - ElevenLabs agent + Render.com webhook + Google Sheets logging |
| Nov 2024 | Upgraded Render to paid ($7/mo) due to free tier spin-down issues |
| Dec 2024 | Migrated from Render to PythonAnywhere (free tier) - saves $20/month |
| Dec 2024 | Added HMAC authentication for webhook security |
