import os
import flask

from twilio import twiml
from twilio.rest import TwilioRestClient

app = flask.Flask(__name__)
twilio_client = TwilioRestClient()

def conference_running():
    return len(twilio_client.conferences.list()) > 0

def call_others(initiator):
    twilio_client.calls.create(to="+442033223875", from_="+442033221789",
        url=None, application_sid="AP92a26b662590492fa99225404e5cb0c7")

@app.route('/')
def index():
    return ""

@app.route('/call')
def call():
    if not conference_running():
        #call_others(flask.request.args['From'])
        call_others("TEST")
    r = twiml.Response()
    r.say("Welcome to the PARTY LINE. Get ready to PARTY HARD.")
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
    app.run(host='0.0.0.0', port=port)
