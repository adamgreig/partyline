import os
import sys
import flask
import redis
import pymongo
import urlparse

from twilio import twiml
from twilio.rest import TwilioRestClient

def config(var):
    try:
        return os.environ[var]
    except KeyError:
        print "Could not find {0} in env, quitting.".format(var)
        sys.exit(1)

def setup_mongo():
    uri = config('MONGOHQ_URI')
    dbname = urlparse.urlparse(uri).path[1:]
    con = pymongo.Connection(uri)
    db = con[dbname]
    return db

def setup_redis():
    uri = urlparse.urlparse(config('REDIS_URI'))
    return redis.StrictRedis(host=uri.hostname, port=uri.port, db=0,
            password=uri.password)

r = setup_redis()
db = setup_mongo()
app = flask.Flask(__name__)
twilio_client = TwilioRestClient()

def check_conferences_active():
    return (
        len(twilio_client.conferences.list(
            friendly_name="selocpartyline", status="in-progress")) +
        len(twilio_client.conferences.list(
            friendly_name="selocpartyline", status="init"))) > 0

def conference_running():
    return r.get('conference_running')

def call_others(initiator):
    twilio_client.calls.create(
        to=config('TWILIO_TROLL_NUMBER'),
        from_=config('TWILIO_FROM_NUMBER'),
        url=None, application_sid=config('TWILIO_APP'))

@app.route('/')
def index():
    return ""

@app.route('/call')
def call():
    r = twiml.Response()
    r.say("Welcome to the PARTY LINE.")
    if r.get('conference_running'):
        r.say("Connecting you to the party. Get ready to PARTY HARD.")
    else:
        r.set('conference_running', True)
        call_others(flask.request.args['From'])
        r.say("Phoning the rest of the party. Please wait.")
    with r.dial() as d:
        d.conference("selocpartyline", muted=False, beep=True,
                startConferenceOnEnter=True, endConferenceOnExit=False)
    resp = flask.make_response(str(r))
    resp.headers['Content-Type'] = 'application/xml'
    return resp

@app.route('/sms')
def sms():
    return ""

@app.route('/hangup')
def hangup():
    if not check_conferences_active():
        r.set('conference_running', False)
    return "OK"

if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        app.debug = True
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
