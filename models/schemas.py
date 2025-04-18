from pydantic import BaseModel
from typing import Optional, List

class Userinfo(BaseModel):
    name: str
    userId: str

class UserMessage(BaseModel):
    userMessage: str
    userId: str

class ChatResponse(BaseModel):
    responseText: str

class BookRecommendation(BaseModel):
    bookTitle: str
    bookReason: str
    imageUrl: str
    bookUrl: str

class BookRecommendationList(BaseModel):
    recommendations: List[BookRecommendation]

class UserName(BaseModel):
    name: str