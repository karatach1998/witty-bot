import requests
from flask import Flask, Response, request, send_from_directory

import config
from tasks import handle_webhook


def enable_webhook_mode():
    base_url = config.APP_BASE_URL
    token = config.TELEGRAM_BOT_TOKEN
    webhook_url = f'{base_url}/{token}'
    r = requests.get(
        f'https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}'
    )
    print(r.json())


app = Flask(__name__)


@app.route('/media/<path:filename>', methods=['GET', 'POST'])
def media(filename):
    if request.method == 'POST':
        file = request.files['file']
        file.save(config.MEDIA_PATH / filename)
        return Response(status=200)
    else:
        return send_from_directory(config.MEDIA_PATH, filename)


@app.route(f'/{config.TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    handle_webhook.delay(request.json)
    return Response(status=200)


enable_webhook_mode()
