# --- api_server.py ---
# This file is used to run the agent API
# uvicorn api_server:app --reload

from fastapi import FastAPI
import asyncio
from main import main

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Agent API is running!"}

@app.get("/run-agent")
async def run_agent():
    result = await main()
    return {"result": result}





