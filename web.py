from flask import Flask, Response, request, send_from_directory

from bot import config, enable_webhook_mode
from tasks import handle_webhook

app = Flask(__name__)


@app.route(f'{config.MEDIA_URL}/<path:filename>', methods=['GET', 'POST'])
def media(filename):
    if request.method == 'POST':
        file = request.files['file']
        file.save(config.MEDIA_PATH / filename)
        return Response(status=200)
    else:
        return send_from_directory(config.MEDIA_PATH, filename)


if __name__ == '__main__':
    app.run('localhost', 8080)
else:

    @app.route(f'/{config.TELEGRAM_BOT_TOKEN}', methods=['POST'])
    def webhook():
        handle_webhook.delay(request.json)
        return Response(status=200)

    enable_webhook_mode()
