import datetime
from uuid import uuid4
from sqlalchemy.schema import Column
from sqlalchemy.types import String, DateTime, Integer, Boolean, TEXT
import sqlalchemy.orm as orm
from db import Base



class Files(Base):
    __tablename__ = "files"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    filename = Column(String(255), index=True)
    bucketname = Column(String(255), index=True)
    filesize = Column(Integer)
    url = Column(String(255))
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class Chunk_tracker(Base):
    __tablename__ = "chunk_tracker"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    file_id = Column(String(255), index=True)   
    chunk_number = Column(Integer) # chunk number
    chunk_size = Column(Integer) # chunk size
    chunk_name = Column(String(255)) # chunk name
    is_completed = Column(Boolean, default=False)
    is_last_chunk = Column(Boolean, default=False)

class Transcribe(Base):
    __tablename__ = "transcribe"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    file_id = Column(String(255), index=True)
    transcribe = Column(TEXT)
    is_completed = Column(Boolean, default=False)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)


class Progress(Base):
    __tablename__ = "progress"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    file_id = Column(String(255), index=True)
    progress = Column(Integer, default=0) # for each chunk that has been added to the file, the progress is incremented by 1
    is_completed = Column(Boolean, default=False)



def find_file(bucket: str, filename: str, db: orm.Session):
    return db.query(Files).filter((Files.bucketname == bucket) & (Files.filename == filename)).first()