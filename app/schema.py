from pydantic import BaseModel

class BriefRequest(BaseModel):
    query: str
    thread_id: str
    user_id: str

class BriefResponse(BaseModel):
    result: str
    
    