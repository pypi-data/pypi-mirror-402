# gui/video_server.py

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import os

app = FastAPI()


@app.get("/video")
async def get_video(path: str = Query(...)):
    real_path = path
    print("PATH FROM FASTAPI:", repr(real_path))

    if not os.path.isfile(real_path):
        return {"error": "File not found"}, 404

    return FileResponse(
        real_path,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
        },
    )
