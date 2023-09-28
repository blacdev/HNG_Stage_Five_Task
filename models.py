import datetime
from uuid import uuid4
from sqlalchemy.schema import Column
from sqlalchemy.types import String, DateTime, Integer
import sqlalchemy.orm as orm
from db import Base



class Files(Base):
    __tablename__ = "files"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    filename = Column(String(255), index=True)
    bucketname = Column(String(255), index=True)
    filesize = Column(Integer, index=True)
    url = Column(String(255))
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)


def find_file(bucket: str, filename: str, db: orm.Session):
    return db.query(Files).filter((Files.bucketname == bucket) & (Files.filename == filename)).first()