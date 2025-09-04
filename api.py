from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
import os
import pandas as pd
from chatbot import chatbot_response
from pdf_processor import process_pdf_resume

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    user_id: str
    user_input: str

class ChatResponse(BaseModel):
    response: str

class UploadResponse(BaseModel):
    success: bool
    message: str

class UserCheckResponse(BaseModel):
    exists: bool

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    with open("static/upload.html", "r") as f:
        return f.read()

@app.get("/chat-ui", response_class=HTMLResponse)
async def chat_page():
    with open("static/chat.html", "r") as f:
        return f.read()

@app.get("/check-user/{user_id}", response_model=UserCheckResponse)
async def check_user(user_id: str):
    try:
        users_df = pd.read_csv("data/users.csv")
        logger.info(f"Users CSV loaded with {len(users_df)} rows")
        logger.info(f"Checking if user {user_id} exists in: {users_df['user_id'].tolist()}")
        exists = user_id in users_df['user_id'].values
        logger.info(f"User {user_id} exists: {exists}")
        return UserCheckResponse(exists=exists)
    except FileNotFoundError:
        logger.warning("users.csv file not found")
        return UserCheckResponse(exists=False)
    except Exception as e:
        logger.error(f"Error checking user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking user")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Chat request received for user {request.user_id}")
    logger.info(f"User input: {request.user_input[:100]}...")
    
    response = await chatbot_response(request.user_id, request.user_input)
    
    logger.info(f"Chat response generated for user {request.user_id}")
    return ChatResponse(response=response)

@app.post("/upload-resume", response_model=UploadResponse)
async def upload_resume(user_id: str = Form(...), file: UploadFile = File(...)):
    logger.info(f"Resume upload request received for user {user_id}")
    logger.info(f"File: {file.filename}, Content-Type: {file.content_type}")
    
    try:
        if file.content_type != "application/pdf":
            logger.warning(f"Invalid file type uploaded: {file.content_type}")
            return UploadResponse(success=False, message="Only PDF files are allowed")
        
        logger.info("Reading PDF file bytes")
        pdf_bytes = await file.read()
        logger.info(f"PDF file read successfully, size: {len(pdf_bytes)} bytes")
        
        logger.info("Processing PDF resume")
        success = process_pdf_resume(user_id, pdf_bytes)
        
        if success:
            logger.info(f"Resume processed successfully for user {user_id}")
            return UploadResponse(success=True, message="Resume uploaded successfully")
        else:
            logger.error(f"Failed to process resume for user {user_id}")
            return UploadResponse(success=False, message="Failed to process resume")
    
    except Exception as e:
        logger.error(f"Exception during resume upload for user {user_id}: {str(e)}")
        return UploadResponse(success=False, message=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server on host 0.0.0.0, port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)