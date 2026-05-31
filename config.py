import os

TOKEN = os.getenv("TOKEN") or os.environ.get("TOKEN")
PREFIX = "!"

if not TOKEN:
    raise ValueError("TOKEN manquant !")