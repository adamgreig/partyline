import os
import flask

from twilio import twiml
from twilio.rest import TwilioRestClient

app = flask.Flask(__name__)
twilio_client = TwilioRestClient()

def conference_running():
    return (
        len(twilio_client.conferences.list(
            FriendlyName="selocpartyline", status="in-progress")) +
        len(twilio_client.conferences.list(
            FriendlyName="selocpartyline", status="init"))) > 0

def call_others(initiator):
    twilio_client.calls.create(
        to=os.environ['TWILIO_TROLL_NUMBER'],
        from_=os.environ['TWILIO_FROM_NUMBER'],
        url=None, application_sid="AP92a26b662590492fa99225404e5cb0c7")

@app.route('/')
def index():
    return ""

@app.route('/call')
def call():
    r = twiml.Response()
    r.say("Welcome to the PARTY LINE.")
    if not conference_running():
        call_others(flask.request.args['From'])
        r.say("Phoning the rest of the party. Please wait.")
    else:
        r.say("Connecting you to the party. Get ready to PARTY HARD.")

    with r.dial() as d:
        d.conference("selocpartyline", muted=False, beep=True,
                startConferenceOnEnter=True, endConferenceOnExit=False)
    resp = flask.make_response(str(r))
    resp.headers['Content-Type'] = 'application/xml'
    return resp

@app.route('/sms')
def sms():
    return ""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    if os.environ.get('DEBUG', False):
        app.debug = True
    app.run(host='0.0.0.0', port=port)
