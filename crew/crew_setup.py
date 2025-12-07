from crewai import Crew, Process, Task
from agents.profile_agent import ProfileAnalyzer
from agents.matcher_agent import CareerMatcher
from agents.roadmap_agent import RoadmapCreator

class CareerCrew:
    def __init__(self):
        self.profile_analyzer = ProfileAnalyzer().create_agent()
        self.career_matcher = CareerMatcher().create_agent()
        self.roadmap_creator = RoadmapCreator().create_agent()
        
    def setup_crew(self, user_data):
        """Set up and return the crew with tasks"""
        # Create tasks for each agent
        profile_task = self._create_profile_analysis_task(user_data)
        matching_task = self._create_career_matching_task()
        roadmap_task = self._create_roadmap_creation_task()
        
        # Create and return the crew
        return Crew(
            agents=[self.profile_analyzer, self.career_matcher, self.roadmap_creator],
            tasks=[profile_task, matching_task, roadmap_task],
            verbose=2,
            process=Process.sequential
        )
    
    def _create_profile_analysis_task(self, user_data):
        """Create the profile analysis task"""
        return Task(
            description=f"""Analyze the following user profile and extract key insights:
            {user_data}
            
            Provide a detailed analysis of the user's profile, including:
            1. Core skills and strengths
            2. Key interests and preferences
            3. Personality traits and work style
            4. Educational background and learning preferences
            5. Career aspirations and salary expectations
            """,
            agent=self.profile_analyzer,
            expected_output="A comprehensive analysis of the user's profile."
        )
    
    def _create_career_matching_task(self):
        """Create the career matching task"""
        return Task(
            description="""Based on the profile analysis, recommend the top 5 most suitable 
            career paths. For each career, provide:
            1. Career title
            2. Brief description
            3. Why it's a good fit
            4. Expected salary range
            5. Job market outlook
            
            Format the output as a JSON object with career recommendations.
            """,
            agent=self.career_matcher,
            expected_output="A JSON object containing top 5 career recommendations with details."
        )
    
    def _create_roadmap_creation_task(self):
        """Create the roadmap creation task"""
        return Task(
            description="""For each recommended career, create a detailed learning 
            roadmap including:
            1. Required skills to learn
            2. Recommended courses/resources
            3. Suggested projects
            4. Timeline for skill acquisition
            5. Certifications (if applicable)
            
            Format the output as a JSON object with roadmaps for each career.
            """,
            agent=self.roadmap_creator,
            expected_output="A JSON object containing detailed learning roadmaps for each recommended career."
        )