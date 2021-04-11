import requests

from . import config


def disable_webhook_mode():
    token = config.TELEGRAM_BOT_TOKEN
    r = requests.get(f'https://api.telegram.org/bot{token}/setWebhook')
    print(r.json())


def enable_webhook_mode():
    base_url = config.APP_BASE_URL
    token = config.TELEGRAM_BOT_TOKEN
    webhook_url = f'{base_url}/{token}'
    r = requests.get(
        f'https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}'
    )
    print(r.json())
