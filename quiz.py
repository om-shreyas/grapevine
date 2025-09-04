import requests
from dotenv import load_dotenv
import json
import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
load_dotenv()

API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Quiz data directory
QUIZ_DIR = Path("data/quizzes")

def load_user_past_questions(user_id: str, days_back: int = 30) -> list[str]:
    """Load past questions for a user from the last N days."""
    quiz_file = QUIZ_DIR / f"{user_id}.csv"
    if not quiz_file.exists():
        return []
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    past_questions = []
    
    try:
        with open(quiz_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                question_date = datetime.fromisoformat(row['timestamp'])
                if question_date > cutoff_date:
                    past_questions.append(row['question_text'])
    except Exception as e:
        print(f"Error loading past questions: {e}")
    
    return past_questions

def save_user_quiz_questions(user_id: str, questions: list[str]):
    quiz_file = QUIZ_DIR / f"{user_id}.csv"
    
    if not quiz_file.exists():
        QUIZ_DIR.mkdir(parents=True, exist_ok=True)
        with open(quiz_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['question_text', 'timestamp'])
    
    timestamp = datetime.now().isoformat()
    try:
        with open(quiz_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for question in questions:
                writer.writerow([question, timestamp])
    except Exception as e:
        print(f"Error saving quiz questions: {e}")


def generate_quiz_questions(user_id: str, resume: str, role: str, past_questions: list[str]) -> list[str]:
    """
    Generate quiz/interview questions tailored to a candidate's resume and a job role.
    Avoids repeating previously asked questions.
    Returns a Python list of new questions.
    """
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    past_q_str = "\n".join([f"- {q}" for q in past_questions]) if past_questions else "None"

    prompt = f"""
You are an expert interviewer. Your task is to generate quiz-style or interview-style questions 
tailored to the following job role and candidate resume.

Role: {role}
Resume: {resume}

The following questions were already asked, do NOT repeat them:
{past_q_str}

Return exactly 5 NEW questions in valid JSON format as a Python list of strings. 
Do not include explanations, only the JSON list.
Example:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]
"""

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are an expert job interviewer and question generator."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4  # factual + role-relevant
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        try:
            questions = json.loads(content)
            if isinstance(questions, list):
                # Save questions to user's quiz file if user_id provided
                if user_id:
                    save_user_quiz_questions(user_id, questions)
                return questions
            else:
                raise ValueError("Model did not return a list.")
        except Exception as e:
            return [f"Error parsing response: {e}", content]

    else:
        return [f"Error {response.status_code}: {response.text}"]


if __name__ == "__main__":
    resume_text = """
    B.Tech in Computer Science, interned at Adobe in Machine Learning,
    built projects on Stock Prediction, NLP models, and Reinforcement Learning.
    Published papers on GANs and Knowledge Graphs.
    """
    role = "Machine Learning Engineer"
    
    # Test with user ID
    test_user_id = "test_user_123"
    new_questions = generate_quiz_questions(user_id=test_user_id, resume=resume_text, role=role)
    print("\n--- Generated Quiz Questions ---\n")
    for q in new_questions:
        print("-", q)
