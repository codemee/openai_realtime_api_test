from openai import OpenAI
from flask import Flask, render_template
import time

app = Flask(__name__)
client = OpenAI()

def get_ephemeral_key():
    # 生成臨時金鑰
    response = client.beta.realtime.sessions.create(
        model='gpt-4o-realtime-preview'
    )
    # 把時效時間顯示在瀏覽器的終端機上
    print(f'Expires at: {time.ctime(response.client_secret.expires_at)}')
    # 傳回臨時金鑰
    return response.client_secret.value

# 顯示首頁
@app.route('/')
def index():
    return render_template('index.html')

# 取得臨時金鑰的路徑
@app.route('/key')
def key():
    return get_ephemeral_key()

if __name__ == '__main__':
    app.run("0.0.0.0", 5000)
