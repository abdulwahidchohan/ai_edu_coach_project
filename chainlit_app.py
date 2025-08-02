import os
import asyncio
from typing import Dict, List, Optional
import chainlit as cl
from chainlit.types import AskFileResponse
from datetime import datetime

# Import agents
from agents.coordinator import CoordinatorAgent
from agents.content_curator import ContentCuratorAgent
from agents.assessment import AssessmentAgent
from agents.tutoring import TutoringAgent
from agents.progress import ProgressTrackingAgent
from agents.doc_processing import DocumentProcessingAgent
from agents.doc_understanding import DocumentUnderstandingAgent
from agents.skill_dev import SkillDevelopmentAgent

# Import models
from models.pydantic_models import (
    Student,
    LearningContent,
    Assessment,
    ProgressReport,
    TutoringSession
)

# Initialize agents
coordinator = CoordinatorAgent()
content_curator = ContentCuratorAgent()
assessment_agent = AssessmentAgent()
tutoring_agent = TutoringAgent()
progress_agent = ProgressTrackingAgent()
doc_processor = DocumentProcessingAgent()
doc_understanding = DocumentUnderstandingAgent()
skill_dev_agent = SkillDevelopmentAgent()

# Store active sessions
active_sessions: Dict[str, Dict] = {}

@cl.on_chat_start
async def on_chat_start():
    # Welcome message
    await cl.Message(
        content="Welcome to the AI Education Coach! I'm here to help you learn and improve your skills. "
        "What subject would you like to focus on today?",
        author="AI Education Coach"
    ).send()
    
    # Set default student for demo purposes
    # In a real app, this would be based on user authentication
    cl.user_session.set("student", Student(
        id=f"student_{datetime.now().timestamp()}",
        name="Demo Student",
        grade_level=10,
        subjects=["Math", "Science", "Language"],
        learning_style="visual",
        progress={"Math": 0.6, "Science": 0.4, "Language": 0.7}
    ))
    
    # Initialize available actions
    cl.user_session.set("actions", [
        "Start Tutoring Session",
        "Get Content Recommendations",
        "Take Assessment",
        "View Progress Report",
        "Identify Skills",
        "Get Exercise Recommendations"
    ])

@cl.on_message
async def on_message(message: cl.Message):
    # Get student from session
    student = cl.user_session.get("student")
    
    # Check if this is an action selection
    actions = cl.user_session.get("actions")
    if message.content in actions:
        await handle_action(message.content, student)
        return
    
    # Check if we're in an active tutoring session
    active_session = cl.user_session.get("active_session")
    if active_session:
        await handle_tutoring_question(message.content, active_session, student)
        return
    
    # Process general message
    # For simplicity, we'll treat this as a subject selection
    if message.content.lower() in [s.lower() for s in student.subjects]:
        subject = message.content.capitalize()
        await cl.Message(
            content=f"Great! Let's focus on {subject}. What would you like to do?",
            author="AI Education Coach"
        ).send()
        
        # Create action buttons
        actions = cl.user_session.get("actions")
        elements = []
        for action in actions:
            elements.append(
                cl.Button(value=action, label=action)
            )
        await cl.Message(content="Choose an action:", elements=elements).send()
    else:
        # Default response for unrecognized input
        await cl.Message(
            content="I'm not sure how to help with that. Please select one of your subjects: " + 
                    ", ".join(student.subjects),
            author="AI Education Coach"
        ).send()

async def handle_action(action: str, student: Student):
    """Handle user-selected actions"""
    if action == "Start Tutoring Session":
        await start_tutoring_session(student)
    elif action == "Get Content Recommendations":
        await get_content_recommendations(student)
    elif action == "Take Assessment":
        await start_assessment(student)
    elif action == "View Progress Report":
        await view_progress_report(student)
    elif action == "Identify Skills":
        await identify_skills(student)
    elif action == "Get Exercise Recommendations":
        await get_exercise_recommendations(student)

async def start_tutoring_session(student: Student):
    """Start a new tutoring session"""
    # Ask for subject
    await cl.Message(
        content="What subject would you like to focus on for this tutoring session?",
        author="AI Education Coach"
    ).send()
    
    # Create subject buttons
    elements = []
    for subject in student.subjects:
        elements.append(
            cl.Button(value=f"tutoring_{subject}", label=subject)
        )
    await cl.Message(content="Choose a subject:", elements=elements).send()
    
    # Set up callback for subject selection
    @cl.on_message
    async def on_subject_selection(message: cl.Message):
        if message.content.startswith("tutoring_"):
            subject = message.content.split("_")[1]
            await cl.Message(
                content=f"What specific topic in {subject} would you like to focus on?",
                author="AI Education Coach"
            ).send()
            
            # Remove this callback
            cl.remove_listeners()
            
            # Set up callback for topic selection
            @cl.on_message
            async def on_topic_selection(message: cl.Message):
                topic = message.content
                
                # Initialize session
                session = await coordinator.start_tutoring_session(
                    student=student,
                    subject=subject,
                    topic=topic
                )
                
                # Store session
                cl.user_session.set("active_session", session)
                
                await cl.Message(
                    content=f"Great! We're now in a tutoring session for {subject}: {topic}. "
                    f"What questions do you have about this topic?",
                    author="AI Education Coach"
                ).send()
                
                # Remove this callback
                cl.remove_listeners()

async def handle_tutoring_question(question: str, session: TutoringSession, student: Student):
    """Handle a question during a tutoring session"""
    # Process the question
    response = await coordinator.process_student_question(
        session_id=session.id,
        question=question
    )
    
    # In a real implementation, this would return a meaningful response
    # For now, we'll use a placeholder
    if response == "Response placeholder":
        # Use the tutoring agent directly
        response, follow_ups = await tutoring_agent.process_question(
            session_id=session.id,
            question=question
        )
    
    # Send response
    await cl.Message(
        content=response,
        author="AI Education Coach"
    ).send()
    
    # Offer follow-up questions if available
    if follow_ups and len(follow_ups) > 0:
        elements = []
        for follow_up in follow_ups:
            elements.append(
                cl.Button(value=follow_up, label=follow_up)
            )
        await cl.Message(
            content="Here are some follow-up questions you might consider:",
            elements=elements
        ).send()

async def get_content_recommendations(student: Student):
    """Get personalized content recommendations"""
    # Ask for subject
    await cl.Message(
        content="What subject would you like content recommendations for?",
        author="AI Education Coach"
    ).send()
    
    # Create subject buttons
    elements = []
    for subject in student.subjects:
        elements.append(
            cl.Button(value=f"content_{subject}", label=subject)
        )
    await cl.Message(content="Choose a subject:", elements=elements).send()
    
    # Set up callback for subject selection
    @cl.on_message
    async def on_subject_selection(message: cl.Message):
        if message.content.startswith("content_"):
            subject = message.content.split("_")[1]
            
            # Get recommendations
            recommendations = await content_curator.recommend_content(
                student=student,
                subject=subject,
                count=3
            )
            
            # In a real implementation, this would return actual content
            # For now, we'll create some placeholder content
            if not recommendations:
                recommendations = [
                    LearningContent(
                        id=f"{subject}_content_{i}",
                        title=f"{subject} Content {i}",
                        subject=subject,
                        difficulty_level=int(student.progress.get(subject, 0.5) * 10),
                        content_type="text",
                        content=f"This is sample content for {subject}, item {i}"
                    ) for i in range(1, 4)
                ]
            
            # Display recommendations
            await cl.Message(
                content=f"Here are some recommended learning materials for {subject}:",
                author="AI Education Coach"
            ).send()
            
            for rec in recommendations:
                await cl.Message(
                    content=f"**{rec.title}**\n\nDifficulty: {rec.difficulty_level}/10\nType: {rec.content_type}\n\n{rec.content[:100]}...",
                ).send()
            
            # Remove this callback
            cl.remove_listeners()
            
            # Return to main menu
            elements = []
            actions = cl.user_session.get("actions")
            for action in actions:
                elements.append(
                    cl.Button(value=action, label=action)
                )
            await cl.Message(content="What would you like to do next?", elements=elements).send()

async def start_assessment(student: Student):
    """Start an assessment"""
    await cl.Message(
        content="Assessment functionality is not fully implemented in this demo. "
        "In a complete implementation, this would provide interactive assessments "
        "based on the student's current level and learning history.",
        author="AI Education Coach"
    ).send()
    
    # Return to main menu
    elements = []
    actions = cl.user_session.get("actions")
    for action in actions:
        elements.append(
            cl.Button(value=action, label=action)
        )
    await cl.Message(content="What would you like to do instead?", elements=elements).send()

async def view_progress_report(student: Student):
    """View a progress report"""
    # Ask for subject
    await cl.Message(
        content="For which subject would you like to see your progress?",
        author="AI Education Coach"
    ).send()
    
    # Create subject buttons
    elements = []
    for subject in student.subjects:
        elements.append(
            cl.Button(value=f"progress_{subject}", label=subject)
        )
    await cl.Message(content="Choose a subject:", elements=elements).send()
    
    # Set up callback for subject selection
    @cl.on_message
    async def on_subject_selection(message: cl.Message):
        if message.content.startswith("progress_"):
            subject = message.content.split("_")[1]
            
            # Get progress report
            report = await progress_agent.update_progress(
                student=student,
                subject=subject,
                assessments=[],  # In a real app, these would be fetched from a database
                sessions=[]
            )
            
            # Display report
            await cl.Message(
                content=f"# Progress Report for {subject}\n\n"
                f"Current Level: {report.current_level * 100:.1f}%\n\n"
                f"**Strengths:**\n" + ("\n".join([f"- {s}" for s in report.strengths]) if report.strengths else "None identified yet") + "\n\n"
                f"**Areas for Improvement:**\n" + ("\n".join([f"- {w}" for w in report.weaknesses]) if report.weaknesses else "None identified yet") + "\n\n"
                f"**Recommendations:**\n" + ("\n".join([f"- {r}" for r in report.recommendations]) if report.recommendations else "Continue current learning path"),
                author="AI Education Coach"
            ).send()
            
            # Remove this callback
            cl.remove_listeners()
            
            # Return to main menu
            elements = []
            actions = cl.user_session.get("actions")
            for action in actions:
                elements.append(
                    cl.Button(value=action, label=action)
                )
            await cl.Message(content="What would you like to do next?", elements=elements).send()

async def identify_skills(student: Student):
    """Identify skills and skill gaps"""
    # Ask for subject
    await cl.Message(
        content="For which subject would you like to identify your skills and skill gaps?",
        author="AI Education Coach"
    ).send()
    
    # Create subject buttons
    elements = []
    for subject in student.subjects:
        elements.append(
            cl.Button(value=f"skills_{subject}", label=subject)
        )
    await cl.Message(content="Choose a subject:", elements=elements).send()
    
    # Set up callback for subject selection
    @cl.on_message
    async def on_subject_selection(message: cl.Message):
        if message.content.startswith("skills_"):
            subject = message.content.split("_")[1]
            
            # Identify skills
            skills = await skill_dev_agent.identify_skills(
                student=student,
                subject=subject
            )
            
            # Display skills
            await cl.Message(
                content=f"# Skill Analysis for {subject}\n\n"
                f"Based on your current progress level of {student.progress.get(subject, 0) * 100:.1f}%, "
                f"here's an analysis of your skills in {subject}:",
                author="AI Education Coach"
            ).send()
            
            # Group skills by category
            skills_by_category = {}
            for skill in skills:
                category = skill.get("category", "General")
                if category not in skills_by_category:
                    skills_by_category[category] = []
                skills_by_category[category].append(skill)
            
            for category, category_skills in skills_by_category.items():
                skill_list = ""
                for skill in category_skills:
                    gap_level = skill.get("gap_level", 0)
                    gap_description = "Strong" if gap_level < 0.3 else "Moderate" if gap_level < 0.6 else "Significant Gap"
                    skill_list += f"- **{skill['name']}**: {gap_description} (Gap Level: {gap_level:.1f})\n"
                
                await cl.Message(
                    content=f"## {category} Skills\n\n{skill_list}",
                ).send()
            
            # Remove this callback
            cl.remove_listeners()
            
            # Offer to recommend exercises
            elements = [
                cl.Button(value=f"exercises_{subject}", label=f"Get Exercise Recommendations for {subject}")
            ]
            await cl.Message(
                content="Would you like personalized exercise recommendations to improve these skills?",
                elements=elements
            ).send()

async def get_exercise_recommendations(student: Student):
    """Get exercise recommendations"""
    # Check if this is coming from skill identification
    message_content = cl.user_session.get("last_message_content", "")
    if message_content.startswith("exercises_"):
        subject = message_content.split("_")[1]
        await recommend_exercises_for_subject(student, subject)
        return
    
    # Ask for subject
    await cl.Message(
        content="For which subject would you like exercise recommendations?",
        author="AI Education Coach"
    ).send()
    
    # Create subject buttons
    elements = []
    for subject in student.subjects:
        elements.append(
            cl.Button(value=f"exercises_{subject}", label=subject)
        )
    await cl.Message(content="Choose a subject:", elements=elements).send()
    
    # Set up callback for subject selection
    @cl.on_message
    async def on_subject_selection(message: cl.Message):
        if message.content.startswith("exercises_"):
            subject = message.content.split("_")[1]
            await recommend_exercises_for_subject(student, subject)
            
            # Remove this callback
            cl.remove_listeners()

async def recommend_exercises_for_subject(student: Student, subject: str):
    """Recommend exercises for a specific subject"""
    # Get exercise recommendations
    exercises = await skill_dev_agent.recommend_exercises(
        student=student,
        subject=subject,
        count=3
    )
    
    # Display exercises
    await cl.Message(
        content=f"# Recommended Exercises for {subject}\n\n"
        f"Here are personalized exercises to help you improve your skills in {subject}:",
        author="AI Education Coach"
    ).send()
    
    for i, exercise in enumerate(exercises):
        await cl.Message(
            content=f"## Exercise {i+1}: {exercise['skill_name']}\n\n"
            f"**Difficulty:** {exercise['difficulty'] * 10:.1f}/10\n"
            f"**Estimated Time:** {exercise['estimated_time_minutes']} minutes\n"
            f"**Type:** {exercise['exercise_type']}\n\n"
            f"**Description:**\n{exercise['description']}\n\n"
            f"**Resources:**\n" + ("\n".join([f"- {r}" for r in exercise['resources']]) if exercise['resources'] else "No additional resources provided"),
        ).send()
    
    # Return to main menu
    elements = []
    actions = cl.user_session.get("actions")
    for action in actions:
        elements.append(
            cl.Button(value=action, label=action)
        )
    await cl.Message(content="What would you like to do next?", elements=elements).send()

if __name__ == "__main__":
    # This allows running the Chainlit app directly
    # Use: python chainlit_app.py
    pass