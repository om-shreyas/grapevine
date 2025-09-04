import asyncio
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import os
import json
import logging
from quiz import generate_quiz_questions
from news import search_job_news as search_news
from job_search import search_jobs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Enhanced tool definitions with better context guidance
tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_quiz_questions",
            "description": "Generate interview practice questions for a specific role. Use this when user asks for quiz, questions, practice, interview prep, or testing knowledge. IMPORTANT: Always use the exact user_id from the conversation context, not a generic placeholder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "The actual user identifier from the conversation context - DO NOT use placeholder values like 'user-123' or 'default_user'"
                    },
                    "text": {
                        "type": "string", 
                        "description": "The user's exact request text"
                    },

                    "role": {
                        "type": "string", 
                        "description": "Target job role or subject area for the quiz questions"
                    },
                    "past_qs": {
                        "type": "array", 
                        "items": {"type": "string"}, 
                        "description": "Previously asked questions to avoid repetition"
                    }
                },
                "required": ["user_id", "text", "role", "past_qs"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_job_news",
            "description": "Get recent job market news and trends for specific topics. IMPORTANT: Always use the exact user_id from the conversation context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "The actual user identifier from the conversation context - DO NOT use placeholder values"
                    },
                    "text": {
                        "type": "string", 
                        "description": "The user's exact request text"
                    },
                    "topic": {
                        "type": "string", 
                        "description": "Topic to search news for"
                    }
                },
                "required": ["user_id", "text", "topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_jobs",
            "description": "Search for job opportunities. IMPORTANT: Always use the exact user_id from the conversation context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "The actual user identifier from the conversation context - DO NOT use placeholder values"
                    },
                    "text": {
                        "type": "string", 
                        "description": "The user's exact request text"
                    },
                    "query": {
                        "type": "string", 
                        "description": "Job search query or keywords"
                    },
                    "top_k": {
                        "type": "integer", 
                        "description": "Number of jobs to return"
                    }
                },
                "required": ["user_id", "text"]
            }
        }
    }
]

user_histories = {}


async def chatbot_response(user_id: str, user_input: str) -> str:
    """Main chatbot function: handles user-level history and tool use."""
    logger.info(f"Processing request for user {user_id}: {user_input[:50]}...")

    if user_id not in user_histories:
        logger.info(f"Creating new conversation history for user {user_id}")
        # Include user_id in the system prompt
        user_histories[user_id] = [
            {"role": "system", "content": f"""You are a helpful career assistant with access to specialized tools. 

CURRENT USER: {user_id}

IMPORTANT: Use tools proactively when users ask for:
- Quiz/Questions/Practice/Interview prep → Use fetch_quiz_questions
- Job search/opportunities → Use find_jobs  
- Job market news/trends → Use search_job_news

When calling tools:
- ALWAYS use "{user_id}" as the user_id parameter
- ALWAYS use the exact user input as the 'text' parameter
- Don't ask for additional information if you can use default values
- Be proactive in using tools to provide immediate value

Examples:
- "Quiz me on X" → Immediately use fetch_quiz_questions with user_id="{user_id}" and X as the role
- "Find me jobs" → Immediately use find_jobs with user_id="{user_id}"
- "What's happening in the job market" → Immediately use search_job_news with user_id="{user_id}"
"""}
        ]

    history = user_histories[user_id]
    history.append({"role": "user", "content": user_input})

    # Check for quiz-related keywords and add context
    quiz_keywords = ["quiz", "question", "practice", "test", "interview prep", "ask me", "challenge me"]
    should_use_quiz = any(keyword in user_input.lower() for keyword in quiz_keywords)
    
    if should_use_quiz:
        logger.info("Quiz keywords detected - adding user context")
        # Add user context to help with tool calling
        history[-1]["content"] += f" [User ID for tool calls: {user_id}]"

    logger.info("Calling OpenAI API with tools enabled")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=history,
        tools=tools,
        tool_choice="auto",
        temperature=0.3
    )

    message = response.choices[0].message

    if message.tool_calls:
        logger.info(f"OpenAI requested {len(message.tool_calls)} tool call(s)")
        
        history.append({
            "role": "assistant", 
            "content": message.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function", 
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                } for call in message.tool_calls
            ]
        })
        
        for call in message.tool_calls:
            func_name = call.function.name
            args = json.loads(call.function.arguments)
            logger.info(f"Calling tool: {func_name} with OpenAI-generated args: {args}")
            
            if func_name == "fetch_quiz_questions":
                # Fetch resume from file
                resume_file = f"data/resumes/{args['user_id']}.txt"
                try:
                    with open(resume_file, 'r') as f:
                        resume = f.read().strip()
                except FileNotFoundError:
                    resume = ""
                
                logger.info(f"Generating quiz questions for user {args['user_id']}, role: {args['role']}")
                result = generate_quiz_questions(
                    user_id=args["user_id"], 
                    resume=resume, 
                    role=args["role"], 
                    past_questions=args["past_qs"]
                )
            elif func_name == "search_job_news":
                logger.info(f"Searching job news for user {args['user_id']}, topic: {args['topic']}")
                result = search_news(topic=args["topic"], user_id=args["user_id"])
            elif func_name == "find_jobs":
                logger.info(f"Searching jobs for user {args['user_id']}, query: {args.get('query')}")
                result = search_jobs(user_id=args["user_id"], query=args.get("query"), top_k=args.get("top_k", 5))
            else:
                logger.warning(f"Unknown function called: {func_name}")
                result = "Unknown function"
            
            logger.info(f"Tool {func_name} completed successfully")
            
            history.append({
                "role": "tool", 
                "tool_call_id": call.id, 
                "content": str(result)
            })

        logger.info("Getting final response after tool execution")
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=history,
            temperature=0.7
        )
        
        final_reply = final_response.choices[0].message.content
        history.append({"role": "assistant", "content": final_reply})
        
        return final_reply

    else:
        logger.info("No tools called, returning direct response")
        reply = message.content
        history.append({"role": "assistant", "content": reply})
        return reply


async def main():
    print("🤖 Enhanced Career Assistant Chatbot\n")

    while True:
        user_id = input("User ID: ")
        user_input = input(f"{user_id}: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        # Try the enhanced version
        reply = await chatbot_response(user_id, user_input)
        print(f"Bot → {user_id}: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())