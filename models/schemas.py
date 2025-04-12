from pydantic import BaseModel
from typing import Optional

class Query(BaseModel):
    question: str
    region: Optional[str] = None  # 지역 정보 (선택)
    
class Userinfo(BaseModel):
    name: str
    idNum: int

class UserMessage(BaseModel):
    userMessage: str
    idNum: int
    