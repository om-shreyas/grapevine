import csv
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, CrossEncoder
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

bi_encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

JOBS_FILE = Path("data/jobs.csv")
JOBS_SHOWN_FILE = Path("data/jobs_shown.csv")
JOBS_INDEX_FILE = Path("data/jobs.index")
RESUMES_DIR = Path("data/resumes")

def load_jobs() -> pd.DataFrame:
    if not JOBS_FILE.exists():
        return pd.DataFrame(columns=['job_id', 'job_title', 'company', 'job_link', 'description', 'requirements', 'location', 'salary', 'posting_date'])
    return pd.read_csv(JOBS_FILE)

def load_jobs_shown(user_id: str) -> set:
    if not JOBS_SHOWN_FILE.exists():
        return set()
    
    df = pd.read_csv(JOBS_SHOWN_FILE)
    user_jobs = df[df['user_id'] == user_id]['job_id'].tolist()
    return set(user_jobs)

def save_job_shown(user_id: str, job_id: str):
    timestamp = datetime.now().isoformat()
    
    # Create file with headers if it doesn't exist
    if not JOBS_SHOWN_FILE.exists():
        with open(JOBS_SHOWN_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'job_id', 'timestamp'])
    
    # Append new record
    with open(JOBS_SHOWN_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, job_id, timestamp])

def build_job_index():
    jobs_df = load_jobs()
    
    if jobs_df.empty:
        print("No jobs found to index")
        return None
    
    job_texts = []
    for _, job in jobs_df.iterrows():
        text = f"{job['job_title']} {job['description']} {job['requirements']}"
        job_texts.append(text)
    
    embeddings = bi_encoder.encode(job_texts)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)

    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype('float32'))
    
    faiss.write_index(index, str(JOBS_INDEX_FILE))
    print(f"Built index with {len(job_texts)} jobs")
    return index

def load_job_index():
    if JOBS_INDEX_FILE.exists():
        return faiss.read_index(str(JOBS_INDEX_FILE))
    else:
        return build_job_index()

def get_user_resume_text(user_id: str) -> str:
    resume_file = RESUMES_DIR / f"{user_id}.txt"
    
    if not resume_file.exists():
        return ""
    
    try:
        with open(resume_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return ""

def search_jobs(user_id: str, query: str = None, top_k: int = 10) -> List[Dict[str, Any]]:

    jobs_df = load_jobs()
    if jobs_df.empty:
        return []
    
    jobs_shown = load_jobs_shown(user_id)
    index = load_job_index()
    
    if index is None:
        return []
    
    if query:
        search_text = query
    else:
        search_text = get_user_resume_text(user_id)
        if not search_text:
            return []
    
    query_embedding = bi_encoder.encode([search_text])
    faiss.normalize_L2(query_embedding)
    
    scores, indices = index.search(query_embedding.astype('float32'), min(top_k * 3, len(jobs_df)))
    
    candidates = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(jobs_df):
            job = jobs_df.iloc[idx]
            if job['job_id'] not in jobs_shown:
                job_dict = job.to_dict()
                job_dict['similarity_score'] = float(score)
                candidates.append(job_dict)
    
    if candidates and len(candidates) > 1:
        job_texts = []
        for job in candidates:
            text = f"{job['job_title']} {job['description']} {job['requirements']}"
            job_texts.append(text)
        
        pairs = [[search_text, job_text] for job_text in job_texts]
        
        cross_scores = cross_encoder.predict(pairs)
        
        for i, score in enumerate(cross_scores):
            candidates[i]['rerank_score'] = float(score)
        
        candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
    
    results = candidates[:top_k]
    for job in results:
        save_job_shown(user_id, job['job_id'])
    
    return results

def add_job(job_data: Dict[str, Any]) -> str:
    import uuid
    
    job_id = str(uuid.uuid4())
    job_data['job_id'] = job_id
    
    df = load_jobs()
    new_job_df = pd.DataFrame([job_data])
    df = pd.concat([df, new_job_df], ignore_index=True)
    df.to_csv(JOBS_FILE, index=False)
    
    build_job_index()
    
    return job_id

if __name__ == "__main__":
    sample_jobs = [
        {
            "job_title": "Machine Learning Engineer",
            "company": "TechCorp",
            "job_link": "https://example.com/job1",
            "description": "Build ML models for recommendation systems",
            "requirements": "Python, TensorFlow, 3+ years experience",
            "location": "Remote",
            "salary": "$120k-150k",
            "posting_date": "2024-01-15"
        },
        {
            "job_title": "Data Scientist",
            "company": "DataInc",
            "job_link": "https://example.com/job2", 
            "description": "Analyze large datasets and build predictive models",
            "requirements": "Python, SQL, Statistics, PhD preferred",
            "location": "San Francisco",
            "salary": "$130k-160k",
            "posting_date": "2024-01-16"
        }
    ]
    
    for job in sample_jobs:
        job_id = add_job(job)
        print(f"Added job: {job_id}")
    
    print("Job search system initialized!")