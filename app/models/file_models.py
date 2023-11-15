"""
This module contains all the models used in the application

TODO: Add more model to handle image and other models as needed
"""
import datetime
from uuid import uuid4
from sqlalchemy.schema import Column
from sqlalchemy.types import String, DateTime, Integer, Boolean, TEXT, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Session
from db import Base


############################ File and Bucket Models ###############################################################

class Bucket(Base):
    __tablename__ = "bucket"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    owner = Column(String(255), ForeignKey("users.id"), index=True, )
    name = Column(String(255), index=True) # nucket name is same as owner's username
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    files = relationship("Files", back_populates="bucket", lazy="joined")

class Files(Base):
    __tablename__ = "files"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    owner_id = Column(String(255), ForeignKey("users.id"), index=True, )
    filename = Column(String(255), index=True)
    bucket_id = Column(String(255), ForeignKey("bucket.id"), index=True,)
    file_format = Column(String(5))
    blob_count = Column(Integer)
    compressed_filesize = Column(Integer)
    thumbnail_name = Column(String(255))
    thumbnail_url = Column(String(255))
    play_back_url = Column(String(255))
    download_url = Column(String(255))
    state = Column(Enum("pending", "processing", "completed", "failed", name="state"), default="pending")
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    bucket = relationship("Bucket", back_populates="files", lazy="joined")
    blob = relationship("Blob", back_populates="file", lazy="joined")
    transcribe = relationship("Transcribe", back_populates="file", lazy="joined") 
    merge_tracking = relationship("merge_tracking", back_populates="file",)


class Blob(Base):
    __tablename__ = "blob"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    file_id = Column(String(255), ForeignKey("files.id"), index=True)
    position = Column(Integer)
    name = Column(String(255), index=True)
    path = Column(String(255), index=True)
    size = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    file = relationship("Files", back_populates="blob",)
    merge_tracking = relationship("merge_tracking", back_populates="blob", lazy="joined")
#############################################################################################################

############################################# Transcribe Models #############################################

class Transcribe(Base):
    __tablename__ = "transcribe"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    file_id = Column(String(255), ForeignKey("files.id"), index=True)
    transcribe = Column(TEXT)
    is_completed = Column(Boolean, default=False)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    file = relationship("Files", back_populates="transcribe", lazy="joined")

#############################################################################################################

############################################# Tracking Model #############################################

class merge_tracking(Base):
    __tablename__ = "merge_tracking"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    file_id = Column(String(255), ForeignKey("files.id"), index=True)
    blob_id = Column(String(255), ForeignKey("blob.id"), index=True)
    is_merged = Column(Boolean, default=False)
    error = Column(TEXT)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    file = relationship("Files", back_populates="merge_tracking", )
    blob = relationship("Blob", back_populates="merge_tracking", )

#############################################################################################################


def find_file():
    ...