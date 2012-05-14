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
                url=None, application_sid=config('TWILIO_APP'),
                if_machine='Continue')

@flask_app.route('/')
def index():
    return "THE PARTY LINE. For party members only."

def make_response(resp):
    response=flask.make_response(str(resp))
    response.headers['Content-Type'] = 'application/xml'
    return response

@flask_app.route('/call')
def call():
    response = twiml.Response()
    response.say("Welcome to the PARTY LINE.")

    if flask.request.args.get('Direction', None) == "outbound-api":
        number = flask.request.args.get('To', None)
    else:
        number = flask.request.args.get('From', None)
    print "Incoming call from {0}".format(number)

    party_member = mongo_client.party_members.find_one({'number': number})

    if not party_member:
        print "Not allowed from {0}".format(number)
        response.say("Sorry, only authorised party members may join the party,"
                     "goodbye.")
        return make_response(response)

    party_starter = redis_client.get('conference_starter')

    if flask.request.args.get('AnsweredBy', None) == "machine":
        response.say(
            "Sorry {0}, {1} started a party but you missed it!".format(
                party_member['name'], party_starter))
        return make_response(response)

    if redis_client.exists('conference_running'):
        print "Connecting through"
        response.say("Hi {0}, {1} has started a party! Connecting you through,"
                     "get ready to PARTY HARD.".format(party_member['name'],
                                                       party_starter))
    else:
        print "Setting up"
        redis_client.set('conference_running', True)
        redis_client.set('conference_starter', party_member['name'])
        call_others(number)
        response.say("Hi {0}, now phoning the rest of the party, "
                     "prepare to PARTY HARD.".format(party_member['name']))
    with response.dial() as dial:
        dial.conference("selocpartyline", muted=False, beep=True,
                startConferenceOnEnter=True, endConferenceOnExit=False)
    return make_response(response)

def send_text(number, message):
    twilio_client.sms.messages.create(to=number,
        from_=config('TWILIO_FROM_NUMBER'), body=message)

@flask_app.route('/sms')
def sms():
    number = flask.request.args['From']
    message = flask.request.args['Body']
    print "Received SMS from {0}: {1}".format(number, message)
    party_member = mongo_client.party_members.find_one({'number': number})
    if not party_member:
        print "Not a party member, dropping"
        msg = "Sorry, only authorised party members can text the PARTY LINE."
        send_text(number, msg)
        return ""
    if len(message) > 140:
        print "Too long, rejecting"
        msg = "Message too long. Keep it under 140 chars. NO PARTY 4 U"
        send_text(number, msg)
    else:
        print "Forwarding."
        msg = "PARTYMSG FROM {0}: {1}".format(party_member['name'], message)
        for member in mongo_client.party_members.find():
            print "Forwarding to {0} ({1})".format(member['name'],
                member['number'])
            send_text(member['number'], msg)
    return "OK"

def clean_up():
    if not check_conferences_active():
        redis_client.delete('conference_running')
    return "OK"

@flask_app.route('/hangup')
def hangup():
    print "Call completed"
    return clean_up()

@flask_app.route('/cron')
def cron():
    print "Cronjob running"
    return clean_up()

if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        flask_app.debug = True
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)
