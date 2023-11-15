import datetime
from uuid import uuid4
from sqlalchemy.schema import Column
from sqlalchemy.types import String, DateTime, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Session
from db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone_number = Column(String(255))
    address = Column(String(255))
    username = Column(String(255), unique=True)
    email = Column(String(255), index=True, unique=True)
    password_hash = Column(String(255))
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    auth = relationship("Auth", backref="user", lazy="joined")
    def create_auth(self, session: Session, auth_type: str = "local"):
        new_auth = Auth(user_id=self.id, type=auth_type)
        session.add(new_auth)
        session.commit()


class Auth(Base):
    __tablename__ = "auth"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    user_id = Column(String(255), ForeignKey("users.id"), index=True, )
    type = Column(Enum("local", "google", name="type"), default="local")
    date_created = Column(DateTime, default=datetime.datetime.utcnow)

class Sessions(Base):
    __tablename__ = "sessions"
    id = Column(String(255), primary_key=True, index=True, default=uuid4().hex)
    user_id = Column(String(255), ForeignKey("users.id"), index=True)
    token = Column(String(255), index=True)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)