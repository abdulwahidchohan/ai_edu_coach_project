from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.coordinator import CoordinatorAgent
from agents.content_curator import ContentCuratorAgent
from agents.assessment import AssessmentAgent
from agents.tutoring import TutoringAgent
from agents.progress import ProgressTrackingAgent
from agents.doc_processing import DocumentProcessingAgent
from agents.doc_understanding import DocumentUnderstandingAgent

from models.pydantic_models import (
    Student,
    LearningContent,
    Assessment,
    ProgressReport,
    TutoringSession
)

app = FastAPI(
    title="AI Education Coach",
    description="An intelligent tutoring system that provides personalized learning assistance",
    version="1.0.0"
)

# Initialize agents
coordinator = CoordinatorAgent()
content_curator = ContentCuratorAgent()
assessment_agent = AssessmentAgent()
tutoring_agent = TutoringAgent()
progress_agent = ProgressTrackingAgent()
doc_processor = DocumentProcessingAgent()
doc_understanding = DocumentUnderstandingAgent()

# API Models
class TutoringRequest(BaseModel):
    student_id: str
    subject: str
    topic: str

class QuestionRequest(BaseModel):
    session_id: str
    question: str

class ContentRequest(BaseModel):
    student_id: str
    subject: str
    count: Optional[int] = 5

class AssessmentRequest(BaseModel):
    student_id: str
    content_id: str
    submission: str

@app.post("/tutoring/start", response_model=TutoringSession)
async def start_tutoring_session(request: TutoringRequest):
    """Start a new tutoring session for a student."""
    try:
        # Get student profile (in real implementation, this would come from a database)
        student = Student(id=request.student_id, name="Test Student")
        
        # Initialize tutoring session
        session = await coordinator.start_tutoring_session(
            student=student,
            subject=request.subject,
            topic=request.topic
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tutoring/question")
async def process_question(request: QuestionRequest):
    """Process a student's question during a tutoring session."""
    try:
        response = await coordinator.process_student_question(
            session_id=request.session_id,
            question=request.question
        )
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/content/recommend", response_model=List[LearningContent])
async def recommend_content(request: ContentRequest):
    """Get personalized content recommendations for a student."""
    try:
        # Get student profile (in real implementation, this would come from a database)
        student = Student(id=request.student_id, name="Test Student")
        
        recommendations = await content_curator.recommend_content(
            student=student,
            subject=request.subject,
            count=request.count
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assessment/submit", response_model=Assessment)
async def submit_assessment(request: AssessmentRequest):
    """Submit and process a student's assessment."""
    try:
        # Get student and content (in real implementation, these would come from a database)
        student = Student(id=request.student_id, name="Test Student")
        content = LearningContent(
            id=request.content_id,
            title="Test Content",
            subject="Test Subject",
            difficulty_level=1,
            content_type="quiz",
            content=""
        )
        
        # Process submission through document processor
        analysis = await doc_processor.process_student_submission(
            submission=request.submission,
            assignment_context={"content_id": content.id}
        )
        
        # Create assessment record
        assessment = await assessment_agent.create_assessment(
            student=student,
            content=content,
            score=analysis['quality_metrics'].get('clarity', 0.0),
            feedback=analysis.get('suggested_improvements', []),
            areas_for_improvement=analysis.get('suggested_improvements', [])
        )
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/progress/{student_id}/{subject}", response_model=ProgressReport)
async def get_progress_report(student_id: str, subject: str):
    """Get a progress report for a student in a specific subject."""
    try:
        # Get student profile (in real implementation, this would come from a database)
        student = Student(id=student_id, name="Test Student")
        
        # Get recent assessments and sessions (in real implementation, these would come from a database)
        assessments = []
        sessions = []
        
        report = await progress_agent.update_progress(
            student=student,
            subject=subject,
            assessments=assessments,
            sessions=sessions
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)