from pydantic import BaseModel

class StudentCreate(BaseModel):
    name: str
    email: str

class PerformanceCreate(BaseModel):
    student_id: int
    topic: str
    score: float
    total: float