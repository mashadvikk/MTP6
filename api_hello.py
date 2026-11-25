from datetime import datetime

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Первое приложение на FastAPI")


@app.get("/")
async def hello():
    return {"hello": "FastAPI"}


@app.get("/time")
async def current_time():
    return {"time": datetime.now().strftime("%H:%M:%S")}


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
