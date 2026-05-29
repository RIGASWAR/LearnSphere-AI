import streamlit as st
from dotenv import load_dotenv
from agent_handler import StudyAssistantHandler
from config import ConfigManager
import matplotlib.pyplot as plt
import speech_recognition as sr
import pyttsx3
import threading
from datetime import date
import random

# =========================
# ENV
# =========================
load_dotenv()

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="EduGenie AI",
    layout="wide",
    page_icon="📚"
)

# =========================
# MODERN UI CSS
# =========================
st.markdown("""
<style>

/* MAIN APP */
.stApp {
    background: linear-gradient(135deg, #0B1120, #111827, #1E1B4B);
    background-attachment: fixed;
    color: white;
    font-family: 'Poppins', sans-serif;
}

/* REMOVE DEFAULT */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* MAIN TITLE */
.main-title {
    font-size: 4rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, #8B5CF6, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 10px;
    margin-bottom: 5px;
}

/* SUBTITLE */
.subtitle {
    text-align: center;
    color: #cbd5e1;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* GLASS CARD */
.glass-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px;
    padding: 25px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

/* BUTTONS */
.stButton > button {
    width: 100%;
    border-radius: 14px;
    border: none;
    padding: 0.7rem 1rem;
    background: linear-gradient(90deg, #7C3AED, #06B6D4);
    color: white;
    font-size: 1rem;
    font-weight: 600;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(124,58,237,0.5);
}

/* INPUT BOXES */
.stTextInput > div > div > input,
.stTextArea textarea {
    background-color: rgba(255,255,255,0.08) !important;
    color: white !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

/* METRIC CARDS */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: rgba(255,255,255,0.05);
    padding: 10px;
    border-radius: 15px;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 12px;
    color: #cbd5e1;
    padding: 10px 18px;
    transition: 0.3s;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg,#7C3AED,#06B6D4);
    color: white !important;
}

/* CHAT */
.stChatMessage {
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 10px;
    margin-bottom: 10px;
}

/* PROGRESS BAR */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg,#7C3AED,#06B6D4);
}

/* SCROLLBAR */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #7C3AED;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HERO SECTION
# =========================
st.markdown("""
<div class="glass-card" style="
background: linear-gradient(
135deg,
rgba(124,58,237,0.35),
rgba(6,182,212,0.25)
);
padding:40px;
margin-bottom:30px;
text-align:center;
">

<h1 style="
font-size:3.5rem;
font-weight:800;
margin-bottom:10px;
color:white;
">
📚 EduGenie AI
</h1>

<p style="
font-size:1.2rem;
color:#E2E8F0;
margin-bottom:20px;
">
AI-Powered Personalized Learning Platform
</p>

<div style="
display:flex;
justify-content:center;
gap:12px;
flex-wrap:wrap;
margin-top:15px;
">

<span style="
background:rgba(255,255,255,0.12);
padding:10px 18px;
border-radius:999px;
color:white;
font-size:0.95rem;
">
🤖 AI Tutor
</span>

<span style="
background:rgba(255,255,255,0.12);
padding:10px 18px;
border-radius:999px;
color:white;
font-size:0.95rem;
">
🗺️ Smart Roadmaps
</span>

<span style="
background:rgba(255,255,255,0.12);
padding:10px 18px;
border-radius:999px;
color:white;
font-size:0.95rem;
">
🎤 Voice AI
</span>

<span style="
background:rgba(255,255,255,0.12);
padding:10px 18px;
border-radius:999px;
color:white;
font-size:0.95rem;
">
🎮 Gamification
</span>

</div>
</div>
""", unsafe_allow_html=True)

# =========================
# INIT
# =========================
config_manager = ConfigManager()

# =========================
# SESSION STATE
# =========================
defaults = {
    "step": 1,
    "handler": None,
    "chat_history": [],
    "planner": [],
    "xp": 0,
    "level": 1,
    "badges": [],
    "streak": 0,
    "last_action_day": None,
    "student_analysis": None,
    "learning_roadmap": None,
    "learning_resources": None
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# VOICE SYSTEM
# =========================
engine = pyttsx3.init()
voice_running = False
stop_flag = False

def speak(text):
    global voice_running, stop_flag
    voice_running = True
    stop_flag = False

    def run_voice():
        global voice_running
        engine.say(text)
        engine.runAndWait()
        voice_running = False

    threading.Thread(target=run_voice, daemon=True).start()

def stop_voice():
    global voice_running, stop_flag
    stop_flag = True
    try:
        engine.stop()
    except:
        pass

def listen():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        st.info("🎤 Listening...")
        audio = r.listen(source)

    try:
        return r.recognize_google(audio)
    except:
        return ""

# =========================
# GAMIFICATION
# =========================
def add_xp(points):
    st.session_state.xp += points

    if st.session_state.xp >= st.session_state.level * 100:
        st.session_state.xp -= st.session_state.level * 100
        st.session_state.level += 1
        st.session_state.badges.append(f"Level {st.session_state.level}")

def update_streak():
    today = str(date.today())

    if st.session_state.last_action_day is None:
        st.session_state.streak = 1

    elif st.session_state.last_action_day != today:
        st.session_state.streak += 1

    st.session_state.last_action_day = today

# =========================
# STEP 1
# =========================
if st.session_state.step == 1:

    st.markdown("## 🎯 Choose Your Learning Category")

    categories = [
        "programming",
        "math",
        "science",
        "languages",
        "business"
    ]

    cols = st.columns(len(categories))

    for i, c in enumerate(categories):
        with cols[i]:
            if st.button(c.title()):
                st.session_state.subject_category = c
                st.session_state.step = 2
                st.rerun()

# =========================
# STEP 2
# =========================
elif st.session_state.step == 2:

    st.markdown("## 📌 Set Your Learning Goal")

    topic = st.text_input("Enter Topic")
    goal = st.text_area("What do you want to achieve?")

    if st.button("🚀 Create Personalized Plan", disabled=not (topic and goal)):
        st.session_state.topic = topic
        st.session_state.learning_goal = goal
        st.session_state.step = 3
        st.rerun()

# =========================
# STEP 3
# =========================
elif st.session_state.step == 3:

    st.markdown("## ⚡ Generating Your AI Learning Plan")

    if st.session_state.handler is None:
        st.session_state.handler = StudyAssistantHandler(
            topic=st.session_state.topic,
            subject_category=st.session_state.subject_category,
            knowledge_level="beginner",
            learning_goal=st.session_state.learning_goal,
            time_available="5 hours",
            learning_style="visual",
            model_name="llama-3.3-70b-versatile",
            provider="groq"
        )

    handler = st.session_state.handler

    if st.session_state.student_analysis is None:
        with st.spinner("🧠 Analyzing student profile..."):
            st.session_state.student_analysis = handler.analyze_student()

    if st.session_state.learning_roadmap is None:
        with st.spinner("🗺️ Creating roadmap..."):
            r = handler.create_roadmap(st.session_state.student_analysis)
            st.session_state.learning_roadmap = r["roadmap"]

    if st.session_state.learning_resources is None:
        with st.spinner("📚 Finding resources..."):
            r = handler.find_resources()
            st.session_state.learning_resources = r["resources"]

    if (
        st.session_state.learning_roadmap
        and st.session_state.learning_resources
    ):
        st.session_state.step = 4
        st.rerun()

# =========================
# STEP 4 DASHBOARD
# =========================
elif st.session_state.step == 4:

    st.markdown("## 🚀 Learning Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📘 Topic", st.session_state.topic)

    with col2:
        st.metric("🏆 Level", st.session_state.level)

    with col3:
        st.metric("⚡ XP", st.session_state.xp)

    with col4:
        st.metric("🔥 Streak", st.session_state.streak)

    tabs = st.tabs([
        "🗺️ Roadmap",
        "📚 Resources",
        "🤖 Tutor",
        "🎤 Voice",
        "📅 Planner",
        "📊 Progress",
        "🎮 Games"
    ])

    # ROADMAP
    with tabs[0]:
        st.markdown(st.session_state.learning_roadmap)

    # RESOURCES
    with tabs[1]:
        st.markdown(st.session_state.learning_resources)

    # TUTOR
    with tabs[2]:

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask anything...")

        if user_input:

            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })

            response = st.session_state.handler.get_tutoring(
                user_input,
                context=str(st.session_state.chat_history[-6:])
            )

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })

            add_xp(10)
            update_streak()

            st.rerun()

    # VOICE
    with tabs[3]:

        st.subheader("🎤 Voice AI Assistant")

        if st.button("🎙️ Speak Question"):

            text = listen()

            if text:

                st.write("You said:", text)

                response = st.session_state.handler.get_tutoring(text)

                st.write(response)

                speak(response)

                add_xp(10)
                update_streak()

        if st.button("🛑 Stop Voice"):
            stop_voice()

    # PLANNER
    with tabs[4]:

        st.subheader("📅 Study Planner")

        task = st.text_input("New Task")

        if st.button("➕ Add Task") and task:
            st.session_state.planner.append({
                "task": task,
                "done": False
            })

            add_xp(5)
            update_streak()

        for i, t in enumerate(st.session_state.planner):

            col1, col2 = st.columns([5, 1])

            with col1:
                st.session_state.planner[i]["done"] = st.checkbox(
                    t["task"],
                    value=t["done"]
                )

            with col2:
                if st.button("❌", key=i):
                    st.session_state.planner.pop(i)
                    st.rerun()

    # PROGRESS
    with tabs[5]:

        st.subheader("📊 Learning Progress")

        completed = sum(
            1 for t in st.session_state.planner if t["done"]
        )

        pending = len(st.session_state.planner) - completed

        fig, ax = plt.subplots()

        ax.bar(
            ["Completed", "Pending"],
            [completed, pending]
        )

        st.pyplot(fig)

        progress = min(100, st.session_state.xp % 100)

        st.progress(progress / 100)

        st.write(f"Level Progress: {progress}%")

        st.write("🏅 Badges:", st.session_state.badges)

    # GAMES
    with tabs[6]:

        st.subheader("🎮 Learning Games")

        game = st.selectbox(
            "Choose Game",
            ["Quiz Battle", "Memory Game", "Speed Math"]
        )

        if game == "Quiz Battle":

            q1 = st.text_input("What is JVM?")
            q2 = st.text_input("Python type?")

            if st.button("Submit Quiz"):

                score = 0

                if q1.lower() == "java virtual machine":
                    score += 1

                if q2.lower() == "interpreted":
                    score += 1

                st.success(f"🎉 Score: {score}/2")

                add_xp(score * 20)

        elif game == "Memory Game":

            word = "inheritance"

            st.info("🧠 Remember: inheritance")

            ans = st.text_input("Type word")

            if st.button("Check"):

                if ans.lower() == word:

                    st.success("✅ Correct!")

                    add_xp(30)

                else:
                    st.error("❌ Wrong")

        elif game == "Speed Math":

            a = random.randint(1, 20)
            b = random.randint(1, 20)

            st.write(f"### {a} + {b} = ?")

            ans = st.text_input("Answer")

            if st.button("Check Answer"):

                if ans and int(ans) == a + b:

                    st.success("✅ Correct!")

                    add_xp(25)

                else:

                    st.error(f"❌ Answer: {a+b}")

    st.divider()

    if st.button("🔄 Restart"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]

        st.rerun()