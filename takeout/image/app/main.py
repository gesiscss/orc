from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/usertakeout/{user_id}")
async def user_data_takeout(user_id: str):
    return FileResponse(f'databackup/{user_id}')