import os
from dotenv import load_dotenv
load_dotenv()
import logging
import json
from typing import List, Dict, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from job_search import JobSearchEngine
from models import SessionLocal, UserProfile

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Structured Output Models (Pydantic Models) ---
# Enforce JSON output format compatible with Frontend rendering

class RoadmapAction(BaseModel):
    phase: str = Field(description="Phase name, e.g., Foundation Skills")
    weeks: str = Field(description="Estimated duration, e.g., Weeks 1-2")
    tasks: List[str] = Field(description="Specific and actionable learning tasks")
    skills_to_acquire: List[str] = Field(description="Skill tags acquired after this phase")
    resources: List[str] = Field(description="Recommended resource links, must include relevant SkillsFuture courses")

class CareerRoadmap(BaseModel):
    gap_analysis: str = Field(description="Detailed analysis of the gap between user skills and target job (especially based on PDF requirements)")
    roadmap: List[RoadmapAction] = Field(description="Phased, personalized career growth roadmap")
    suggested_jobs: List[str] = Field(description="List of relevant Job IDs matched from database")
    gov_support_info: str = Field(description="Relevant government support schemes, like CareersFinder or subsidy info")
    milestones: List[str] = Field(description="Key career milestones, used for Application Tracking")

class FrontendRoadmapStep(BaseModel):
    step: str = Field(description="The specific skill or task to learn/do")
    desc: str = Field(description="Short actionable instruction")
    type: str = Field(description="One of ['course', 'project', 'practice', 'action']")
    status: str = Field(default="todo", description="Always 'todo' for new items")

class FrontendRoadmap(BaseModel):
    steps: List[FrontendRoadmapStep]

from config import config

class CareerAIDEAgents:
    def __init__(self):
        # Use DeepSeek V3/OpenAI model as reasoning core
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL_NAME,
            openai_api_key=config.API_KEY,
            openai_api_base=config.LLM_API_BASE,
            max_tokens=4096,
            temperature=config.LLM_TEMPERATURE
        )
        self.search_engine = JobSearchEngine()
        self.parser = JsonOutputParser(pydantic_object=CareerRoadmap)
        self.frontend_parser = JsonOutputParser(pydantic_object=FrontendRoadmap)

    def _get_skillsfuture_resources(self, target_skills: List[str]) -> str:
        """
        Logic enhancement based on Singapore SkillsFuture course library.
        In live demo, this could connect to real SkillsFuture API or preset course JSON.
        """
        # Preset course examples for common requirements in Techfest Job PDF
        sf_catalog = {
            "Software Engineering": "SkillsFuture Series for Software Development (Up to 90% subsidy)",
            "Python": "Python Programming (SkillsFuture Credit Eligible) by NUS-ISS",
            "AI": "AI Singapore (AISG) Literacy Programme",
            "Data Analysis": "Data Analytics with Tableau (SSG Funded)",
            "Cloud": "AWS Cloud Practitioner Essentials (SkillsFuture Eligible)"
        }
        
        matched = []
        for skill in target_skills:
            if skill in sf_catalog:
                matched.append(f"{skill}: {sf_catalog[skill]}")
        
        return "\n".join(matched) if matched else "Search SkillsFuture Portal for relevant modular certifications."

    def perform_gap_analysis(self, user_profile: str, job_description: str) -> List[Dict[str, Any]]:
        """
        Frontend-specific method to generate a simple linear roadmap.
        Matches the interface expected by the ReUnion frontend.
        """
        try:
            prompt = PromptTemplate(
                template="""You are a Career Coach specializing in Singapore Tech Jobs.
User Profile: {user_profile}
Target Job: {job_description}

Analyze the gap to identify what skills should be bridged to maximize the chance of matching this role.
Create a prioritized roadmap.

1. **Priority Order**: List steps in order of priority (Highest Impact first).
2. **Optional Items**: Mark lower priority or nice-to-have items with "(optional)" in the step title.
3. **Justification**: In the description, provide a brief justification for why this step maximizes the match.

For each step, suggest if it is a 'course' (SkillsFuture preferred), 'project', or 'practice'.

{format_instructions}
""",
                input_variables=["user_profile", "job_description"],
                partial_variables={"format_instructions": self.frontend_parser.get_format_instructions()}
            )
            
            chain = prompt | self.llm | self.frontend_parser
            result = chain.invoke({
                "user_profile": user_profile,
                "job_description": job_description
            })
            
            # Return just the list of steps as expected by frontend
            return [step if isinstance(step, dict) else step.dict() for step in result.get("steps", [])]
        except Exception as e:
            logger.error(f"Gap analysis error: {e}")
            # Fallback
            return [
                {"step": "Analyze Requirements", "desc": "Review job description carefully.", "type": "action", "status": "todo"},
                {"step": "Update Resume", "desc": "Highlight relevant skills.", "type": "action", "status": "todo"}
            ]

    def process_query(self, user_query: str, user_data: Dict = None) -> Dict[str, Any]:
        """
        Frontend-specific method for the chat interface.
        """
        try:
            # Simple direct response for now, can be enhanced with RAG later
            response = self.llm.invoke(f"You are a helpful career assistant. User context: {user_data}. Question: {user_query}")
            return {
                "answer": response.content,
                "agent_name": "🤖 AI Assistant",
                "sources": []
            }
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "answer": "I'm having trouble connecting to the brain. Please try again.",
                "agent_name": "System",
                "sources": []
            }

    def get_career_roadmap(self, user_id: str, user_query: str, filters: dict) -> Dict[str, Any]:
        """
        Core Function: Integrate multi-source data to generate actionable career roadmap.
        """
        session = SessionLocal()
        try:
            # 1. Get User Profile
            user = session.query(UserProfile).filter_by(user_id=user_id).first()
            user_skills = ", ".join(user.skills) if user and user.skills else "Fresh graduate with basic academic knowledge"
            
            # 2. Hybrid Search Job Data (SQL + RAG)
            # Responds to "Integrated data from multiple sources"
            jobs = self.search_engine.search(
                min_salary=filters.get('salary', 0),
                location=filters.get('location'),
                query=user_query
            )
            
            # Extract top 3 relevant jobs for context reasoning
            jobs_context = ""
            job_ids = []
            extracted_tech_stack = [] # Logic for Bonus Tech Stack Filter

            for i, doc in enumerate(jobs[:3]):
                jobs_context += f"Position {i+1}:\n{doc.page_content}\n"
                job_ids.append(doc.metadata.get('job_id', 'Unknown'))
                if doc.metadata.get('skills'):
                    extracted_tech_stack.extend(doc.metadata.get('skills'))

            # 3. Get SkillsFuture Course Recommendations Context
            sf_context = self._get_skillsfuture_resources(extracted_tech_stack)

            # 4. Build Customized Prompt
            prompt = PromptTemplate(
                template="""You are an expert Career Consultant in Singapore specializing in Tech talent.
                
                USER PROFILE:
                - Current Skills: {user_skills}
                - Goal: {career_goal}
                - Search Intent: {user_query}
                
                MARKET REALITY (Integrated Job Data from MCF & Glassdoor):
                {jobs_context}
                
                LOCAL UPSKILLING RESOURCES:
                {sf_context}
                
                TASK:
                1. ANALYZE the 'Skills Gap' between the user and these real Singapore jobs.
                2. CREATE an actionable roadmap. If jobs like 'Hypotenuse Tech' require 'No exp', focus on project portfolios.
                3. INTEGRATE SkillsFuture-eligible courses into the roadmap.
                4. HIGHLIGHT government support schemes like 'CareersFinder' for fresh grads.
                
                {format_instructions}
                """,
                input_variables=["user_skills", "career_goal", "user_query", "jobs_context", "sf_context"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )

            # 5. Execute Reasoning Chain
            chain = prompt | self.llm | self.parser
            
            result = chain.invoke({
                "user_skills": user_skills,
                "career_goal": user.career_goal if user else "Secure a Software Engineering role",
                "user_query": user_query,
                "jobs_context": jobs_context,
                "sf_context": sf_context
            })

            # Append Job IDs list
            result['suggested_jobs'] = job_ids

            # 6. Persist Result (for Frontend Application Tracking)
            if user:
                user.current_roadmap = json.dumps(result)
                user.last_updated = datetime.now()
                session.commit()
            
            return result
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error generating roadmap: {str(e)}")
            return {"error": "Failed to generate roadmap due to an internal error."}
        finally:
            session.close()

    def chat_response(self, user_id: str, message: str, context: str = None) -> str:
        """
        Real-time Chat: Support user follow-up questions on generated roadmap.
        Hint: Can guide users to use CareersFinder to filter government-supported jobs here.
        """
        system_msg = "You are a Singapore Career Assistant. Always be encouraging and provide info on SkillsFuture subsidies."
        # Can reuse self.llm for simple chat logic here
        pass
