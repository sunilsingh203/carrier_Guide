from crewai import Agent
import google.generativeai as genai

class CareerMatcher:
    def __init__(self):
        # Use Gemini Flash 2.5 model identifier
        self.model = genai.GenerativeModel('gemini/gemini-2.5-flash')
        
    def create_agent(self):
        return Agent(
            role='Career Matcher',
            goal='Match user profile to suitable career paths',
            backstory="""You are a career matching expert who takes analyzed user profiles 
            and maps them to the most suitable career paths based on their skills, 
            interests, and market demand.""",
            verbose=True,
            llm=self.model,
            tools=[],
            allow_delegation=False
        )