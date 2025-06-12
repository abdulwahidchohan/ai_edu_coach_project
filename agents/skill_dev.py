from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json
import os
import re

from ..models.pydantic_models import Student

class SkillDevelopmentAgent:
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the skill development agent.
        
        Args:
            storage_path: Optional path for storing skill data
        """
        self.storage_path = storage_path or os.path.join(os.getcwd(), "data", "skills")
        self.skill_records: Dict[str, Dict] = {}
        self.skill_taxonomies = {}
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)
        
        # Load skill taxonomies
        self._load_skill_taxonomies()
    
    async def identify_skills(self, student: Student, subject: str, content: Optional[str] = None) -> List[Dict]:
        """Identify current skills and skill gaps for a student in a specific subject.
        
        Args:
            student: The student object
            subject: The subject area
            content: Optional content to analyze for skill identification
            
        Returns:
            List of identified skills with metadata
        """
        student_id = student.id
        
        # Create a unique identifier for this skill assessment
        assessment_id = f"skill_assessment_{student_id}_{subject}_{datetime.now().timestamp()}"
        
        # Analyze student's current progress level
        current_level = student.progress.get(subject, 0.0)
        
        # Define skill tiers based on progress level
        if current_level < 0.3:
            tier = "beginner"
        elif current_level < 0.7:
            tier = "intermediate"
        else:
            tier = "advanced"
        
        # Map skills based on subject and tier
        skills = self._map_skills_for_subject(subject, tier)
        
        # If content is provided, enhance skill identification with content analysis
        if content:
            # Get the relevant skill taxonomy for this subject
            taxonomy = self.skill_taxonomies.get(subject.lower(), {})
            if taxonomy:
                # Look for skill indicators in the content based on the taxonomy
                for skill_category, skill_items in taxonomy.items():
                    for skill_name, skill_info in skill_items.items():
                        # Check for skill keywords and patterns
                        keywords = skill_info.get("keywords", [])
                        patterns = skill_info.get("patterns", [])
                        
                        # Check for direct keyword matches
                        keyword_found = any(keyword.lower() in content.lower() for keyword in keywords)
                        
                        # Check for regex pattern matches
                        pattern_found = False
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                pattern_found = True
                                break
                        
                        if keyword_found or pattern_found:
                            # Check if this skill is already in the list
                            skill_exists = False
                            for skill in skills:
                                if skill["name"].lower() == skill_name.lower():
                                    skill_exists = True
                                    # Update gap level based on content analysis
                                    skill["gap_level"] = min(skill["gap_level"], 0.2)  # Reduce gap if skill is present in content
                                    break
                            
                            # If skill not in list, add it
                            if not skill_exists:
                                skills.append({
                                    "id": f"{subject}_{skill_name.lower().replace(' ', '_')}",
                                    "name": skill_name,
                                    "category": skill_category,
                                    "gap_level": 0.3,  # Default gap level for newly identified skills
                                    "level": skill_info.get("level", tier)
                                })
        
        # Store the assessment
        self.skill_records[assessment_id] = {
            "student_id": student_id,
            "subject": subject,
            "timestamp": datetime.now(),
            "current_level": current_level,
            "tier": tier,
            "skills": skills
        }
        
        return skills
    
    async def recommend_exercises(self, student: Student, subject: str, count: int = 3, content: Optional[str] = None) -> List[Dict]:
        """Recommend skill development exercises for a student.
        
        Args:
            student: The student object
            subject: The subject area
            count: Number of exercises to recommend
            content: Optional content to analyze for more targeted recommendations
            
        Returns:
            List of recommended exercises
        """
        # First identify skills, passing content for enhanced analysis if available
        skills = await self.identify_skills(student, subject, content)
        
        # Filter skills with significant gaps
        skill_gaps = [skill for skill in skills if skill.get("gap_level", 0) > 0.4]
        
        # If no significant gaps, use all skills
        if not skill_gaps:
            skill_gaps = skills
        
        # Sort by gap level (highest first)
        skill_gaps.sort(key=lambda x: x.get("gap_level", 0), reverse=True)
        
        # Take top skills based on count
        target_skills = skill_gaps[:count]
        
        # Get student's learning history if available
        learning_history = self._get_learning_history(student, subject)
        
        # Generate exercises for each skill
        exercises = []
        for skill in target_skills:
            skill_name = skill["name"]
            skill_level = skill.get("level", "beginner")
            skill_category = skill.get("category", "general")
            
            # Get skill info from taxonomy if available
            skill_info = self._get_skill_info(subject, skill_category, skill_name)
            
            # Generate exercise description with enhanced context
            description = self._generate_exercise_description(
                skill_name, 
                skill_level, 
                subject,
                skill_info=skill_info,
                learning_history=learning_history,
                content_context=content
            )
            
            # Calculate difficulty (0.0 to 1.0) with more factors
            difficulty = self._calculate_difficulty(
                gap_level=skill["gap_level"],
                progress_level=student.progress.get(subject, 0),
                skill_level=skill_level,
                previous_attempts=learning_history.get(skill["id"], {}).get("attempts", 0)
            )
            
            # Determine exercise type based on skill and student preferences
            exercise_type = self._determine_exercise_type(skill, student)
            
            # Calculate estimated time based on difficulty and exercise type
            estimated_time = self._calculate_estimated_time(difficulty, exercise_type)
            
            exercises.append({
                "id": f"exercise_{skill['id']}_{len(exercises)}",
                "skill_id": skill["id"],
                "skill_name": skill_name,
                "description": description,
                "difficulty": difficulty,
                "subject": subject,
                "category": skill_category,
                "exercise_type": exercise_type,
                "estimated_time_minutes": estimated_time,
                "resources": self._get_skill_resources(subject, skill_name, skill_level)
            })
        
        return exercises
        
    async def recommend_skill_exercises(self, student: Student, subject: str, skill_id: str) -> List[Dict]:
        """Recommend exercises to develop a specific skill."""
        # Get skill details
        skill_info = self._get_skill_info(subject, skill_id)
        
        if not skill_info:
            return []
        
        # Generate exercises based on skill level and student's progress
        current_level = student.progress.get(subject, 0.0)
        
        exercises = [
            {
                "id": f"exercise_{skill_id}_{i}",
                "title": f"{skill_info['name']} Exercise {i+1}",
                "description": self._generate_exercise_description(skill_info, i, current_level),
                "difficulty": self._calculate_difficulty(current_level, i),
                "estimated_time": 15 + (i * 5)  # minutes
            } for i in range(3)  # Generate 3 exercises of increasing difficulty
        ]
        
        return exercises
    
    async def track_progress(self, student: Student, exercise_id: str, completion_status: float, feedback: Optional[str] = None) -> Dict:
        """Track student progress on skill development exercises.
        
        Args:
            student: The student object
            exercise_id: ID of the completed exercise
            completion_status: Completion level (0.0-1.0)
            feedback: Optional feedback on the exercise
            
        Returns:
            Dictionary with progress tracking results
        """
        # Find the exercise
        exercise = None
        for assessment_id, assessment in self.skill_records.items():
            if assessment["student_id"] == student.id:
                # This is a record for our student
                for skill in assessment["skills"]:
                    # Check if this skill matches our exercise
                    if exercise_id.startswith(f"exercise_{skill['id']}"):
                        # Found the relevant skill
                        exercise = {
                            "id": exercise_id,
                            "skill_id": skill["id"],
                            "skill_name": skill["name"],
                            "subject": assessment["subject"]
                        }
                        break
            
            if exercise:
                break
        
        if not exercise:
            return {"error": "Exercise not found"}
        
        # Create a progress record
        timestamp = datetime.now()
        progress_id = f"progress_{exercise_id}_{timestamp.timestamp()}"
        
        progress_record = {
            "id": progress_id,
            "student_id": student.id,
            "exercise_id": exercise_id,
            "skill_id": exercise["skill_id"],
            "skill_name": exercise["skill_name"],
            "subject": exercise["subject"],
            "timestamp": timestamp,
            "completion_status": completion_status,
            "feedback": feedback
        }
        
        # Store the progress record
        self.progress_records[progress_id] = progress_record
        
        # Update student's overall progress in the subject
        subject = exercise["subject"]
        current_progress = student.progress.get(subject, 0.0)
        
        # Calculate progress impact (completion status weighted by a small factor)
        progress_impact = completion_status * 0.05  # Small incremental impact
        
        # Update progress (capped at 1.0)
        new_progress = min(current_progress + progress_impact, 1.0)
        student.progress[subject] = new_progress
        
        # Update learning history for this skill
        skill_id = exercise["skill_id"]
        self._update_learning_history(student, subject, skill_id, completion_status, feedback)
        
        # Update skill gap based on completion status
        self._update_skill_gap(student, subject, skill_id, completion_status)
        
        return {
            "progress_id": progress_id,
            "student_id": student.id,
            "subject": subject,
            "previous_progress": current_progress,
            "new_progress": new_progress,
            "skill_name": exercise["skill_name"],
            "completion_status": completion_status,
            "timestamp": timestamp.isoformat()
        }
        
    async def track_skill_progress(self, student: Student, skill_id: str, exercise_results: List[Dict]) -> Dict:
        """Track a student's progress in developing a specific skill.
        
        Args:
            student: The student object
            skill_id: ID of the skill
            exercise_results: List of exercise result dictionaries
            
        Returns:
            Dictionary with skill progress tracking results
        """
        # Calculate average score from exercise results
        scores = [result.get("score", 0) for result in exercise_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Determine progress level
        progress_level = min(1.0, avg_score / 100)  # Normalize to 0-1 range
        
        # Create progress record
        progress_record = {
            "student_id": student.id,
            "skill_id": skill_id,
            "timestamp": datetime.now(),
            "exercise_count": len(exercise_results),
            "average_score": avg_score,
            "progress_level": progress_level,
            "completed_exercises": [ex.get("id") for ex in exercise_results]
        }
        
        # Store progress record
        record_id = f"skill_progress_{student.id}_{skill_id}_{datetime.now().timestamp()}"
        self.skill_records[record_id] = progress_record
        
        # Update learning history for this skill
        # Find the subject for this skill
        subject = None
        for assessment_id, assessment in self.skill_records.items():
            if assessment["student_id"] == student.id:
                for skill in assessment["skills"]:
                    if skill["id"] == skill_id:
                        subject = assessment["subject"]
                        break
            if subject:
                break
        
        if subject:
            # Update learning history
            self._update_learning_history(
                student, 
                subject, 
                skill_id, 
                progress_level, 
                f"Completed {len(exercise_results)} exercises with average score {avg_score:.1f}%"
            )
            
            # Update skill gap
            self._update_skill_gap(student, subject, skill_id, progress_level)
        
        return progress_record
    
    async def generate_skill_development_plan(self, student: Student, subject: str) -> Dict:
        """Generate a comprehensive skill development plan for a student."""
        # Identify current skills and gaps
        skills = await self.identify_skills(student, subject)
        
        # Sort skills by priority (gaps first)
        prioritized_skills = sorted(skills, key=lambda s: s.get("gap_level", 0), reverse=True)
        
        # Create development timeline
        timeline = []
        current_week = 1
        
        for skill in prioritized_skills[:5]:  # Focus on top 5 priority skills
            timeline.append({
                "week": current_week,
                "skill_id": skill["id"],
                "skill_name": skill["name"],
                "focus_areas": skill.get("focus_areas", []),
                "target_improvement": 0.2  # Aim for 20% improvement
            })
            current_week += 1
        
        # Create the complete plan
        plan = {
            "student_id": student.id,
            "subject": subject,
            "created_at": datetime.now(),
            "current_level": student.progress.get(subject, 0.0),
            "target_level": min(1.0, student.progress.get(subject, 0.0) + 0.3),  # Aim for 30% overall improvement
            "duration_weeks": current_week - 1,
            "priority_skills": [s["id"] for s in prioritized_skills[:5]],
            "timeline": timeline
        }
        
        return plan
    
    def _map_skills_for_subject(self, subject: str, tier: str) -> List[Dict]:
        """Map relevant skills for a subject based on the student's tier."""
        # This would typically connect to a skill database
        # Simplified implementation with hardcoded skills
        skill_map = {
            "math": {
                "beginner": [
                    {"id": "math_basic_arithmetic", "name": "Basic Arithmetic", "gap_level": 0.2},
                    {"id": "math_fractions", "name": "Fractions", "gap_level": 0.5},
                    {"id": "math_decimals", "name": "Decimals", "gap_level": 0.4}
                ],
                "intermediate": [
                    {"id": "math_algebra", "name": "Algebra", "gap_level": 0.3},
                    {"id": "math_geometry", "name": "Geometry", "gap_level": 0.4},
                    {"id": "math_statistics", "name": "Statistics", "gap_level": 0.6}
                ],
                "advanced": [
                    {"id": "math_calculus", "name": "Calculus", "gap_level": 0.5},
                    {"id": "math_linear_algebra", "name": "Linear Algebra", "gap_level": 0.7},
                    {"id": "math_probability", "name": "Probability Theory", "gap_level": 0.4}
                ]
            },
            "science": {
                "beginner": [
                    {"id": "science_basic_concepts", "name": "Basic Science Concepts", "gap_level": 0.3},
                    {"id": "science_observation", "name": "Scientific Observation", "gap_level": 0.4},
                    {"id": "science_classification", "name": "Classification Skills", "gap_level": 0.5}
                ],
                "intermediate": [
                    {"id": "science_hypothesis", "name": "Hypothesis Formation", "gap_level": 0.4},
                    {"id": "science_experimentation", "name": "Experimentation", "gap_level": 0.5},
                    {"id": "science_data_analysis", "name": "Data Analysis", "gap_level": 0.6}
                ],
                "advanced": [
                    {"id": "science_research", "name": "Research Methods", "gap_level": 0.5},
                    {"id": "science_critical_analysis", "name": "Critical Analysis", "gap_level": 0.6},
                    {"id": "science_scientific_writing", "name": "Scientific Writing", "gap_level": 0.7}
                ]
            }
        }
        
        # Return default skills if subject not found
        return skill_map.get(subject, {}).get(tier, [])
    
    def _get_skill_info(self, subject: str, category: str = None, skill_name: str = None, skill_id: str = None) -> Optional[Dict]:
        """Get detailed information about a specific skill.
        
        Args:
            subject: The subject area
            category: Optional skill category
            skill_name: Optional skill name
            skill_id: Optional skill ID
            
        Returns:
            Dictionary with skill information or None if not found
        """
        # If we have a skill_id, try to find it in our records first
        if skill_id:
            for tier in ["beginner", "intermediate", "advanced"]:
                skills = self._map_skills_for_subject(subject, tier)
                for skill in skills:
                    if skill["id"] == skill_id:
                        return skill
        
        # If we have category and skill_name, try to find it in the taxonomy
        if category and skill_name and subject in self.skill_taxonomies:
            taxonomy = self.skill_taxonomies[subject]
            if category in taxonomy and skill_name in taxonomy[category]:
                return taxonomy[category][skill_name]
        
        # If just skill_name is provided, search across all categories
        if skill_name and subject in self.skill_taxonomies:
            taxonomy = self.skill_taxonomies[subject]
            for category, skills in taxonomy.items():
                if skill_name in skills:
                    return skills[skill_name]
        
        return None
    
    def _generate_exercise_description(self, skill_name: str, skill_level: str, subject: str, 
                                    skill_info: Optional[Dict] = None, 
                                    learning_history: Optional[Dict] = None,
                                    content_context: Optional[str] = None) -> str:
        """Generate a description for a skill development exercise.
        
        Args:
            skill_name: Name of the skill
            skill_level: Level of the skill (beginner, intermediate, advanced)
            subject: Subject area
            skill_info: Additional information about the skill from taxonomy
            learning_history: Student's learning history for this skill
            content_context: Content context for more targeted exercises
            
        Returns:
            Exercise description
        """
        # Base description based on skill level
        if skill_level == "beginner":
            base_desc = f"Practice basic {skill_name} concepts with these introductory exercises."
        elif skill_level == "intermediate":
            base_desc = f"Strengthen your {skill_name} skills with these practice problems."
        else:  # advanced
            base_desc = f"Challenge yourself with these advanced {skill_name} problems to master the skill."
        
        # Enhance description with skill info if available
        if skill_info:
            description_templates = skill_info.get("exercise_templates", [])
            if description_templates:
                # Use a template from the skill info
                import random
                template = random.choice(description_templates)
                base_desc = template.format(skill_name=skill_name, subject=subject)
        
        # Personalize based on learning history if available
        if learning_history and skill_name in str(learning_history):
            attempts = learning_history.get(f"{subject}_{skill_name.lower().replace(' ', '_')}", {}).get("attempts", 0)
            if attempts > 0:
                base_desc += f" You've worked on this skill {attempts} times before."
                
                # Add challenge element for repeated skills
                if attempts > 2:
                    base_desc += " This exercise will challenge you with more advanced concepts."
        
        # Add context-specific elements if content is provided
        if content_context:
            # Extract a relevant snippet from the content (first 100 chars)
            snippet = content_context[:100] + "..." if len(content_context) > 100 else content_context
            base_desc += f" This exercise relates to the content: '{snippet}'"
        
        return base_desc
    
    def _calculate_difficulty(self, gap_level: float, progress_level: float, skill_level: str = "beginner", previous_attempts: int = 0) -> float:
        """Calculate appropriate difficulty level for an exercise.
        
        Args:
            gap_level: The identified skill gap level (0.0-1.0)
            progress_level: Overall student progress in the subject (0.0-1.0)
            skill_level: Skill level category (beginner, intermediate, advanced)
            previous_attempts: Number of previous attempts at exercises for this skill
            
        Returns:
            Calculated difficulty level (0.0-1.0)
        """
        # Base difficulty on gap level (higher gap = higher difficulty)
        base_difficulty = gap_level
        
        # Adjust based on overall progress (higher progress = higher difficulty)
        progress_factor = progress_level * 0.5
        
        # Adjust based on skill level
        level_factors = {
            "beginner": -0.1,
            "intermediate": 0.0,
            "advanced": 0.1
        }
        level_factor = level_factors.get(skill_level.lower(), 0.0)
        
        # Adjust based on previous attempts (more attempts = slightly higher difficulty)
        attempt_factor = min(previous_attempts * 0.05, 0.2)  # Cap at 0.2
        
        # Combine all factors (capped between 0.1 and 1.0)
        difficulty = min(max(base_difficulty + progress_factor + level_factor + attempt_factor, 0.1), 1.0)
        
        return round(difficulty, 2)
        
    def _load_skill_taxonomies(self) -> None:
        """Load skill taxonomies from storage."""
        taxonomy_dir = os.path.join(self.storage_path, "taxonomies")
        
        # Create taxonomies directory if it doesn't exist
        if not os.path.exists(taxonomy_dir):
            os.makedirs(taxonomy_dir, exist_ok=True)
            # Create default taxonomies
            self._create_default_taxonomies(taxonomy_dir)
        
        # Load all taxonomy files
        for filename in os.listdir(taxonomy_dir):
            if filename.endswith(".json"):
                subject = filename.split("_taxonomy.json")[0]
                file_path = os.path.join(taxonomy_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.skill_taxonomies[subject] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading taxonomy {filename}: {str(e)}")
    
    def _get_learning_history(self, student: Student, subject: str) -> Dict:
        """Get a student's learning history for a subject.
        
        Args:
            student: The student object
            subject: The subject area
            
        Returns:
            Dictionary with learning history information
        """
        # Initialize history dictionary if it doesn't exist
        if not hasattr(self, 'learning_histories'):
            self.learning_histories = {}
            
        # Create student history key
        student_key = f"history_{student.id}"
        
        # Initialize student history if it doesn't exist
        if student_key not in self.learning_histories:
            self.learning_histories[student_key] = {}
            
        # Initialize subject history if it doesn't exist
        if subject not in self.learning_histories[student_key]:
            self.learning_histories[student_key][subject] = {}
            
        return self.learning_histories[student_key][subject]
    
    def _update_learning_history(self, student: Student, subject: str, skill_id: str, completion_status: float, feedback: Optional[str] = None) -> None:
        """Update a student's learning history for a skill.
        
        Args:
            student: The student object
            subject: The subject area
            skill_id: The skill ID
            completion_status: Completion level (0.0-1.0)
            feedback: Optional feedback
        """
        history = self._get_learning_history(student, subject)
        
        # Initialize skill history if it doesn't exist
        if skill_id not in history:
            history[skill_id] = {
                "attempts": 0,
                "completions": [],
                "average_completion": 0.0,
                "last_attempt": None
            }
            
        # Update skill history
        skill_history = history[skill_id]
        skill_history["attempts"] += 1
        skill_history["completions"].append(completion_status)
        skill_history["average_completion"] = sum(skill_history["completions"]) / len(skill_history["completions"])
        skill_history["last_attempt"] = datetime.now().isoformat()
        
        if feedback:
            if "feedback" not in skill_history:
                skill_history["feedback"] = []
            skill_history["feedback"].append({
                "timestamp": datetime.now().isoformat(),
                "content": feedback
            })
    
    def _update_skill_gap(self, student: Student, subject: str, skill_id: str, completion_status: float) -> None:
        """Update the gap level for a skill based on completion status.
        
        Args:
            student: The student object
            subject: The subject area
            skill_id: The skill ID
            completion_status: Completion level (0.0-1.0)
        """
        # Find the skill in our records
        for assessment_id, assessment in self.skill_records.items():
            if assessment["student_id"] == student.id and assessment["subject"] == subject:
                for skill in assessment["skills"]:
                    if skill["id"] == skill_id:
                        # Update gap level based on completion status
                        # Higher completion = lower gap
                        current_gap = skill.get("gap_level", 0.5)
                        # Reduce gap by a percentage of completion status
                        reduction = completion_status * 0.2  # 20% of completion status
                        new_gap = max(0.0, current_gap - reduction)
                        skill["gap_level"] = round(new_gap, 2)
                        break
    
    def _determine_exercise_type(self, skill: Dict, student: Student) -> str:
        """Determine the most appropriate exercise type for a skill and student.
        
        Args:
            skill: The skill dictionary
            student: The student object
            
        Returns:
            Exercise type string
        """
        # Default exercise types by skill level
        default_types = {
            "beginner": "multiple_choice",
            "intermediate": "short_answer",
            "advanced": "project"
        }
        
        # Get skill level
        skill_level = skill.get("level", "beginner")
        
        # Get student preferences if available
        preferences = getattr(student, "preferences", {})
        preferred_type = preferences.get("exercise_type", None)
        
        # If student has a preference and it's appropriate for their level, use it
        if preferred_type:
            # Map of appropriate exercise types by level
            level_appropriate = {
                "beginner": ["multiple_choice", "matching", "fill_in_blank"],
                "intermediate": ["short_answer", "multiple_choice", "problem_solving"],
                "advanced": ["project", "essay", "problem_solving", "research"]
            }
            
            # If preference is appropriate for level, use it
            if preferred_type in level_appropriate.get(skill_level, []):
                return preferred_type
        
        # Otherwise use default for level
        return default_types.get(skill_level, "multiple_choice")
    
    def _calculate_estimated_time(self, difficulty: float, exercise_type: str) -> int:
        """Calculate estimated time to complete an exercise.
        
        Args:
            difficulty: Exercise difficulty (0.0-1.0)
            exercise_type: Type of exercise
            
        Returns:
            Estimated time in minutes
        """
        # Base times by exercise type (in minutes)
        base_times = {
            "multiple_choice": 5,
            "matching": 7,
            "fill_in_blank": 8,
            "short_answer": 10,
            "problem_solving": 15,
            "essay": 25,
            "project": 45,
            "research": 30
        }
        
        # Get base time for exercise type
        base_time = base_times.get(exercise_type, 10)
        
        # Adjust based on difficulty (higher difficulty = more time)
        difficulty_factor = 1 + difficulty  # 1.0 to 2.0
        
        # Calculate final time
        estimated_time = int(base_time * difficulty_factor)
        
        return estimated_time
    
    def _get_skill_resources(self, subject: str, skill_name: str, skill_level: str) -> List[Dict]:
        """Get learning resources for a skill.
        
        Args:
            subject: The subject area
            skill_name: Name of the skill
            skill_level: Level of the skill
            
        Returns:
            List of resource dictionaries
        """
        # This would typically connect to a resource database
        # Simplified implementation with example resources
        resources = [
            {
                "title": f"{skill_name} Tutorial",
                "type": "article",
                "difficulty": skill_level,
                "url": f"https://example.com/{subject}/{skill_name.lower().replace(' ', '-')}"
            }
        ]
        
        # Add video resource for intermediate and advanced levels
        if skill_level in ["intermediate", "advanced"]:
            resources.append({
                "title": f"{skill_name} Video Lesson",
                "type": "video",
                "difficulty": skill_level,
                "url": f"https://example.com/videos/{subject}/{skill_name.lower().replace(' ', '-')}"
            })
        
        # Add practice problems for all levels
        resources.append({
            "title": f"{skill_name} Practice Problems",
            "type": "practice",
            "difficulty": skill_level,
            "url": f"https://example.com/practice/{subject}/{skill_name.lower().replace(' ', '-')}"
        })
        
        return resources
    
    def _create_default_taxonomies(self, taxonomy_dir: str) -> None:
        """Create default skill taxonomies if none exist.
        
        Args:
            taxonomy_dir: Directory to store taxonomies
        """
        # Example math taxonomy
        math_taxonomy = {
            "arithmetic": {
                "addition": {
                    "level": "beginner",
                    "description": "Ability to add numbers",
                    "keywords": ["add", "sum", "plus", "addition"],
                    "patterns": [r"\d+\s*\+\s*\d+"]
                },
                "subtraction": {
                    "level": "beginner",
                    "description": "Ability to subtract numbers",
                    "keywords": ["subtract", "minus", "difference", "subtraction"],
                    "patterns": [r"\d+\s*-\s*\d+"]
                },
                "multiplication": {
                    "level": "intermediate",
                    "description": "Ability to multiply numbers",
                    "keywords": ["multiply", "product", "times", "multiplication"],
                    "patterns": [r"\d+\s*\*\s*\d+", r"\d+\s*×\s*\d+"]
                },
                "division": {
                    "level": "intermediate",
                    "description": "Ability to divide numbers",
                    "keywords": ["divide", "quotient", "division"],
                    "patterns": [r"\d+\s*/\s*\d+", r"\d+\s*÷\s*\d+"]
                }
            },
            "algebra": {
                "equations": {
                    "level": "intermediate",
                    "description": "Ability to solve equations",
                    "keywords": ["equation", "solve", "unknown", "variable"],
                    "patterns": [r"[a-z]\s*=\s*\d+", r"solve for [a-z]"]
                },
                "expressions": {
                    "level": "intermediate",
                    "description": "Ability to work with algebraic expressions",
                    "keywords": ["expression", "simplify", "expand", "factor"],
                    "patterns": [r"simplify", r"expand", r"factor"]
                }
            },
            "geometry": {
                "area": {
                    "level": "intermediate",
                    "description": "Ability to calculate area of shapes",
                    "keywords": ["area", "square units", "square feet", "square meters"],
                    "patterns": [r"area of", r"find the area"]
                },
                "perimeter": {
                    "level": "intermediate",
                    "description": "Ability to calculate perimeter of shapes",
                    "keywords": ["perimeter", "circumference", "distance around"],
                    "patterns": [r"perimeter of", r"find the perimeter"]
                }
            }
        }
        
        # Example language taxonomy
        language_taxonomy = {
            "reading": {
                "comprehension": {
                    "level": "intermediate",
                    "description": "Ability to understand and interpret text",
                    "keywords": ["comprehend", "understand", "interpret", "meaning"],
                    "patterns": [r"what does .+ mean", r"main idea"]
                },
                "vocabulary": {
                    "level": "intermediate",
                    "description": "Knowledge and use of words",
                    "keywords": ["vocabulary", "word meaning", "definition", "synonym"],
                    "patterns": [r"define the word", r"meaning of"]
                }
            },
            "writing": {
                "grammar": {
                    "level": "intermediate",
                    "description": "Correct use of grammar rules",
                    "keywords": ["grammar", "sentence structure", "syntax", "punctuation"],
                    "patterns": [r"correct grammar", r"proper sentence"]
                },
                "composition": {
                    "level": "advanced",
                    "description": "Ability to compose coherent text",
                    "keywords": ["compose", "write", "essay", "paragraph", "composition"],
                    "patterns": [r"write an essay", r"compose a paragraph"]
                }
            }
        }
        
        # Example science taxonomy
        science_taxonomy = {
            "scientific_method": {
                "hypothesis": {
                    "level": "intermediate",
                    "description": "Ability to formulate testable hypotheses",
                    "keywords": ["hypothesis", "predict", "if-then", "testable"],
                    "patterns": [r"form a hypothesis", r"if .+ then"]
                },
                "experimentation": {
                    "level": "intermediate",
                    "description": "Ability to design and conduct experiments",
                    "keywords": ["experiment", "test", "variable", "control"],
                    "patterns": [r"design an experiment", r"control group"]
                }
            },
            "biology": {
                "cells": {
                    "level": "intermediate",
                    "description": "Understanding of cell structure and function",
                    "keywords": ["cell", "organelle", "membrane", "nucleus"],
                    "patterns": [r"cell structure", r"function of .+ in a cell"]
                },
                "ecosystems": {
                    "level": "intermediate",
                    "description": "Understanding of ecosystem dynamics",
                    "keywords": ["ecosystem", "food web", "habitat", "species"],
                    "patterns": [r"food chain", r"ecosystem balance"]
                }
            }
        }
        
        # Save default taxonomies
        taxonomies = {
            "math": math_taxonomy,
            "language": language_taxonomy,
            "science": science_taxonomy
        }
        
        for subject, taxonomy in taxonomies.items():
            file_path = os.path.join(taxonomy_dir, f"{subject}_taxonomy.json")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(taxonomy, f, ensure_ascii=False, indent=2)
            except IOError as e:
                print(f"Error creating default taxonomy for {subject}: {str(e)}")