import requests
import uuid

# Unique ID per bot instance
BOT_ID = uuid.uuid4()

# Shared session for the library
session = requests.Session()
session.headers.update({
    "User-Agent": f"GenreLinkingBot/1.0 (id={BOT_ID})"
})
