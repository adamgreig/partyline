import os
import flask
import time

from werkzeug import Headers

from twilio import twiml
from twilio.rest import TwilioRestClient

app = flask.Flask(__name__)
twilio = TwilioRestClient()

@app.route('/')
def index():
    return ""

@app.route('/call')
def call():
    def process():
        yield '<?xml version="1.0" encoding="UTF-8"?><Response>'
        yield '<Say>Welcome to the PARTY LINE. Please wait...</Say>'
        time.sleep(15)
        yield '<Say>Thanks for waiting!</Say></Response>'
    #r = twiml.Response()
    #r.say("Welcome to the PARTY LINE. Get ready to PARTY HARD.")
    #resp = flask.make_response(str(r))
    #resp.headers['Content-Type'] = 'application/xml'
    #return resp
    header = Headers()
    header.add('Content-Type', 'application/xml')
    return flask.Response(process(), headers=header, direct_passthrough=True)

@app.route('/sms')
def sms():
    return ""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
