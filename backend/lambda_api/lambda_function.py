# lambda_function.py
"""Lambda handler for FastAPI music recommender chatbot."""
from mangum import Mangum
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import uuid
import json
import os

# Initialize FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# Initialize Lex client
lex_client = boto3.client("lexv2-runtime")

# Configuration - use environment variables in Lambda
LEX_BOT_ID = os.environ.get("LEX_BOT_ID")
LEX_BOT_ALIAS_ID = os.environ.get("LEX_BOT_ALIAS_ID", "TSTALIASID")
LEX_LOCALE_ID = os.environ.get("LEX_LOCALE_ID", "en_US")

if not LEX_BOT_ID:
    raise ValueError("LEX_BOT_ID environment variable is required")

@app.post("/chat/")
def chat_with_lex(request: ChatRequest):
    # Generate a unique session ID for each request
    session_id = str(uuid.uuid4())

    try:
        response = lex_client.recognize_text(
            botId=LEX_BOT_ID,
            botAliasId=LEX_BOT_ALIAS_ID,
            localeId=LEX_LOCALE_ID,
            sessionId=session_id,
            text=request.message
        )

        messages = response.get("messages", [])
        print(f"Lex response: {messages}")

        if messages:
            return {"response": messages[0].get("content", "")}
        else:
            return {"response": "Sorry, I didn't get that."}

    except Exception as e:
        print(f"Error calling Lex: {str(e)}")
        return {"response": "Sorry, there was an error processing your request."}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Create the Lambda handler
handler = Mangum(app)