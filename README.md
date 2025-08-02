# AI Education Coach Project

An intelligent tutoring system that provides personalized learning assistance through a team of specialized AI agents.

## Features

- **Personalized Tutoring**: Interactive tutoring sessions tailored to your learning style
- **Content Recommendations**: Discover learning materials matched to your current level
- **Skill Development**: Identify skill gaps and get targeted exercise recommendations
- **Progress Tracking**: Monitor your learning journey with detailed progress reports
- **Assessments**: Evaluate your understanding with adaptive assessments

## Architecture

The system is built with a multi-agent architecture where specialized agents handle different aspects of the educational experience:

- **Coordinator Agent**: Orchestrates interactions between specialized agents
- **Tutoring Agent**: Manages interactive learning sessions
- **Content Curator Agent**: Recommends personalized learning content
- **Assessment Agent**: Evaluates student performance
- **Progress Tracking Agent**: Monitors student advancement
- **Document Processing Agent**: Handles educational materials
- **Document Understanding Agent**: Processes and comprehends educational content
- **Skill Development Agent**: Identifies skills and recommends exercises

## Running the Application

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the FastAPI Backend

To run the FastAPI backend server:

```bash
python main.py
```

This will start the server at http://localhost:8000

### Running the Chainlit Interface

To run the Chainlit chat interface:

```bash
chainlit run chainlit_app.py
```

This will start the Chainlit app at http://localhost:8000

## API Documentation

When running the FastAPI backend, you can access the API documentation at:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Demo Mode

The application currently runs in demo mode with sample data. In a production environment, it would connect to a database for persistent storage of student profiles, learning content, and progress data.

## License

This project is licensed under the MIT License - see the LICENSE file for details.