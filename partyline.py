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
    print "Checking for still-active conference"
    return (
        len(twilio_client.conferences.list(
            friendly_name="selocpartyline", status="in-progress")) +
        len(twilio_client.conferences.list(
            friendly_name="selocpartyline", status="init"))) > 0

def call_others(initiator):
    print "Calling other party members"
    for member in mongo_client.party_members.find():
        print "Considering {0}".format(member['name'])
        if member['number'] != initiator:
            print "Phoning {0}".format(member['number'])
            twilio_client.calls.create(
                to=member['number'], from_=config('TWILIO_FROM_NUMBER'),
                url=None, application_sid=config('TWILIO_APP'))

@flask_app.route('/')
def index():
    return ""

@flask_app.route('/call')
def call():
    response = twiml.Response()
    response.say("Welcome to the PARTY LINE.")
    number = flask.request.args.get('From', None)
    if flask.request.args.get('Direction', None) == "outbound-dial":
        number = flask.request.args.get('To', None)
    print "Incoming call from {0}".format(number)
    if not mongo_client.party_members.find_one({'number': number}):
        print "Not allowed"
        response.say("Sorry, only authorised party members may join the party.")
        response.say("Goodbye.")
    else:
        if redis_client.exists('conference_running'):
            print "Connecting through"
            response.say("Connecting you to the party.")
            response.say("Get ready to PARTY HARD.")
        else:
            print "Setting up"
            redis_client.set('conference_running', True)
            call_others(number)
            response.say("Phoning the rest of the party.")
            response.say("Prepare to PARTY HARD.")
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
    print "Call completed"
    if not check_conferences_active():
        redis_client.delete('conference_running')
    return "OK"

if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        flask_app.debug = True
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)
