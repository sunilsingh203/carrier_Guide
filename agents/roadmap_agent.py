from crewai import Agent
import google.generativeai as genai

class RoadmapCreator:
    def __init__(self):
        # Use Gemini Flash 2.5 model identifier
        self.model = genai.GenerativeModel('gemini/gemini-2.5-flash')
        
    def create_agent(self):
        return Agent(
            role='Career Roadmap Creator',
            goal='Create detailed learning roadmaps for recommended careers',
            backstory="""You are an expert in career development and education planning. 
            You create actionable learning paths and skill development plans for 
            various career options.""",
            verbose=True,
            llm=self.model,
            tools=[],
            allow_delegation=False
        )