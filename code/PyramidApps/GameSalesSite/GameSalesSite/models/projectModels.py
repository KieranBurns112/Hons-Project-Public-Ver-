from sqlalchemy import Column, Integer, Text
from .meta import Base

class Listings(Base):
    __tablename__ = 'listings'
    id = Column(Integer, primary_key=True)
    game = Column(Text)
    platform = Column(Text)
    price = Column(Text)
    seller = Column(Text)

class Users(Base):
    __tablename__ = 'users'
    username = Column(Text, primary_key=True)
    password = Column(Text)
