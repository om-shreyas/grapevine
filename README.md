# Grapevine - AI-Powered Career Assistant

Grapevine is an intelligent career assistance application that helps users find jobs, take skill quizzes, and stay updated with relevant news to keep them motivated and prepared for their job search journey.

## Features

- **Job Search**: AI-powered job matching based on your resume and preferences
- **Interactive Chat**: Get personalized career advice and job recommendations
- **Resume Processing**: Upload and analyze your PDF resume for better job matching
- **Skill Quizzes**: Test your knowledge and improve your skills
- **Career News**: Stay updated with industry trends and job market insights

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   
   cd "grapevine"
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv env_job
   source env_job/bin/activate  # On Windows: env_job\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Create data directories**
   ```bash
   mkdir -p data/resumes data/quizzes
   ```

### Running the Application

1. **Start the server**
   ```bash
   python api.py
   ```

2. **Access the application**
   Open your web browser and go to: `http://localhost:8000`

## Usage

1. **First Time Users**:
   - Enter your user ID on the home page
   - Upload your resume (PDF format only)
   - Start chatting with the AI assistant

2. **Returning Users**:
   - Enter your existing user ID
   - Continue directly to the chat interface

3. **Chat Features**:
   - Ask for job recommendations
   - Get career advice
   - Request skill quizzes
   - Ask for industry news and trends

## File Structure

```
grapevine/
├── api.py              # Main FastAPI application
├── chatbot.py          # AI chatbot logic
├── pdf_processor.py    # Resume processing
├── job_search.py       # Job matching system
├── quiz.py             # Quiz functionality
├── news.py             # News fetching
├── static/             # Frontend HTML files
│   ├── index.html      # Home page
│   ├── upload.html     # Resume upload page
│   └── chat.html       # Chat interface
├── data/               # Data storage
│   ├── users.csv       # User database
│   ├── jobs.csv        # Job listings
│   ├── resumes/        # Processed resumes
│   └── quizzes/        # Quiz results
└── requirements.txt    # Python dependencies
```

## API Endpoints

- `GET /` - Home page
- `GET /upload` - Resume upload page
- `GET /chat-ui` - Chat interface
- `GET /check-user/{user_id}` - Check if user exists
- `POST /upload-resume` - Upload and process resume
- `POST /chat` - Chat with AI assistant

## Troubleshooting

- **Server won't start**: Check if port 8000 is available
- **Resume upload fails**: Ensure file is PDF format and under 10MB
- **Chat not working**: Verify OpenAI API key is set correctly
- **User not found**: Try uploading resume again to register

## Support

For issues or questions, check the application logs for detailed error messages.