import yaml
import streamlit as st
from study_agents import StudyAgents
from rag_helper import RAGHelper


class StudyAssistantHandler:
    def __init__(self, topic, subject_category, knowledge_level,
                 learning_goal, time_available, learning_style,
                 model_name="llama-3.3-70b-versatile",provider="groq"):

        self.topic = topic
        self.subject_category = subject_category
        self.knowledge_level = knowledge_level
        self.learning_goal = learning_goal
        self.time_available = time_available
        self.learning_style = learning_style
        self.model_name = model_name
        self.provider = provider

        self.agents = StudyAgents(
            topic, subject_category, knowledge_level,
            learning_goal, time_available,
            learning_style, model_name, provider
        )

        self.config = self._load_config()
        self.rag_helper = None

    # =========================
    # CONFIG LOADER
    # =========================
    def _load_config(self):
        with open("prompts.yaml", "r") as file:
            return yaml.safe_load(file)

    def _format_prompt(self, prompt_template, **kwargs):
        return prompt_template.format(**kwargs)

    # =========================
    # STUDENT ANALYSIS
    # =========================
    def analyze_student(self):
        with st.status("Analyzing your learning profile...", expanded=True):
            analyzer = self.agents.student_analyzer_agent()

            prompt = self._format_prompt(
                self.config["prompts"]["student_analysis"]["base"],
                topic=self.topic,
                subject_category=self.subject_category,
                knowledge_level=self.knowledge_level,
                learning_goal=self.learning_goal,
                time_available=self.time_available,
                learning_style=self.learning_style
            )

            resp = analyzer.run(prompt, stream=False)

            result = resp.content

            st.session_state.student_analysis = result

            return {"analysis": result}

    # =========================
    # ROADMAP (FIXED OUTPUT)
    # =========================
    def create_roadmap(self, student_analysis: str):
        with st.status("Creating roadmap...", expanded=True):

            creator = self.agents.roadmap_creator_agent()

            prompt = self._format_prompt(
                self.config["prompts"]["roadmap_creation"]["base"],
                student_analysis=student_analysis,
                topic=self.topic,
                learning_goal=self.learning_goal,
                time_available=self.time_available,
                knowledge_level=self.knowledge_level
            )

            resp = creator.run(prompt, stream=False)

            result = resp.content

            st.session_state.learning_roadmap = result

            # 🔥 FIX: ALWAYS RETURN CLEAN DICT
            return {"roadmap": result}

    # =========================
    # RESOURCES (FIXED - NO TOOL USAGE)
    # =========================
    def find_resources(self):
        with st.status("Finding learning resources...", expanded=True):

            finder = self.agents.resource_finder_agent()

            prompt = f"""
You are an expert learning assistant.

Provide HIGH QUALITY learning resources for:

Topic: {self.topic}
Goal: {self.learning_goal}
Level: {self.knowledge_level}
Style: {self.learning_style}

Include:
- YouTube videos
- Free websites
- Practice platforms
- Roadmap suggestions

Format in clean markdown with links.
"""

            resp = finder.run(prompt, stream=False)

            result = resp.content

            st.session_state.learning_resources = result

            # 🔥 FIX: ALWAYS RETURN CLEAN DICT
            return {"resources": result}

    # =========================
    # QUIZ
    # =========================
    def generate_quiz(self, difficulty_level="intermediate",
                      focus_areas="general", num_questions=10):

        quiz_agent = self.agents.quiz_generator_agent()

        prompt = self._format_prompt(
            self.config["prompts"]["quiz_generation"]["base"],
            topic=self.topic,
            difficulty_level=difficulty_level,
            focus_areas=focus_areas,
            num_questions=num_questions
        )

        resp = quiz_agent.run(prompt, stream=False)

        return {"quiz": resp.content}

    # =========================
    # TUTOR
    # =========================
    def get_tutoring(self, student_question: str, context: str = ""):

        tutor = self.agents.tutor_agent()

        prompt = self._format_prompt(
            self.config["prompts"]["tutoring"]["base"],
            student_question=student_question,
            context=context,
            knowledge_level=self.knowledge_level
        )

        resp = tutor.run(prompt, stream=False)

        return resp.content

    # =========================
    # RAG SYSTEM
    # =========================
    def initialize_rag(self, collection_name="study_materials"):
        self.rag_helper = RAGHelper(collection_name=collection_name)

    def add_document_to_rag(self, file_path: str, file_type: str = "pdf"):
        if not self.rag_helper:
            self.initialize_rag()

        if file_type == "pdf":
            return self.rag_helper.load_pdf(file_path)
        else:
            return self.rag_helper.load_text(file_path)

    def query_documents(self, question: str, k: int = 4):

        if not self.rag_helper:
            return "No documents uploaded yet."

        docs = self.rag_helper.query(question, k=k)

        if not docs:
            return "No relevant information found."

        context = "\n\n".join(docs)

        rag_tutor = self.agents.rag_tutor_agent()

        prompt = self._format_prompt(
            self.config["prompts"]["rag_query"]["base"],
            question=question,
            context=context
        )

        resp = rag_tutor.run(prompt, stream=False)

        return resp.content

    # =========================
    # UTIL
    # =========================
    def get_document_count(self):
        if not self.rag_helper:
            return 0
        return self.rag_helper.get_document_count()

    def clear_documents(self):
        if not self.rag_helper:
            return False
        return self.rag_helper.clear_database()