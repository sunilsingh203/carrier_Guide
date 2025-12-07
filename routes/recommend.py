from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime
from crewai import Task, Crew, Process, Agent
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

recommend_bp = Blueprint('recommend', __name__)

# Initialize Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# Configure the Gemini model
genai.configure(api_key=GOOGLE_API_KEY)

# Set the model name (change to Gemini Flash 2.5)
# If your provider expects a different identifier, replace with that string
# Correct Gemini Flash 2.5 identifier
# Common provider format: "gemini/<model-id>" — update if your environment uses a different form
MODEL_NAME = "gemini/gemini-2.5-flash"

def initialize_agents():
    try:
        # Initialize agents with the model name directly
        profile_analyzer = Agent(
            role='Profile Analyzer',
            goal='Analyze user profile to understand skills, interests, and personality',
            backstory="""You are an expert at analyzing user profiles to understand their 
            core competencies, interests, and personality traits. You help identify 
            key strengths and preferences that are crucial for career matching.""",
            verbose=True,
            llm=MODEL_NAME
        )

        career_matcher = Agent(
            role='Career Matcher',
            goal='Match user profile to suitable career paths',
            backstory="""You are a career matching expert who takes analyzed user profiles 
            and maps them to the most suitable career paths based on their skills, 
            interests, and market demand.""",
            verbose=True,
            llm=MODEL_NAME
        )

        roadmap_creator = Agent(
            role='Career Roadmap Creator',
            goal='Create detailed learning roadmaps for recommended careers',
            backstory="""You are an expert in career development and education planning. 
            You create actionable learning paths and skill development plans for 
            various career options.""",
            verbose=True,
            llm=MODEL_NAME
        )
        
        return profile_analyzer, career_matcher, roadmap_creator
        
    except Exception as e:
        print(f"Error initializing agents: {str(e)}")
        raise

@recommend_bp.route('/recommend', methods=['POST'])
def get_career_recommendations():
    try:
        # Initialize agents
        profile_analyzer, career_matcher, roadmap_creator = initialize_agents()
        
        data = request.get_json()
        
        # Basic validation
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Create tasks
        profile_analysis_task = Task(
            description=f"""Analyze the following user profile and extract key insights:
            Skills: {data.get('skills', 'Not specified')}
            Interests: {data.get('interests', 'Not specified')}
            Strengths: {data.get('strengths', 'Not specified')}
            Personality Traits: {data.get('personality_traits', 'Not specified')}
            Work Style: {data.get('work_style', 'Not specified')}
            Education: {data.get('education', 'Not specified')}
            Salary Expectations: {data.get('salary_expectations', 'Not specified')}
            Tech Preference: {data.get('tech_preference', 'Not specified')}
            Learning Ability: {data.get('learning_ability', 'Not specified')}
            Past Projects: {data.get('past_projects', 'No past projects specified')}
            
            Provide a detailed analysis of the user's profile.
            """,
            agent=profile_analyzer,
            expected_output="A comprehensive analysis of the user's profile."
        )
        
        career_matching_task = Task(
            description="""Based on the profile analysis, recommend the top 5 most suitable 
            career paths. For each career, provide:
            1. Career title
            2. Brief description
            3. Why it's a good fit
            4. Expected salary range
            5. Job market outlook
            
            Format the output as a JSON object with a 'careers' array.
            """,
            agent=career_matcher,
            expected_output="A JSON object containing top 5 career recommendations with details.",
            context=[profile_analysis_task]
        )
        
        roadmap_creation_task = Task(
            description="""For each recommended career, create a detailed learning 
            roadmap including:
            1. Required skills to learn
            2. Recommended courses/resources
            3. Suggested projects
            4. Timeline for skill acquisition
            5. Certifications (if applicable)
            
            Format the output as a JSON object with roadmaps for each career.
            """,
            agent=roadmap_creator,
            expected_output="A JSON object containing detailed learning roadmaps for each recommended career.",
            context=[career_matching_task]
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[profile_analyzer, career_matcher, roadmap_creator],
            tasks=[profile_analysis_task, career_matching_task, roadmap_creation_task],
            verbose=True,
            process=Process.sequential
        )
        
        # Execute the workflow
        result = crew.kickoff()
        
        # Extract the output from CrewOutput object
        # CrewOutput has an 'output' attribute containing the final result
        output_data = result.output if hasattr(result, 'output') else str(result)
        
        # Try to parse as JSON if it's a string
        if isinstance(output_data, str):
            try:
                output_data = json.loads(output_data)
            except json.JSONDecodeError:
                # If it's not JSON, keep it as a string
                pass
        
        # Process and return the result
        return jsonify({
            'status': 'success',
            'result': output_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_career_recommendations: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500