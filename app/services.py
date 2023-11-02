from fastapi import Request
import os
from pprint import pprint
from typing import Union
from app.settings import settings

def get_url_full_path(request: Request, file_type: Union[str, None] = None) -> str:
    hostname = request.headers.get("host")
    print("hostname", hostname)

    path = request.url.path
    print("path", path)
    request = f"{request.url.scheme}://"
    print("request", request)

    if file_type == "video":
        return f"{request}{hostname}{path}/download"


    elif file_type == "thumbnail":
        return f"{request}{hostname}{path}/thumbnail"

    elif file_type == "playback":
        return f"{request}{hostname}{path}/playback"


def append_to_file(file_path: str, file_name: str, bytes: bytes):
    with open(os.path.join(file_path, file_name), "ab") as f:
        f.write(bytes)



def create_empty_file(file_name: str, bucket_name: str):
    # create folder with bucket name
    if not os.path.exists(os.path.join(settings.FILES_BASE_FOLDER, bucket_name)):
        os.mkdir(os.path.join(settings.FILES_BASE_FOLDER, bucket_name))
    try:

        # create empty file
        with open(file_name, "wb") as f:
            f.write(b"")
        return True
    except Exception as e:
        print(e)
        return False

async def video_streamer(file_path: str):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1000000)
            if not chunk:
                break
            yield chunk