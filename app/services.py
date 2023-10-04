from fastapi import Request
import os
from pprint import pprint
from app.settings import settings

def getUrlFullPath(request: Request, file_id: str):
    hostname = request.headers.get("host")
    request = f"{request.url.scheme}://"
    if hostname == "127.0.0.1:8000":
        hostname = request + hostname
    else:
        hostname = f"https://{hostname}"  

    return f"{hostname}/files/{file_id}"




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