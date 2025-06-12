from typing import Dict, List, Any, Optional, Union, Tuple
import re
import json
import os
import aiohttp
from datetime import datetime

class CustomTools:
    """A collection of custom tools and utilities for the AI Education Coach."""
    
    def __init__(self):
        """Initialize the custom tools."""
        self.cache_dir = os.path.join(os.getcwd(), "data", "cache")
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    async def extract_key_concepts(self, text: str) -> List[str]:
        """Extract key educational concepts from a text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of key concepts found in the text
        """
        # Simple implementation using regex patterns for common concept indicators
        # In a production system, this would use NLP or ML techniques
        
        # Look for phrases that often indicate key concepts
        concept_patterns = [
            r"key concept[s]?:?\s*([^.\n]+)[.\n]",
            r"important:?\s*([^.\n]+)[.\n]",
            r"remember:?\s*([^.\n]+)[.\n]",
            r"definition:?\s*([^.\n]+)[.\n]",
            r"is defined as:?\s*([^.\n]+)[.\n]",
            r"([^.\n]+)\s+is a term used to describe",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|are|refers to)"
        ]
        
        concepts = []
        for pattern in concept_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            concepts.extend([match.strip() for match in matches if match.strip()])
        
        # Remove duplicates while preserving order
        unique_concepts = []
        for concept in concepts:
            if concept not in unique_concepts:
                unique_concepts.append(concept)
        
        return unique_concepts
    
    async def generate_quiz_questions(self, content: str, num_questions: int = 5, 
                                     difficulty: str = "medium") -> List[Dict[str, Any]]:
        """Generate quiz questions based on educational content.
        
        Args:
            content: The educational content to base questions on
            num_questions: Number of questions to generate
            difficulty: Difficulty level ("easy", "medium", "hard")
            
        Returns:
            List of quiz questions with answers
        """
        # In a production system, this would use an LLM or specialized model
        # Here we'll implement a template-based approach for demonstration
        
        # Extract key concepts to focus questions on
        concepts = await self.extract_key_concepts(content)
        
        # If no concepts were found, use a simple fallback approach
        if not concepts:
            # Split content into sentences and use those as basis for questions
            sentences = re.split(r'(?<=[.!?])\s+', content)
            sentences = [s for s in sentences if len(s.split()) > 5]  # Only use substantial sentences
            
            # Use up to 5 sentences as the basis for questions
            concepts = sentences[:min(5, len(sentences))]
        
        questions = []
        for i in range(min(num_questions, len(concepts))):
            concept = concepts[i]
            
            # Create a question based on the concept
            if difficulty == "easy":
                question_text = f"What is {concept}?"
                options = ["Correct definition", "Incorrect option 1", "Incorrect option 2", "Incorrect option 3"]
            elif difficulty == "medium":
                question_text = f"Explain the significance of {concept} in this context."
                options = ["Correct explanation", "Partially correct", "Incorrect option 1", "Incorrect option 2"]
            else:  # hard
                question_text = f"Analyze how {concept} relates to other key concepts in this material."
                options = ["Correct analysis", "Partially correct 1", "Partially correct 2", "Incorrect option"]
            
            questions.append({
                "id": f"q{i+1}",
                "question": question_text,
                "options": options,
                "correct_answer": 0,  # Index of correct option
                "difficulty": difficulty,
                "concept": concept
            })
        
        return questions
    
    async def simplify_text(self, text: str, grade_level: str = "middle") -> str:
        """Simplify text to make it more accessible for different grade levels.
        
        Args:
            text: The text to simplify
            grade_level: Target grade level ("elementary", "middle", "high")
            
        Returns:
            Simplified version of the text
        """
        # In a production system, this would use an LLM or specialized model
        # Here we'll implement a simple rule-based approach
        
        if grade_level == "elementary":
            # For elementary level, simplify vocabulary and shorten sentences
            # Replace complex words with simpler alternatives
            replacements = {
                r"\butilize\b": "use",
                r"\bfacilitate\b": "help",
                r"\bsubsequently\b": "then",
                r"\bnevertheless\b": "but",
                r"\bconsequently\b": "so",
                r"\binitiate\b": "start",
                r"\bterminate\b": "end",
                r"\bprocure\b": "get",
                r"\bcomprehend\b": "understand",
                r"\bsufficient\b": "enough"
            }
            
            for complex_word, simple_word in replacements.items():
                text = re.sub(complex_word, simple_word, text, flags=re.IGNORECASE)
            
            # Break long sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            simplified_sentences = []
            
            for sentence in sentences:
                if len(sentence.split()) > 15:  # If sentence is too long
                    # Try to break at conjunctions
                    parts = re.split(r'(,\s+(?:and|but|or|because|so)\s+)', sentence)
                    reconstructed = []
                    
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):
                            reconstructed.append(parts[i] + parts[i+1])
                        else:
                            reconstructed.append(parts[i])
                    
                    simplified_sentences.extend(reconstructed)
                else:
                    simplified_sentences.append(sentence)
            
            return " ".join(simplified_sentences)
            
        elif grade_level == "middle":
            # For middle school, moderate simplification
            replacements = {
                r"\butilize\b": "use",
                r"\bfacilitate\b": "help",
                r"\bsubsequently\b": "then",
                r"\bnevertheless\b": "however"
            }
            
            for complex_word, simple_word in replacements.items():
                text = re.sub(complex_word, simple_word, text, flags=re.IGNORECASE)
            
            return text
            
        else:  # high school or default
            # For high school, minimal simplification
            return text
    
    async def format_as_flashcards(self, content: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """Convert educational content into flashcard format.
        
        Args:
            content: The educational content to convert
            num_cards: Maximum number of flashcards to create
            
        Returns:
            List of flashcards with front and back content
        """
        # Extract key concepts and definitions
        concepts = await self.extract_key_concepts(content)
        
        # Look for definition patterns in the text
        definition_patterns = [
            r"([^.\n:]+)\s+is defined as\s+([^.\n]+)[.\n]",
            r"([^.\n:]+)\s+refers to\s+([^.\n]+)[.\n]",
            r"([^.\n:]+)\s+means\s+([^.\n]+)[.\n]",
            r"definition of ([^.\n:]+)\s+is\s+([^.\n]+)[.\n]",
            r"([^.\n:]+):\s+([^.\n]+)[.\n]"
        ]
        
        flashcards = []
        
        # Extract term-definition pairs using patterns
        for pattern in definition_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for term, definition in matches:
                if len(flashcards) >= num_cards:
                    break
                    
                flashcards.append({
                    "front": term.strip(),
                    "back": definition.strip()
                })
        
        # If we don't have enough flashcards yet, use the concepts
        if len(flashcards) < num_cards and concepts:
            for concept in concepts:
                if len(flashcards) >= num_cards:
                    break
                    
                # Check if this concept is already used as a term
                if not any(card["front"].lower() == concept.lower() for card in flashcards):
                    # Search for sentences containing this concept
                    concept_pattern = re.escape(concept)
                    sentences = re.findall(f"[^.\n]*{concept_pattern}[^.\n]*[.\n]", content, re.IGNORECASE)
                    
                    if sentences:
                        flashcards.append({
                            "front": concept.strip(),
                            "back": sentences[0].strip()
                        })
        
        return flashcards
    
    async def generate_study_guide(self, content: str, format_type: str = "outline") -> str:
        """Generate a study guide from educational content.
        
        Args:
            content: The educational content to process
            format_type: The format of the study guide ("outline", "summary", "notes")
            
        Returns:
            Formatted study guide as a string
        """
        # Extract key concepts
        concepts = await self.extract_key_concepts(content)
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        if format_type == "outline":
            # Create an outline format
            study_guide = "# Study Guide\n\n"
            
            # Add main concepts section
            study_guide += "## Key Concepts\n\n"
            for i, concept in enumerate(concepts):
                study_guide += f"{i+1}. {concept}\n"
            
            study_guide += "\n## Content Outline\n\n"
            
            # Process paragraphs to create outline sections
            current_section = None
            for paragraph in paragraphs:
                # Check if paragraph looks like a heading
                if len(paragraph.strip()) < 100 and not paragraph.endswith('.'):
                    current_section = paragraph.strip()
                    study_guide += f"### {current_section}\n\n"
                elif current_section and paragraph.strip():
                    # Add bullet points for content under the current section
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    for sentence in sentences[:3]:  # Limit to first 3 sentences per paragraph
                        if sentence.strip():
                            study_guide += f"- {sentence.strip()}\n"
                    study_guide += "\n"
            
        elif format_type == "summary":
            # Create a summary format
            study_guide = "# Study Guide Summary\n\n"
            
            # Add concepts as a quick reference
            study_guide += "## Quick Reference\n\n"
            for concept in concepts:
                study_guide += f"- {concept}\n"
            
            study_guide += "\n## Summary\n\n"
            
            # Include a condensed version of each paragraph
            for paragraph in paragraphs:
                if len(paragraph.strip()) > 0:
                    # Take first sentence of each paragraph for the summary
                    first_sentence = re.split(r'(?<=[.!?])\s+', paragraph.strip())[0]
                    if first_sentence:
                        study_guide += f"{first_sentence}\n\n"
            
        else:  # "notes" format
            # Create a detailed notes format
            study_guide = "# Study Notes\n\n"
            
            # Add concepts section
            study_guide += "## Important Concepts to Remember\n\n"
            for concept in concepts:
                study_guide += f"- **{concept}**\n"
            
            study_guide += "\n## Detailed Notes\n\n"
            
            # Include more detailed notes from the content
            for paragraph in paragraphs:
                if len(paragraph.strip()) > 0:
                    # Look for potential section headings
                    if len(paragraph.strip()) < 100 and not paragraph.endswith('.'):
                        study_guide += f"### {paragraph.strip()}\n\n"
                    else:
                        # Process regular content paragraphs
                        study_guide += f"{paragraph.strip()}\n\n"
                        
                        # Highlight any key concepts that appear in this paragraph
                        for concept in concepts:
                            if concept.lower() in paragraph.lower():
                                study_guide += f"**Note:** Pay attention to *{concept}* in this section.\n"
                        study_guide += "\n"
        
        return study_guide
    
    async def analyze_learning_style(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze student responses to determine preferred learning style.
        
        Args:
            responses: List of student responses to learning style assessment
            
        Returns:
            Analysis of learning style preferences
        """
        # This is a simplified implementation of learning style analysis
        # In a production system, this would use more sophisticated models
        
        # Initialize counters for different learning styles
        styles = {
            "visual": 0,
            "auditory": 0,
            "reading_writing": 0,
            "kinesthetic": 0
        }
        
        # Process each response
        for response in responses:
            question_type = response.get("question_type", "")
            answer = response.get("answer", "")
            
            # Increment counters based on response patterns
            if question_type == "preference" and isinstance(answer, str):
                lower_answer = answer.lower()
                
                if any(term in lower_answer for term in ["see", "visual", "image", "picture", "diagram"]):
                    styles["visual"] += 1
                    
                if any(term in lower_answer for term in ["hear", "listen", "audio", "sound", "talk"]):
                    styles["auditory"] += 1
                    
                if any(term in lower_answer for term in ["read", "write", "text", "note", "book"]):
                    styles["reading_writing"] += 1
                    
                if any(term in lower_answer for term in ["do", "practice", "hands-on", "experience", "activity"]):
                    styles["kinesthetic"] += 1
            
            elif question_type == "rating" and isinstance(answer, (int, float)):
                category = response.get("category", "")
                if category in styles and 1 <= answer <= 5:  # Assuming 1-5 rating scale
                    styles[category] += answer / 5  # Normalize to 0-1 range
        
        # Determine primary and secondary learning styles
        sorted_styles = sorted(styles.items(), key=lambda x: x[1], reverse=True)
        primary_style = sorted_styles[0][0]
        secondary_style = sorted_styles[1][0] if sorted_styles[1][1] > 0 else None
        
        # Calculate percentages
        total = sum(styles.values())
        percentages = {style: (count / total * 100 if total > 0 else 0) for style, count in styles.items()}
        
        # Generate recommendations based on learning style
        recommendations = self._generate_learning_recommendations(primary_style, secondary_style)
        
        return {
            "primary_style": primary_style,
            "secondary_style": secondary_style,
            "style_breakdown": percentages,
            "recommendations": recommendations
        }
    
    def _generate_learning_recommendations(self, primary_style: str, 
                                          secondary_style: Optional[str] = None) -> Dict[str, List[str]]:
        """Generate learning recommendations based on learning style.
        
        Args:
            primary_style: The primary learning style
            secondary_style: The secondary learning style, if any
            
        Returns:
            Dictionary of recommendations by category
        """
        recommendations = {
            "study_techniques": [],
            "content_formats": [],
            "tools": []
        }
        
        # Recommendations for visual learners
        if primary_style == "visual" or secondary_style == "visual":
            recommendations["study_techniques"].extend([
                "Use mind maps and concept diagrams",
                "Color-code your notes",
                "Convert text information into charts and graphs"
            ])
            recommendations["content_formats"].extend([
                "Video tutorials",
                "Infographics",
                "Illustrated guides"
            ])
            recommendations["tools"].extend([
                "Mind mapping software",
                "Video learning platforms",
                "Visual note-taking apps"
            ])
        
        # Recommendations for auditory learners
        if primary_style == "auditory" or secondary_style == "auditory":
            recommendations["study_techniques"].extend([
                "Record and listen to lectures",
                "Participate in group discussions",
                "Read material aloud to yourself"
            ])
            recommendations["content_formats"].extend([
                "Podcasts",
                "Audio books",
                "Recorded lectures"
            ])
            recommendations["tools"].extend([
                "Voice recording apps",
                "Text-to-speech software",
                "Podcast platforms"
            ])
        
        # Recommendations for reading/writing learners
        if primary_style == "reading_writing" or secondary_style == "reading_writing":
            recommendations["study_techniques"].extend([
                "Take detailed notes",
                "Rewrite key concepts in your own words",
                "Create summaries and outlines"
            ])
            recommendations["content_formats"].extend([
                "Textbooks",
                "Articles",
                "Written guides"
            ])
            recommendations["tools"].extend([
                "Note-taking apps",
                "Digital flashcards",
                "E-readers"
            ])
        
        # Recommendations for kinesthetic learners
        if primary_style == "kinesthetic" or secondary_style == "kinesthetic":
            recommendations["study_techniques"].extend([
                "Use hands-on experiments",
                "Take breaks and move around while studying",
                "Create physical models or demonstrations"
            ])
            recommendations["content_formats"].extend([
                "Interactive simulations",
                "Lab exercises",
                "Project-based tutorials"
            ])
            recommendations["tools"].extend([
                "Educational games",
                "Virtual labs",
                "DIY project kits"
            ])
        
        return recommendations