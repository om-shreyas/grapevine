import requests
from dotenv import load_dotenv
load_dotenv()
import os
import json
from pathlib import Path
# Replace with your actual Perplexity API key
API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Resume data directory
RESUME_DIR = Path("data/resumes")

def load_user_resume(user_id: str) -> str:
    """Load user resume from the resume database."""
    resume_file = RESUME_DIR / f"{user_id}.json"
    if not resume_file.exists():
        return ""
    
    try:
        with open(resume_file, 'r') as f:
            resume_data = json.load(f)
            return resume_data.get('resume_text', '')
    except Exception as e:
        print(f"Error loading resume: {e}")
        return ""

def search_job_news(topic: str, user_id: str = None):
    """
    Search for relevant news relating to job search or upskilling
    for a given topic using the Perplexity API.
    """
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # Load user resume if user_id provided
    resume_context = ""
    if user_id:
        resume_text = load_user_resume(user_id)
        if resume_text:
            resume_context = f"\n\nUser's background: {resume_text}"
    
    # We explicitly request "news" relevance in the prompt
    payload = {
        "model": "sonar",  # Fast model with web access
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that finds the latest news articles related to job search, careers, and upskilling."
            },
            {
                "role": "user",
                "content": f"Find the most recent news and updates about '{topic}' in the context of job search or upskilling. Tailor the results to be relevant for someone with this background.{resume_context} Provide links if available."
            }
        ],
        "temperature": 0.2,
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        # Extract the content of the assistant's reply
        answer = result["choices"][0]["message"]["content"]
        return answer
    else:
        return f"Error {response.status_code}: {response.text}"


if __name__ == "__main__":
    topic = "Data Science"
    test_user_id = "test_user_123"
    news = search_job_news(topic, user_id=test_user_id)
    print("\n--- Relevant News ---\n")
    print(news)
