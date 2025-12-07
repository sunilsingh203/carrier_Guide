from crewai import Agent
import google.generativeai as genai

class ProfileAnalyzer:
    def __init__(self):
        # Use Gemini Flash 2.5 model identifier
        self.model = genai.GenerativeModel('gemini/gemini-2.5-flash')
        
    def create_agent(self):
        return Agent(
            role='Profile Analyzer',
            goal='Analyze user profile to understand skills, interests, and personality',
            backstory="""You are an expert at analyzing user profiles to understand their 
            core competencies, interests, and personality traits. You help identify 
            key strengths and preferences that are crucial for career matching.""",
            verbose=True,
            llm=self.model,
            tools=[],
            allow_delegation=False
        )