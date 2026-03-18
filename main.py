from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from models import UserRequest, AgentResponse
from planner import parse_request
from orchestrator import Orchestrator

app = FastAPI(title="Mini Agent Orchestrator", description="A lightweight, event-driven order processing agent.")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    file_path = "static/index.html"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="UI not found. Please create static/index.html.")

@app.post("/process", response_model=AgentResponse)
async def process_request(request: UserRequest):
    """
    Receives a natural language request, plans it, and executes it.
    Endpoint is asynchronous processing tasks over I/O non-blockingly.
    """
    # 1. Plan the steps
    try:
        plan = parse_request(request.prompt)
    except Exception as e:
        # Fallback format or execution error
        raise HTTPException(status_code=400, detail=f"Planning failed: {str(e)}")
        
    if not plan:
        raise HTTPException(status_code=400, detail="LLM could not formulate a plan from the input.")

    # 2. Orchestrate execution
    orchestrator = Orchestrator()
    result = await orchestrator.execute_plan(plan)
    
    return AgentResponse(**result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
