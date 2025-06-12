from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class Student(BaseModel):
    id: str
    name: str
    grade_level: Optional[int] = None
    subjects: List[str] = []
    learning_style: Optional[str] = None
    progress: Dict[str, float] = {}

class LearningContent(BaseModel):
    id: str
    title: str
    subject: str
    difficulty_level: int
    content_type: str  # video, text, quiz, etc.
    content: str
    metadata: Dict[str, str] = {}

class Assessment(BaseModel):
    id: str
    student_id: str
    content_id: str
    score: float
    completed_at: datetime
    feedback: str
    areas_for_improvement: List[str] = []

class ProgressReport(BaseModel):
    student_id: str
    subject: str
    current_level: float
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    generated_at: datetime

class TutoringSession(BaseModel):
    id: str
    student_id: str
    subject: str
    topic: str
    start_time: datetime
    end_time: Optional[datetime] = None
    questions_asked: List[str] = []
    concepts_covered: List[str] = []
    session_summary: Optional[str] = None