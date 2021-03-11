import os
from pathlib import Path


# Resources directory tree:
# resources/
#   books/
#     book_title.json
#   math/
#     subject1/
#       problems/
#         task1.txt  # List of LaTeX formulas.
#       book.json
#   russian.json  # russian.xml

APP_NAME = "witty-bot"

if os.getenv("DYNO"):
    APP_URL = f"https://{APP_NAME}.herokuapp.com"
else:
    APP_URL = "http://localhost:8080"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_PATH = Path(PROJECT_DIR, "resources")
MATH_PROBLEMS_PATH = RESOURCES_PATH / "math"
BOOKS_PATH = RESOURCES_PATH / "books"
MEDIA_PATH = Path("/tmp")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_AUTH_CLIENT_SECRETS = os.getenv("GOOGLE_AUTH_CLIENT_SECRETS")
YANDEX_DISK_TOKEN = os.getenv("YANDEX_DISK_TOKEN")
WOLFRAMALPHA_APP_ID = os.getenv("WOLFRAMALPHA_APP_ID")
