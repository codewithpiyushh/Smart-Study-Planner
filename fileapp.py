# enhanced_app.py

import streamlit as st
import json
from datetime import datetime, timedelta
import calendar
from agents import (
    run_question_generation_agent, 
    run_exam_preparator, 
    run_timetable_planner, 
    get_syllabus_direct, 
    create_timetable_direct, 
    generate_study_plan_with_llm, 
    generate_syllabus_with_llm, 
    suggest_topics_to_strengthen,
    generate_questions_direct,
    generate_topic_suggestions
)

# Page configuration with better theme
st.set_page_config(
    page_title="📚 Smart Study Planner", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/study-planner',
        'Report a bug': "https://github.com/yourusername/study-planner/issues",
        'About': "# Smart Study Planner\nYour AI-powered exam preparation companion!"
    }
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .feature-card {
        
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .roadmap-month {
        
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
    }
    
    .roadmap-week {
       
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #2196f3;
    }
    
    .subject-tag {
        
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .quiz-question {
       
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    
    .sidebar-option {
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-radius: 8px;
        cursor: pointer;
    }
    
    .sidebar-option:hover {
        background: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "Timetable Planner"
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🎯 Navigation")
    
    # Navigation buttons with better styling
    if st.button("📅 Timetable Planner", key="nav_timetable", use_container_width=True):
        st.session_state.page = "Timetable Planner"
        st.rerun()
    
    if st.button("📖 Exam Preparer", key="nav_exam", use_container_width=True):
        st.session_state.page = "Exam Preparer"
        st.rerun()
    
    if st.button("🧠 Take A Quiz", key="nav_quiz", use_container_width=True):
        st.session_state.page = "Take A Quiz"
        st.rerun()
    
    st.divider()
    
    # Exam selection
    st.markdown("## 🎓 Select Exam")
    exam_type = st.selectbox("Choose your exam:", ["JEE", "NEET", "UPSC", "GATE"], key="exam_selector")
    
    st.divider()
    
    # Status indicators
    st.markdown("## 📊 Status")
    if st.session_state.quiz_data:
        st.success("✅ Quiz Ready")
    else:
        st.info("💡 Generate a quiz")
    
    # Quick stats or tips based on current page
    if st.session_state.page == "Timetable Planner":
        st.info("💡 **Tip:** Set a realistic exam date for better planning")
    elif st.session_state.page == "Exam Preparer":
        st.info("💡 **Tip:** Review syllabus before creating timetable")
    else:
        st.info("💡 **Tip:** Regular practice improves retention")

# Main header
st.markdown("""
<div class="main-header">
    <h1>📚 Smart Study Planner</h1>
    <p>Your AI-powered exam preparation companion</p>
</div>
""", unsafe_allow_html=True)

# Display current page indicator
st.markdown(f"### 🔹 {st.session_state.page}")

def show_enhanced_roadmap(plan, exam_date):
    """Display an enhanced roadmap with monthly/weekly breakdown"""
    if not plan:
        st.warning("⚠️ No study plan generated.")
        return
    
    st.markdown("## 🗺️ Your Study Roadmap")
    
    # Calculate timeline
    today = datetime.now()
    target_date = datetime.strptime(exam_date, "%Y-%m-%d")
    total_days = (target_date - today).days
    
    # Timeline overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Days Remaining", total_days)
    with col2:
        st.metric("📚 Total Topics", len(plan) if isinstance(plan, list) else 0)
    with col3:
        study_days = sum(1 for day in plan if day.get('type') != 'revision') if isinstance(plan, list) else 0
        st.metric("📖 Study Days", study_days)
    
    st.divider()
    
    # Group plan by months and weeks
    if isinstance(plan, list):
        current_date = today
        month_groups = {}
        
        for day_info in plan:
            day_date = current_date + timedelta(days=day_info['day'] - 1)
            month_key = day_date.strftime("%B %Y")
            week_key = f"Week {day_date.isocalendar()[1]}"
            
            if month_key not in month_groups:
                month_groups[month_key] = {}
            if week_key not in month_groups[month_key]:
                month_groups[month_key][week_key] = []
            
            month_groups[month_key][week_key].append({
                'date': day_date,
                'day_info': day_info
            })
        
        # Display roadmap by month
        for month, weeks in month_groups.items():
            st.markdown(f'<div class="roadmap-month">📅 {month}</div>', unsafe_allow_html=True)
            
            for week, days in weeks.items():
                with st.expander(f"📊 {week} ({len(days)} days)", expanded=True):
                    for day_data in days:
                        day_info = day_data['day_info']
                        date_str = day_data['date'].strftime("%a, %b %d")
                        
                        if day_info.get('type') == 'revision':
                            st.markdown(f"""
                            <div class="roadmap-week">
                                <strong>🔄 {date_str} - Revision Day</strong><br>
                                <em>{day_info.get('topics', 'Review all covered topics')}</em>
                            </div>
                            """, unsafe_allow_html=True)
                        elif day_info.get('topics'):
                            subjects = []
                            topic_details = []
                            for topic_info in day_info["topics"]:
                                subject = topic_info['subject']
                                topic = topic_info['topic']
                                hours = topic_info.get('suggested_hours', 2)
                                
                                if subject not in subjects:
                                    subjects.append(subject)
                                topic_details.append(f"• {topic} ({hours}h)")
                            
                            subject_tags = ''.join([f'<span class="subject-tag">{s}</span>' for s in subjects])
                            topic_list = '<br>'.join(topic_details)
                            
                            st.markdown(f"""
                            <div class="roadmap-week">
                                <strong>📚 {date_str}</strong><br>
                                {subject_tags}<br>
                                <div style="margin-top: 0.5rem;">
                                    {topic_list}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
    else:
        # Fallback for markdown format
        st.markdown(plan)

def show_enhanced_syllabus(syllabus_content):
    """Display syllabus with better formatting"""
    st.markdown("## 📋 Complete Syllabus")
    
    if isinstance(syllabus_content, str):
        st.markdown(syllabus_content)
    else:
        st.markdown("### 📚 Curriculum Overview")
        for subject, topics in syllabus_content.items():
            with st.expander(f"📖 {subject}", expanded=True):
                if isinstance(topics, dict):
                    for topic, subtopics in topics.items():
                        st.markdown(f"**• {topic}**")
                        if subtopics:
                            st.markdown("  *Subtopics:* " + ", ".join(subtopics))
                else:
                    for topic in topics:
                        st.markdown(f"• {topic}")

def display_enhanced_quiz_results(quiz_data, user_answers):
    """Enhanced quiz results with better UI"""
    questions = quiz_data.get('questions', [])
    if not questions:
        st.error("❌ No questions found in quiz data.")
        return
    
    score = 0
    total_questions = len(questions)
    wrong_topics = []
    
    st.markdown("## 🎯 Quiz Results")
    
    # Score overview
    for idx, question in enumerate(questions):
        user_answer = user_answers.get(f"q_{idx}", "")
        correct_answer = question.get('answer', '')
        is_correct = user_answer == correct_answer
        
        if is_correct:
            score += 1
        else:
            topic = question.get('topic', f"Question {idx+1}")
            wrong_topics.append(topic)
    
    percentage = (score / total_questions) * 100
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{score}/{total_questions}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        if percentage >= 80:
            st.metric("Grade", "A", "🎉")
        elif percentage >= 60:
            st.metric("Grade", "B", "👍")
        else:
            st.metric("Grade", "C", "📚")
    
    st.divider()
    
    # Detailed results
    st.markdown("### 📝 Detailed Review")
    for idx, question in enumerate(questions):
        user_answer = user_answers.get(f"q_{idx}", "")
        correct_answer = question.get('answer', '')
        is_correct = user_answer == correct_answer
        
        result_emoji = "✅" if is_correct else "❌"
        result_color = "success" if is_correct else "error"
        
        with st.expander(f"{result_emoji} Question {idx+1}", expanded=False):
            st.markdown(f"**Question:** {question.get('question', 'N/A')}")
            st.markdown(f"**Your Answer:** {user_answer}")
            st.markdown(f"**Correct Answer:** {correct_answer}")
            if question.get('topic'):
                st.markdown(f"**Topic:** {question['topic']}")
    
    # Performance feedback
    st.divider()
    if percentage >= 80:
        st.success("🎉 **Excellent Performance!** You have a strong understanding of the concepts.")
    elif percentage >= 60:
        st.warning("👍 **Good Performance!** Focus on the missed topics for improvement.")
    else:
        st.error("📚 **Needs Improvement** Review the fundamentals and practice more.")
    
    # Study recommendations
    if wrong_topics:
        st.markdown("### 📈 Personalized Study Recommendations")
        with st.spinner("Generating recommendations..."):
            try:
                topics_str = ", ".join(wrong_topics)
                suggestions = generate_topic_suggestions(exam_type, wrong_topics)
                if suggestions and suggestions.strip():
                    st.markdown(suggestions)
                else:
                    st.error("No suggestions generated. Please try again.")
            except Exception as e:
                st.error(f"Could not generate suggestions: {str(e)}")
                st.markdown("**Topics to focus on:**")
                for topic in set(wrong_topics):
                    st.markdown(f"• {topic}")

# Exam subject mapping for selection
EXAM_SUBJECTS = {
    "JEE": ["Mathematics", "Physics", "Chemistry"],
    "NEET": ["Physics", "Chemistry", "Biology"],
    "UPSC": ["General Studies", "CSAT", "Essay"],
    "GATE": ["General Aptitude", "Technical"]
}

# Main content based on selected page
if st.session_state.page == "Timetable Planner":
    st.markdown("""
    <div class="feature-card">
        <h3>📅 Smart Timetable Planning</h3>
        <p>Create a personalized study roadmap with AI-powered scheduling that adapts to your exam date and syllabus requirements.</p>
    </div>
    """, unsafe_allow_html=True)
    
    deadline = st.date_input("🗓️ When is your exam?", help="Select your exam date to create an optimized study plan")
    
    if st.button("🚀 Generate Smart Roadmap", type="primary", use_container_width=True):
        if isinstance(deadline, tuple):
            selected_date = deadline[0] if len(deadline) > 0 else None
        else:
            selected_date = deadline
            
        if selected_date:
            with st.spinner("🤖 AI is creating your personalized study roadmap..."):
                try:
                    plan_content = generate_study_plan_with_llm(exam_type, selected_date.strftime("%Y-%m-%d"))
                    
                    # Try to parse if it's structured data, otherwise display as markdown
                    try:
                        if isinstance(plan_content, str) and plan_content.strip().startswith('['):
                            plan_data = json.loads(plan_content)
                            show_enhanced_roadmap(plan_data, selected_date.strftime("%Y-%m-%d"))
                        else:
                            st.success("✅ Your Study Roadmap is Ready!")
                            show_enhanced_roadmap(plan_content, selected_date.strftime("%Y-%m-%d"))
                    except:
                        st.success("✅ Your Study Plan is Ready!")
                        st.markdown(plan_content)
                        
                except Exception as e:
                    st.error(f"❌ Error generating study plan: {str(e)}")
        else:
            st.error("⚠️ Please select a valid exam date.")

elif st.session_state.page == "Exam Preparer":
    st.markdown("""
    <div class="feature-card">
        <h3>📖 Comprehensive Syllabus Overview</h3>
        <p>Get a complete, structured breakdown of your exam syllabus with topics and subtopics organized for optimal learning.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📚 Load Complete Syllabus", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is organizing your syllabus..."):
            try:
                syllabus_content = generate_syllabus_with_llm(exam_type)
                st.success("✅ Syllabus Loaded Successfully!")
                show_enhanced_syllabus(syllabus_content)
            except Exception as e:
                st.error(f"❌ Error generating syllabus: {str(e)}")

elif st.session_state.page == "Take A Quiz":
    st.markdown("""
    <div class="feature-card">
        <h3>🧠 Intelligent Practice Quiz</h3>
        <p>Test your knowledge with AI-generated questions tailored to your exam. Get instant feedback and personalized study recommendations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Subject selection and number of questions (always visible)
    subjects = EXAM_SUBJECTS.get(exam_type, [])
    selected_subjects = st.multiselect("Select subject(s) for the quiz:", subjects, default=subjects[:1] if subjects else [])
    num_questions = st.slider("Number of questions:", 3, 10, 5)
    
    # Only show quiz generation button if at least one subject is selected
    if selected_subjects:
        if st.button("🎯 Generate Practice Quiz", type="primary", use_container_width=True) or st.session_state.quiz_data is None:
            with st.spinner("🤖 AI is creating your personalized quiz..."):
                try:
                    subject_str = ", ".join(selected_subjects)
                    quiz_data = generate_questions_direct(f"{exam_type} - {subject_str}", num_questions)
                    if quiz_data and quiz_data.get('questions'):
                        st.session_state.quiz_data = quiz_data
                        st.session_state.quiz_submitted = False
                        st.session_state.user_answers = {}
                        st.success(f"✅ Generated {len(quiz_data['questions'])} questions!")
                        st.rerun()
                    else:
                        st.error("❌ Could not generate quiz questions. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error generating quiz: {str(e)}")
    else:
        st.info("Please select at least one subject to start the quiz.")
    
    # Display Quiz Questions
    if st.session_state.quiz_data and not st.session_state.quiz_submitted:
        questions = st.session_state.quiz_data.get('questions', [])
        
        if questions:
            st.markdown("## 📝 Practice Questions")
            
            with st.form("quiz_form"):
                for idx, question in enumerate(questions):
                    st.markdown(f"""
                    <div class="quiz-question">
                        <strong>Question {idx+1}:</strong> {question.get('question', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    options = question.get('options', [])
                    if options:
                        user_choice = st.radio(
                            "Select your answer:",
                            options,
                            key=f"q_{idx}",
                            index=None
                        )
                        st.session_state.user_answers[f"q_{idx}"] = user_choice
                    else:
                        st.error(f"❌ No options available for question {idx+1}")
                    
                    st.divider()
                
                submitted = st.form_submit_button("📊 Submit Quiz", type="primary", use_container_width=True)
                
                if submitted:
                    unanswered = []
                    for idx in range(len(questions)):
                        if f"q_{idx}" not in st.session_state.user_answers or st.session_state.user_answers[f"q_{idx}"] is None:
                            unanswered.append(idx + 1)
                    
                    if unanswered:
                        st.error(f"⚠️ Please answer all questions. Missing: {', '.join(map(str, unanswered))}")
                    else:
                        st.session_state.quiz_submitted = True
                        st.rerun()
    
    # Display Results
    if st.session_state.quiz_data and st.session_state.quiz_submitted:
        display_enhanced_quiz_results(st.session_state.quiz_data, st.session_state.user_answers)
        
        st.divider()
        if st.button("🔄 Take Another Quiz", use_container_width=True):
            st.session_state.quiz_data = None
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = {}
            st.rerun()

# Footer
st.divider()
