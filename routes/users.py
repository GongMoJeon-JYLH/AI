from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from models.deepseek_model import handle_conversation
from models.schemas import Userinfo, UserName
from uuid import uuid4

router = APIRouter()

users = {}

@router.post("/users", tags=["유저 ID 생성"], response_model=Userinfo)
def createUser(userName: UserName):
    userId = str(uuid4())
    users[userName.name] = userId
    return {"name": userName.name, "userId": userId}
