import datetime
from uuid import uuid4
from sqlalchemy.schema import Column
from sqlalchemy.types import String, DateTime, Integer, Boolean, TEXT, Enum
import sqlalchemy.orm as orm
from db import Base


class Files(Base):
    __tablename__ = "files"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    filename = Column(String(255), index=True)
    bucket_name = Column(String(255), index=True)
    filesize = Column(Integer)
    compressed_filesize = Column(Integer)
    thumbnail_name = Column(String(255))
    thumbnail_url = Column(TEXT)
    play_back_url = Column(TEXT)
    download_url = Column(TEXT)
    status = Column(Enum("processing", "completed", "failed", name="status"), default="processing")
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class Transcribe(Base):
    __tablename__ = "transcribe"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    file_id = Column(String(255), index=True)
    transcribe = Column(TEXT)
    is_completed = Column(Boolean, default=False)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)




def find_file(bucket: str, filename: str, db: orm.Session):
    return db.query(Files).filter((Files.bucket_name == bucket) & (Files.filename == filename)).first()