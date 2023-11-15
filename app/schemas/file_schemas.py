import datetime
from typing import Optional
from pydantic import BaseModel


class FileSchema(BaseModel):
    id: str
    filename: str
    bucket_name: str
    date_created: Optional[datetime.datetime]
    last_updated: Optional[datetime.datetime]
    download_url: Optional[str]
    thumbnail_url: Optional[str]
    play_back_url: Optional[str] = None

    class Config:
        json_schema_extra= {
            "example": {
                "file": "<file>",
                "bucketname": "<bucketname>",
            },

            "response": {
                "id": "<id>",
                "filename": "<filename>",
                "bucketname": "<bucketname>",
                "date_created": "<date_created>",
                "last_updated": "<last_updated>",
                "url": "<url>",
                "play_back_url": "<play_back_url>"

            }

        }
        from_attributes = True


class FileResponseSchema(BaseModel):
    message: str
    data: FileSchema

    class Config:
        json_schema_extra= {
            "example": {
                "message": "<message>",
                "data": {
                    "id": "<id>",
                    "filename": "<filename>",
                    "bucketname": "<bucketname>",
                    "date_created": "<date_created>",
                    "last_updated": "<last_updated>",
                    "url": "<url>",
                    "play_back_url": "<play_back_url>"
                }
            }
        }
        from_attributes = True

class AllFileResponse(BaseModel):
    message: str
    data: list[FileSchema]

