from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..models.pydantic_models import Student, ProgressReport, Assessment, TutoringSession

class ProgressTrackingAgent:
    def __init__(self):
        self.progress_history: Dict[str, List[ProgressReport]] = {}

    async def update_progress(
        self,
        student: Student,
        subject: str,
        assessments: List[Assessment],
        sessions: List[TutoringSession]
    ) -> ProgressReport:
        """Update and analyze student's progress based on recent activities."""
        # Calculate current level based on recent assessments
        recent_scores = [a.score for a in assessments if a.completed_at > 
                        datetime.now() - timedelta(days=30)]
        
        current_level = student.progress.get(subject, 0.0)
        if recent_scores:
            current_level = sum(recent_scores) / len(recent_scores)

        # Analyze strengths and weaknesses
        strengths, weaknesses = self._analyze_performance(assessments, sessions)

        # Generate recommendations
        recommendations = self._generate_recommendations(weaknesses, current_level)

        # Create progress report
        report = ProgressReport(
            student_id=student.id,
            subject=subject,
            current_level=current_level,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            generated_at=datetime.now()
        )

        # Store report in history
        if student.id not in self.progress_history:
            self.progress_history[student.id] = []
        self.progress_history[student.id].append(report)

        return report

    async def get_progress_history(
        self,
        student_id: str,
        subject: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ProgressReport]:
        """Retrieve progress history for a student with optional filters."""
        if student_id not in self.progress_history:
            return []

        reports = self.progress_history[student_id]
        filtered_reports = []

        for report in reports:
            if subject and report.subject != subject:
                continue

            if start_date and report.generated_at < start_date:
                continue

            if end_date and report.generated_at > end_date:
                continue

            filtered_reports.append(report)

        return sorted(filtered_reports, key=lambda x: x.generated_at)

    async def analyze_learning_rate(
        self,
        student: Student,
        subject: str
    ) -> Dict:
        """Analyze student's learning rate and progress patterns."""
        reports = await self.get_progress_history(student.id, subject)
        if len(reports) < 2:
            return {
                'learning_rate': 0.0,
                'consistency': 'insufficient_data',
                'trend': 'insufficient_data'
            }

        # Calculate learning rate (change in level over time)
        first_report = reports[0]
        last_report = reports[-1]
        time_diff = (last_report.generated_at - first_report.generated_at).days
        level_diff = last_report.current_level - first_report.current_level

        if time_diff == 0:
            learning_rate = 0.0
        else:
            learning_rate = level_diff / time_diff

        # Analyze consistency and trend
        levels = [r.current_level for r in reports]
        consistency = self._calculate_consistency(levels)
        trend = self._analyze_trend(levels)

        return {
            'learning_rate': learning_rate,
            'consistency': consistency,
            'trend': trend
        }

    def _analyze_performance(
        self,
        assessments: List[Assessment],
        sessions: List[TutoringSession]
    ) -> Tuple[List[str], List[str]]:
        """Analyze student's performance to identify strengths and weaknesses."""
        strengths = []
        weaknesses = []

        # Analyze assessment performance
        high_scores = [a for a in assessments if a.score >= 0.8]
        low_scores = [a for a in assessments if a.score <= 0.6]

        # Identify common topics in high/low scoring assessments
        if high_scores:
            strengths.append(f"Strong performance in {len(high_scores)} assessments")

        if low_scores:
            weaknesses.append(f"Needs improvement in {len(low_scores)} areas")

        # Analyze tutoring sessions
        if sessions:
            concepts_covered = set()
            for session in sessions:
                concepts_covered.update(session.concepts_covered)

            strengths.append(f"Engaged with {len(concepts_covered)} different concepts")

        return strengths, weaknesses

    def _generate_recommendations(
        self,
        weaknesses: List[str],
        current_level: float
    ) -> List[str]:
        """Generate personalized recommendations based on identified weaknesses."""
        recommendations = []

        for weakness in weaknesses:
            recommendations.append(f"Focus on improving: {weakness}")

        # Add level-appropriate recommendations
        if current_level < 0.4:
            recommendations.append("Review fundamental concepts")
        elif current_level < 0.7:
            recommendations.append("Practice with intermediate exercises")
        else:
            recommendations.append("Challenge yourself with advanced topics")

        return recommendations

    def _calculate_consistency(
        self,
        levels: List[float]
    ) -> str:
        """Calculate learning consistency based on level progression."""
        if len(levels) < 3:
            return "insufficient_data"

        # Calculate variations between consecutive levels
        variations = [abs(levels[i] - levels[i-1]) for i in range(1, len(levels))]
        avg_variation = sum(variations) / len(variations)

        if avg_variation < 0.1:
            return "very_consistent"
        elif avg_variation < 0.2:
            return "consistent"
        else:
            return "variable"

    def _analyze_trend(
        self,
        levels: List[float]
    ) -> str:
        """Analyze the overall trend in learning progress."""
        if len(levels) < 2:
            return "insufficient_data"

        if levels[-1] > levels[0]:
            return "improving"
        elif levels[-1] < levels[0]:
            return "declining"
        else:
            return "stable"