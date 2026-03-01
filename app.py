from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import os, json, requests, io
from datetime import datetime

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE       = os.environ["TWILIO_PHONE"]
YOUR_PHONE         = os.environ["YOUR_PHONE"]
DRIVE_FOLDER_ID    = os.environ["DRIVE_FOLDER_ID"]   # ID of your Google Drive folder
GOOGLE_CREDS_JSON  = os.environ["GOOGLE_CREDS_JSON"] # full service account JSON as a string

def get_drive_service():
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build("drive", "v3", credentials=creds)

def upload_to_drive(mp3_bytes, filename):
    service = get_drive_service()
    file_metadata = {
        "name": filename,
        "parents": [DRIVE_FOLDER_ID]
    }
    media = MediaIoBaseUpload(io.BytesIO(mp3_bytes), mimetype="audio/mpeg")
    service.files().create(body=file_metadata, media_body=media).execute()

@app.route("/call", methods=["POST"])
def make_call():
    """cron-job.org hits this to trigger the daily call."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.calls.create(
        to=YOUR_PHONE,
        from_=TWILIO_PHONE,
        url=request.url_root + "voice"
    )
    return "Call initiated", 200

@app.route("/voice", methods=["POST"])
def voice():
    """Twilio calls this when the call connects to get instructions."""
    response = VoiceResponse()
    response.say(
        "Hi Lukas! How was your day? Please cover: what did you do today, what went well, and what went badly.",
        voice="Polly.Matthew"
    )
    response.record(
        max_length=300,
        action="/recording-done",
        transcribe=False
    )
    return str(response)

@app.route("/recording-done", methods=["POST"])
def recording_done():
    """Twilio calls this when recording finishes — downloads and saves to Drive."""
    recording_url = request.form.get("RecordingUrl") + ".mp3"

    # Download the recording from Twilio
    mp3_response = requests.get(recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    # Upload to Google Drive with a dated filename
    filename = f"robo_diary_{datetime.now().strftime('%Y-%m-%d')}.mp3"
    upload_to_drive(mp3_response.content, filename)
    print(f"Uploaded {filename} to Google Drive")

    response = VoiceResponse()
    response.say("Thanks! Have a great evening.", voice="Polly.Matthew")
    response.hangup()
    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
