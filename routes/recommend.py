from flask import Blueprint, request, jsonify, url_for
import json
import os
from datetime import datetime
from crewai import Task, Crew, Process, Agent
from dotenv import load_dotenv
import google.generativeai as genai
import uuid
import tempfile
from multiprocessing import Process as MPProcess
from pathlib import Path

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


def _run_crew_and_write_output(form_data, out_path):
    """
    Worker function to run the crew.kickoff and write normalized JSON output to out_path.
    This runs in a separate process to avoid blocking the web worker.
    """
    try:
        # Re-create agents and tasks inside the child process
        profile_analyzer, career_matcher, roadmap_creator = initialize_agents()

        profile_analysis_task = Task(
            description=f"Analyze profile: {form_data}",
            agent=profile_analyzer,
            expected_output="JSON summary of profile",
        )

        career_matching_task = Task(
            description="Match user profile to suitable careers",
            agent=career_matcher,
            expected_output="JSON list of careers",
            context=[profile_analysis_task]
        )

        roadmap_creation_task = Task(
            description="Create learning roadmaps for recommended careers",
            agent=roadmap_creator,
            expected_output="JSON roadmaps",
            context=[career_matching_task]
        )

        crew = Crew(
            agents=[profile_analyzer, career_matcher, roadmap_creator],
            tasks=[profile_analysis_task, career_matching_task, roadmap_creation_task],
            verbose=False,
            process=Process.sequential
        )

        result = crew.kickoff()
        output_data = result.output if hasattr(result, 'output') else str(result)

        # Try to parse JSON if possible
        if isinstance(output_data, str):
            try:
                output_data = json.loads(output_data)
            except Exception:
                pass

        normalized = normalize_career_data(output_data)

        # Write to file
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({'status': 'success', 'result': normalized, 'timestamp': datetime.utcnow().isoformat()}, f)
    except Exception as e:
        # On error, write error info so status endpoint can report it
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({'status': 'error', 'message': str(e), 'timestamp': datetime.utcnow().isoformat()}, f)

@recommend_bp.route('/recommend', methods=['POST'])
def get_career_recommendations():
    try:
        data = request.get_json()

        # Basic validation
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        
        # Launch the heavy LLM workflow in a background process and return a job ID
        job_id = str(uuid.uuid4())
        out_dir = os.path.join(tempfile.gettempdir(), 'career_helper_jobs')
        out_path = os.path.join(out_dir, f"{job_id}.json")

        # Spawn process to run crew and write result
        p = MPProcess(target=_run_crew_and_write_output, args=(data, out_path))
        p.daemon = True
        p.start()

        status_url = url_for('recommend.get_recommendation_status', job_id=job_id, _external=False)
        return jsonify({'status': 'accepted', 'job_id': job_id, 'status_url': status_url}), 202
        
    except Exception as e:
        print(f"Error in get_career_recommendations: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def normalize_career_data(data):
    """
    Normalize career data into a standardized structure.
    Handles various agent output formats and converts to career_roadmaps array.
    """
    print(f"[NORMALIZE] Input type: {type(data)}")
    
    if not data:
        print(f"[NORMALIZE] Data is empty/None")
        return {'career_roadmaps': []}
    
    # If it's a string, try to parse it first
    if isinstance(data, str):
        print(f"[NORMALIZE] Input is string (len: {len(data)})")
        # Try several strategies to extract JSON from wrapped text:
        # 1) fenced code blocks with ```json or ```
        # 2) balanced {...} or [...] substring extraction that respects string quotes
        try:
            import re

            # Strategy A: fenced JSON blocks ```json ... ``` or ``` ... ```
            fenced_json = re.search(r'```\s*json\s*([\s\S]*?)```', data, re.IGNORECASE)
            if not fenced_json:
                fenced_json = re.search(r'```([\s\S]*?)```', data)
            if fenced_json:
                candidate = fenced_json.group(1).strip()
                try:
                    parsed = json.loads(candidate)
                    print(f"[NORMALIZE] Extracted JSON from fenced code block")
                    return normalize_career_data(parsed)
                except Exception as e:
                    print(f"[NORMALIZE] Fenced JSON parse failed: {e}")

            # Strategy B: find the first balanced JSON object or array substring
            def find_balanced(text, open_ch, close_ch):
                start = text.find(open_ch)
                if start == -1:
                    return None
                depth = 0
                in_str = False
                esc = False
                for i in range(start, len(text)):
                    ch = text[i]
                    if esc:
                        esc = False
                        continue
                    if ch == '\\':
                        esc = True
                        continue
                    if ch == '"':
                        in_str = not in_str
                        continue
                    if in_str:
                        continue
                    if ch == open_ch:
                        depth += 1
                    elif ch == close_ch:
                        depth -= 1
                        if depth == 0:
                            return text[start:i+1]
                return None

            # Try object then array
            obj_candidate = find_balanced(data, '{', '}')
            arr_candidate = find_balanced(data, '[', ']')

            # Prefer object candidate if it exists and parses
            for candidate in (obj_candidate, arr_candidate):
                if candidate:
                    try:
                        parsed = json.loads(candidate)
                        print(f"[NORMALIZE] Extracted JSON by balanced-scan")
                        return normalize_career_data(parsed)
                    except Exception as e:
                        print(f"[NORMALIZE] Balanced-scan parse failed: {e}")
        except Exception as e:
            print(f"[NORMALIZE] Exception while extracting JSON from string: {e}")

        print(f"[NORMALIZE] Could not extract JSON from string, returning empty")
        return {'career_roadmaps': []}
    
    # If it's already in the correct format
    if isinstance(data, dict) and 'career_roadmaps' in data:
        if isinstance(data['career_roadmaps'], list):
            print(f"[NORMALIZE] Already has career_roadmaps ({len(data['career_roadmaps'])} items)")
            return data
    
    # If it's an array of careers
    if isinstance(data, list):
        print(f"[NORMALIZE] Is array ({len(data)} items)")
        return {'career_roadmaps': data}
    
    # If it's a dict, examine its structure
    if isinstance(data, dict):
        print(f"[NORMALIZE] Is dict with keys: {list(data.keys())}")
        
        # If it's a dict with 'careers' key
        if 'careers' in data:
            careers = data['careers']
            if isinstance(careers, list):
                print(f"[NORMALIZE] Found 'careers' key ({len(careers)} items)")
                return {'career_roadmaps': careers}
        
        # If it's a dict with 'roadmap' key
        if 'roadmap' in data:
            roadmap = data['roadmap']
            if isinstance(roadmap, list):
                print(f"[NORMALIZE] Found 'roadmap' array ({len(roadmap)} items)")
                return {'career_roadmaps': roadmap}
            elif isinstance(roadmap, dict):
                print(f"[NORMALIZE] Found 'roadmap' dict")
                return {'career_roadmaps': [roadmap]}
        
        # If it looks like a single career object
        if 'career_title' in data or 'title' in data:
            print(f"[NORMALIZE] Looks like single career object")
            return {'career_roadmaps': [data]}
        
        # If it has 'roadmaps' (plural)
        if 'roadmaps' in data and isinstance(data['roadmaps'], list):
            print(f"[NORMALIZE] Found 'roadmaps' array ({len(data['roadmaps'])} items)")
            return {'career_roadmaps': data['roadmaps']}
        
        # Look for any array values that might be careers
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                print(f"[NORMALIZE] Found potential careers array in key '{key}' ({len(value)} items)")
                if isinstance(value[0], dict):
                    return {'career_roadmaps': value}
    
    # Fallback: wrap the entire data
    print(f"[NORMALIZE] Fallback: wrapping entire data")
    return {'career_roadmaps': [data] if isinstance(data, dict) else []}


@recommend_bp.route('/recommend/status/<job_id>', methods=['GET'])
def get_recommendation_status(job_id):
    out_dir = os.path.join(tempfile.gettempdir(), 'career_helper_jobs')
    out_path = os.path.join(out_dir, f"{job_id}.json")
    if os.path.exists(out_path):
        try:
            with open(out_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Failed reading result: {e}'}), 500
    else:
        return jsonify({'status': 'pending'}), 202