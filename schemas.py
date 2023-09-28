import datetime
from typing import Optional
from pydantic import BaseModel


class FileSchema(BaseModel):
    id: str
    filename: str
    bucketname: str
    filesize: int
    date_created: Optional[datetime.datetime]
    last_updated: Optional[datetime.datetime]
    url: Optional[str]

    class Config:
        json_schema_extra= {
            "example": {
                "filename": "test.jpeg",
                "fileid": "Ki7n2ZD4hyP3FyW3XX",
                "bucketid": "photos",
                "filesize": 2333,
                "url": "http://localhost:8000/files/photos/test.jpeg"
            }
        }
        from_attributes = True