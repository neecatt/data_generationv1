from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    slug = Column(String)
    postCount = Column(Integer)
    # Establish the relationship (one Category to many Posts)
    posts = relationship("Post", back_populates="category")

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    likeCount = Column(Integer)
    commentCount = Column(Integer)
    publishedAt = Column(String)
    isApproval = Column(Boolean)
    # Define a foreign key that references the Category table
    category_id = Column(Integer, ForeignKey('categories.id'))
    # Establish the relationship (many Posts to one Category)
    category = relationship("Category", back_populates="posts")


class ApprovalModel(BaseModel):
    isApproval: bool

class Message(BaseModel):
    message: str

class NotFoundMessage(BaseModel):
    detail: str