from fastapi import FastAPI
from fastapi.responses import FileResponse
import requests
import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(current_dir, "_secret_token.json")) as f:
    data = json.load(f)
app = FastAPI()


@app.get("/usertakeout/{user_id}")
async def user_data_takeout(user_id: str):
    # add a post notification to telegram bot
    payload = {
        "chat_id": data["chat_id"],
        "text": "This is a test from takeout API.",
        "disable_notification": "true",
    }
    requests.post(data["url"], data=json.dumps(payload))
    return FileResponse(f"data6/databackup/{user_id}")
