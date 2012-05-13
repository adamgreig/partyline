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

flask_app = flask.Flask(__name__)
redis_client = setup_redis()
mongo_client = setup_mongo()
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

@flask_app.route('/')
def index():
    return ""

@flask_app.route('/call')
def call():
    response = twiml.Response()
    response.say("Welcome to the PARTY LINE.")
    if redis_client.get('conference_running'):
        response.say("Connecting you to the party. Get ready to PARTY HARD.")
    else:
        redis_client.set('conference_running', True)
        call_others(flask.request.args['From'])
        response.say("Phoning the rest of the party. Please wait.")
    with response.dial() as dial:
        dial.conference("selocpartyline", muted=False, beep=True,
                startConferenceOnEnter=True, endConferenceOnExit=False)
    response = flask.make_response(str(response))
    response.headers['Content-Type'] = 'application/xml'
    return response

@flask_app.route('/sms')
def sms():
    return ""

@flask_app.route('/hangup')
def hangup():
    if not check_conferences_active():
        redis_client.set('conference_running', False)
    return "OK"

if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        flask_app.debug = True
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)
