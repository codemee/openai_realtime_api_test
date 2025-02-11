from openai import OpenAI
from flask import Flask, render_template
import time

app = Flask(__name__)
client = OpenAI()

def get_ephemeral_key():
    response = client.beta.realtime.sessions.create(
        model='gpt-4o-realtime-preview'
    )
    print(f'Expires at: {time.ctime(response.client_secret.expires_at)}')
    return response.client_secret.value

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/key')
def key():
    return get_ephemeral_key()

if __name__ == '__main__':
    app.run("0.0.0.0", 5000)
