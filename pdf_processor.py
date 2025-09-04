import PyPDF2
from pathlib import Path
import io

import pandas as pd
from datetime import datetime

RESUMES_DIR = Path("data/resumes")
USERS_FILE = Path("data/users.csv")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def save_resume_to_file(user_id: str, resume_text: str) -> bool:
    """Save resume text to individual file."""
    try:
        RESUMES_DIR.mkdir(parents=True, exist_ok=True)
        resume_file = RESUMES_DIR / f"{user_id}.txt"
        
        with open(resume_file, 'w', encoding='utf-8') as f:
            f.write(resume_text)
        
        return True
    except Exception as e:
        raise Exception(f"Failed to save resume: {str(e)}")

def register_user(user_id: str) -> bool:
    """Register user in users.csv file."""
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing users or create empty DataFrame
        try:
            df = pd.read_csv(USERS_FILE)
        except FileNotFoundError:
            df = pd.DataFrame(columns=['user_id', 'username', 'password', 'name', 'email', 'registration_date'])
        
        # Check if user already exists
        if user_id in df['user_id'].values:
            return True
        
        # Add new user
        new_user = pd.DataFrame([{
            'user_id': user_id,
            'username': user_id,
            'password': '',
            'name': '',
            'email': '',
            'registration_date': datetime.now().isoformat()
        }])
        
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_csv(USERS_FILE, index=False)
        
        return True
    except Exception as e:
        raise Exception(f"Failed to register user: {str(e)}")

def process_pdf_resume(user_id: str, pdf_bytes: bytes) -> bool:
    """Process PDF resume and save to file."""
    resume_text = extract_text_from_pdf(pdf_bytes)
    success = save_resume_to_file(user_id, resume_text)
    
    if success:
        print(f"Registering user: {user_id}")
        register_user(user_id)
        print(f"User {user_id} registered")
    
    return success