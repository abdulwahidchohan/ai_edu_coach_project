from typing import List, Dict, Optional
from datetime import datetime

from ..models.pydantic_models import Student, Assessment, LearningContent

class AssessmentAgent:
    def __init__(self):
        self.assessments: Dict[str, Assessment] = {}

    async def create_assessment(
        self,
        student: Student,
        content: LearningContent,
        score: float,
        feedback: str,
        areas_for_improvement: List[str]
    ) -> Assessment:
        """Create a new assessment record for a student."""
        assessment = Assessment(
            id=f"assessment_{datetime.now().timestamp()}",
            student_id=student.id,
            content_id=content.id,
            score=score,
            completed_at=datetime.now(),
            feedback=feedback,
            areas_for_improvement=areas_for_improvement
        )
        self.assessments[assessment.id] = assessment
        return assessment

    async def get_student_assessments(
        self,
        student_id: str,
        subject: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Assessment]:
        """Retrieve assessments for a specific student with optional filters."""
        results = []
        for assessment in self.assessments.values():
            if assessment.student_id != student_id:
                continue

            if subject and assessment.content_id.split('_')[0] != subject:
                continue

            if start_date and assessment.completed_at < start_date:
                continue

            if end_date and assessment.completed_at > end_date:
                continue

            results.append(assessment)

        return sorted(results, key=lambda x: x.completed_at, reverse=True)

    async def analyze_performance(
        self,
        student: Student,
        subject: Optional[str] = None
    ) -> Dict:
        """Analyze student's performance across assessments."""
        assessments = await self.get_student_assessments(student.id, subject)
        
        if not assessments:
            return {
                'average_score': 0.0,
                'trend': 'No assessments found',
                'common_improvement_areas': [],
                'strengths': [],
                'total_assessments': 0
            }

        # Calculate metrics
        scores = [a.score for a in assessments]
        improvement_areas = [area for a in assessments for area in a.areas_for_improvement]
        
        # Analyze score trend
        trend = 'stable'
        if len(scores) > 1:
            if scores[0] > scores[-1]:
                trend = 'improving'
            elif scores[0] < scores[-1]:
                trend = 'declining'

        # Identify common areas for improvement
        area_counts = {}
        for area in improvement_areas:
            area_counts[area] = area_counts.get(area, 0) + 1

        common_areas = sorted(
            area_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return {
            'average_score': sum(scores) / len(scores),
            'trend': trend,
            'common_improvement_areas': [area for area, _ in common_areas],
            'strengths': self._identify_strengths(assessments),
            'total_assessments': len(assessments)
        }

    def _identify_strengths(
        self,
        assessments: List[Assessment]
    ) -> List[str]:
        """Identify student's strengths based on high-scoring assessments."""
        high_scoring = [a for a in assessments if a.score >= 0.8]
        
        # In a real implementation, this would analyze the content
        # and feedback of high-scoring assessments to identify
        # specific topics or skills where the student excels
        return [f"High performance in assessment {a.id}" for a in high_scoring[:3]]