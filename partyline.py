import os
import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
    return ""

@app.route('/call')
def call():
    resp = "<Response><Say>Welcome to the PARTY LINE.</Say></Response>"
    xml = '<?xml version="1.0" encoding="UTF-8"?>' + resp
    resp = flask.make_response(xml)
    resp.headers['Content-Type'] = 'application/xml'
    return resp

@app.route('/sms')
def sms():
    return ""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
