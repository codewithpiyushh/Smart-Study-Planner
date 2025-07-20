# agents.py
import json
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.tools import tool
from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# === Tool: Load syllabus ===
@tool
def load_syllabus(exam_name: str) -> str:
    """LLM-powered: Generates a detailed syllabus for the given exam (jee, neet, upsc, gate) with subtopics."""
    llm = get_gemini_llm()
    prompt = (
        f"You are an expert exam coach. "
        f"Generate a complete, detailed syllabus for the {exam_name} exam, including all subjects, topics, and subtopics. "
        f"Format the output as JSON."
    )
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, 'content') else result
    if not isinstance(content, str):
        content = str(content)
    return content

# === Tool: Create timetable ===
@tool
def create_timetable(syllabus_json: str, end_date: str) -> str:
    """LLM-powered: Generates a detailed daily study plan to cover the syllabus within the given time frame. Each day includes subject, topic, subtopics, and suggested hours. Revision days are added at the end. Returns JSON."""
    llm = get_gemini_llm()
    prompt = (
        f"You are an expert study planner. "
        f"Given the following syllabus (as JSON): {syllabus_json}\n"
        f"and the exam end date: {end_date}, generate a daily study timetable to cover the entire syllabus by the end date. "
        f"For each day, specify the subject, topic, subtopics, and suggested study hours. Include revision days. Format the output as JSON."
    )
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, 'content') else result
    if not isinstance(content, str):
        content = str(content)
    return content

# === Tool: Generate Questions ===
@tool
def generate_questions(exam_name: str, num_questions: int = 5) -> str:
    """
    LLM-powered: Generates a multiple-choice quiz for the given exam. Returns a JSON string with a list of questions, each with 'question', 'options', and 'answer'.
    """
    llm = get_gemini_llm()
    prompt = (
        f"Generate {num_questions} multiple-choice questions for the {exam_name} exam. "
        f"Each question should be based on the official syllabus, cover a variety of topics, and have 4 options (A, B, C, D). "
        f"Return ONLY a valid JSON object in this exact format:\n"
        f'{{\n'
        f'  "questions": [\n'
        f'    {{\n'
        f'      "question": "What is the derivative of x^2?",\n'
        f'      "options": ["2x", "x", "2", "x^2"],\n'
        f'      "answer": "2x",\n'
        f'      "topic": "Calculus"\n'
        f'    }}\n'
        f'  ]\n'
        f'}}\n'
        f"Make sure the JSON is properly formatted and contains exactly {num_questions} questions."
    )
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, 'content') else result
    if not isinstance(content, str):
        content = str(content)
    
    # Clean up the response to extract JSON
    content = content.strip()
    if content.startswith('```json'):
        content = content[7:]
    if content.endswith('```'):
        content = content[:-3]
    content = content.strip()
    
    return content

# === Tool: Suggest Topics to Strengthen ===
@tool
def suggest_topics_to_strengthen(exam_name: str, wrong_topics: str) -> str:
    """
    LLM-powered: Suggests study tips and resources for topics where the student made mistakes. wrong_topics should be a comma-separated string.
    """
    llm = get_gemini_llm()
    prompt = (
        f"For the {exam_name} exam, suggest detailed study tips and resources for the following topics where the student made mistakes: {wrong_topics}. "
        f"Format the output as a markdown list with specific actionable advice for each topic."
    )
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, 'content') else result
    if not isinstance(content, str):
        content = str(content)
    return content

# === Gemini LLM Setup ===
def get_gemini_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        google_api_key=GEMINI_API_KEY
    )

# === Agent 1: Exam Preparator ===
def get_exam_preparator_agent():
    llm = get_gemini_llm()
    tools = [Tool(
        name="load_syllabus",
        func=load_syllabus,
        description="Loads syllabus JSON for a given exam (jee or neet) with all topics and subtopics."
    )]
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

# === Agent 2: Timetable Planner ===
def get_timetable_planner_agent():
    llm = get_gemini_llm()
    tools = [Tool(
        name="create_timetable",
        func=create_timetable,
        description="Creates a detailed daily study plan to cover the syllabus within the given time frame. Each day includes subject, topic, subtopics, and suggested hours. Revision days are added at the end."
    )]
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

# === Agent 3: Question Generator ===
def get_question_generation_agent():
    llm = get_gemini_llm()
    tools = [Tool(
        name="generate_questions",
        func=generate_questions,
        description="Generates a multiple-choice quiz for the given exam with specified number of questions."
    )]
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

# === Direct function calls (bypassing agents for simplicity) ===
def get_syllabus_direct(exam_name: str):
    """Direct function to get syllabus without going through agent"""
    return load_syllabus(exam_name)

def create_timetable_direct(syllabus: dict, end_date: str):
    """Direct function to create a detailed timetable without going through agent"""
    today = datetime.today()
    target = datetime.strptime(end_date, "%Y-%m-%d")
    days = max(1, (target - today).days)
    topic_list = [(subject, topic) for subject, topics in syllabus.items() for topic in topics]
    total_topics = len(topic_list)
    revision_days = max(1, days // 7)
    study_days = days - revision_days
    topics_per_day = max(1, total_topics // study_days) if study_days > 0 else total_topics
    plan = []
    for i in range(study_days):
        start_idx = i * topics_per_day
        end_idx = min((i + 1) * topics_per_day, total_topics)
        day_plan = topic_list[start_idx:end_idx]
        if day_plan:
            detailed_topics = [
                {
                    "subject": subject,
                    "topic": topic,
                    "suggested_hours": 2 if subject.lower() != "essay" else 1
                }
                for subject, topic in day_plan
            ]
            plan.append({"day": i + 1, "type": "study", "topics": detailed_topics})
    for j in range(revision_days):
        plan.append({"day": study_days + j + 1, "type": "revision", "topics": "Revise all covered topics"})
    return plan

# === Standalone agent access for UI ===
def run_exam_preparator(exam_name: str):
    """Run exam preparator with proper input format"""
    try:
        agent = get_exam_preparator_agent()
        result = agent.run(f"Load the syllabus for {exam_name} exam with all topics and subtopics.")
        try:
            return json.loads(result)
        except Exception:
            return result
    except Exception as e:
        print(f"Agent error: {e}")
        return {}

def run_timetable_planner(syllabus: dict, end_date: str):
    """Run timetable planner with proper input format"""
    try:
        agent = get_timetable_planner_agent()
        syllabus_json = json.dumps(syllabus)
        result = agent.run(f"Create a detailed timetable for syllabus: {syllabus_json} with end date: {end_date}. Include subtopics and suggested hours.")
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return result
        return result
    except Exception as e:
        print(f"Agent error: {e}")
        return []

def run_question_generation_agent(exam_name: str, num_questions: int = 5):
    """Fixed function to generate questions properly"""
    try:
        # Direct function call for better reliability
        result = generate_questions(exam_name, num_questions)
        
        # Parse the JSON result
        if isinstance(result, str):
            try:
                parsed_result = json.loads(result)
                return parsed_result
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Raw result: {result}")
                return None
        else:
            return result
    except Exception as e:
        print(f"Question generation error: {e}")
        return None

def generate_questions_direct(exam_name: str, num_questions: int = 5):
    """Direct question generation without agent wrapper"""
    try:
        llm = get_gemini_llm()
        prompt = (
            f"Generate {num_questions} multiple-choice questions for the {exam_name} exam. "
            f"Each question should be based on the official syllabus and cover different topics. "
            f"Return ONLY a valid JSON object in this exact format:\n"
            f'{{\n'
            f'  "questions": [\n'
            f'    {{\n'
            f'      "question": "Question text here?",\n'
            f'      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
            f'      "answer": "Correct option text",\n'
            f'      "topic": "Topic name"\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n'
            f"Make sure the JSON is properly formatted."
        )
        
        result = llm.invoke(prompt)
        content = result.content if hasattr(result, 'content') else str(result)
        
        # Clean up the response
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        parsed_result = json.loads(content)
        return parsed_result
        
    except Exception as e:
        print(f"Direct question generation error: {e}")
        return None
    
def generate_study_plan_with_llm(exam_name: str, end_date: str):
    llm = get_gemini_llm()
    prompt = (
        f"You are an expert study planner. "
        f"Generate a complete, detailed syllabus for the {exam_name} exam, including all subjects, topics, and subtopics. "
        f"Then, create a daily study timetable to cover the entire syllabus by {end_date}. "
        f"For each day, specify the subject, topic, subtopics, and suggested study hours. "
        f"Include revision days and make the plan as detailed and realistic as possible. "
        f"Format the output as markdown with clear sections for Syllabus and Timetable."
    )
    result = llm.invoke(prompt)
    return result.content if hasattr(result, 'content') else result

def generate_syllabus_with_llm(exam_name: str):
    llm = get_gemini_llm()
    prompt = (
        f"You are an expert exam coach. "
        f"Generate a complete, detailed syllabus for the {exam_name} exam, including all subjects, topics, and subtopics. "
        f"Format the output as markdown with clear sections for each subject."
    )
    result = llm.invoke(prompt)
    return result.content if hasattr(result, 'content') else result

def generate_topic_suggestions(exam_name: str, wrong_topics: list):
    """Generate study suggestions for topics where student made mistakes"""
    topics_str = ", ".join(wrong_topics)
    llm = get_gemini_llm()
    prompt = (
        f"For the {exam_name} exam, suggest detailed study tips and resources for the following topics where the student made mistakes: {topics_str}. "
        f"Format the output as a markdown list with specific actionable advice for each topic."
    )
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, 'content') else result
    if not isinstance(content, str):
        content = str(content)
    return content