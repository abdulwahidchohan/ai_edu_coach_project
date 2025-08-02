from typing import List, Dict, Optional
from datetime import datetime

from models.pydantic_models import Student, LearningContent

class ContentCuratorAgent:
    def __init__(self):
        self.content_database: Dict[str, LearningContent] = {}

    async def add_content(
        self,
        content: LearningContent
    ) -> LearningContent:
        """Add new learning content to the database."""
        self.content_database[content.id] = content
        return content

    async def get_content(
        self,
        content_id: str
    ) -> Optional[LearningContent]:
        """Retrieve specific learning content by ID."""
        return self.content_database.get(content_id)

    async def recommend_content(
        self,
        student: Student,
        subject: str,
        count: int = 5
    ) -> List[LearningContent]:
        """Recommend personalized learning content based on student profile."""
        # Filter content by subject
        subject_content = [
            content for content in self.content_database.values()
            if content.subject == subject
        ]

        # Sort by relevance to student's current level
        student_level = student.progress.get(subject, 0.0)
        recommended = sorted(
            subject_content,
            key=lambda x: abs(x.difficulty_level - student_level)
        )

        return recommended[:count]

    async def generate_study_plan(
        self,
        student: Student,
        subject: str,
        duration_days: int
    ) -> List[Dict]:
        """Generate a structured study plan with recommended content."""
        recommended = await self.recommend_content(student, subject, count=duration_days * 2)
        
        study_plan = []
        for day in range(duration_days):
            if day * 2 + 1 >= len(recommended):
                break
                
            daily_plan = {
                'day': day + 1,
                'main_content': recommended[day * 2],
                'practice_content': recommended[day * 2 + 1],
                'estimated_duration': '2 hours'
            }
            study_plan.append(daily_plan)
            
        return study_plan

    async def search_content(
        self,
        query: str,
        filters: Dict = None
    ) -> List[LearningContent]:
        """Search for learning content based on query and filters."""
        filters = filters or {}
        results = []

        for content in self.content_database.values():
            # Basic text matching - in production this would use proper search indexing
            if query.lower() in content.title.lower() or query.lower() in content.content.lower():
                matches_filters = True
                
                # Apply any additional filters
                for key, value in filters.items():
                    if hasattr(content, key) and getattr(content, key) != value:
                        matches_filters = False
                        break
                
                if matches_filters:
                    results.append(content)

        return results