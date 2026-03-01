from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record
import os

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE       = os.environ["TWILIO_PHONE"]
YOUR_PHONE         = os.environ["YOUR_PHONE"]

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
    response.say("Hi! Tell me about your day. I'm listening.")
    response.record(
        max_length=300,          # 5 minutes max
        action="/recording-done",
        transcribe=False
    )
    return str(response)

@app.route("/recording-done", methods=["POST"])
def recording_done():
    """Twilio calls this when recording finishes."""
    recording_url = request.form.get("RecordingUrl")
    print(f"Recording saved at: {recording_url}")
    # Optional: trigger Google Drive upload here
    response = VoiceResponse()
    response.say("Thanks! Have a great evening.")
    response.hangup()
    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
