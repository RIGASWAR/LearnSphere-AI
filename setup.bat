@echo off

echo ======================================
echo 🚀 Setting up EduGenie AI
echo ======================================

python -m venv venv

call venv\Scripts\activate

pip install --upgrade pip

pip install -r requirements.txt

if not exist .env (
    echo OPENAI_API_KEY=your_key_here > .env
    echo GROQ_API_KEY=your_key_here >> .env
)

echo ======================================
echo ✅ Setup Complete!
echo Run: streamlit run app.py
echo ======================================

pause