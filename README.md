# Tool-Enhanced AI Assistant - Interview Task 

## Overview
In this task, you'll implement a simple tool for an AI assistant. The system should enable the assistant to fetch the current time.

## What's Already Implemented
The repository contains a working FastAPI application with:
* A streaming chat endpoint that connects to Claude
* A simple web interface for testing the chat functionality
* Basic project structure and configuration


Implement a tool that allows the assistant to:
1. Fetch the current time
2. Use this information in conversations with users

## Requirements

### Time Tool Implementation
1. **Time Tool Design**:
   * Create a simple tool function that returns the current date and time
   * Make this tool callable by the assistant through the function calling interface

2. **Context Integration**:
   * Update the system prompt to instruct the Assistant on using the time tool
   * Ensure the assistant knows when and how to use this tool effectively

### Example Flow

```
User: "What time is it right now?"
(Assistant calls get_current_time())
Assistant: "The current time is 3:45 PM on May 9, 2025."

User: "Is it winter?"
(Assistant calls get_current_time())
Assistant: "Today is May 9, 2025. It is not winter."
```

## Getting Started
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt` (Note, not all python versions are compatible. When in doubt, use python 3.10)
3. Set your `ANTHROPIC_API_KEY` in `.env` (copy from `.env.example`)
4. Run the application: `uvicorn app.main:app --reload`
5. Access the chat interface at http://localhost:8000
6. Implement the time tool by extending the existing code

