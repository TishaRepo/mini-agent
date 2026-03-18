# Mini Agent Orchestrator

A lightweight, event-driven order processing agent built with Python and FastAPI. This agent receives natural language requests, plans executable steps using an LLM (or a fallback mock service), and orchestrates their asynchronous execution sequentially while maintaining state and guardrails.

## Overview

- **The Planner**: Parses an unstructured prompt like "Cancel order #9921 and email me at user@example.com" into a structured execution plan (DAG or sequence of tool calls). It seamlessly switches between a direct OpenAI integration when `OPENAI_API_KEY` is present, or a regex-based mock parser when the key is absent.
- **The Orchestrator**: Executes the generated plan asynchronously.
- **Tools**: Includes `cancel_order` with a simulated 20% random failure rate, and `send_email` with an asynchronous 1-second simulated delay.
- **Guardrails & State**: Handles tool failure gracefully. If step 1 (like `cancel_order`) fails, step 2 (like `send_email`) is aborted to prevent misleading communications.

## Setup & Local Run

1. Clone or download the repository, then navigate to the project directory:
    ```bash
    cd mini-agent
    ```
2. Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    venv\Scripts\activate   # On Windows
    # source venv/bin/activate # On Unix/macOS
    pip install -r requirements.txt
    ```
3. (Optional) Set your OpenAI API key for real LLM planning. If omitted, it will use the robust regex-based mock parser:
    ```bash
    set OPENAI_API_KEY=your-api-key   # On Windows
    # export OPENAI_API_KEY="your-api-key" # On Unix/macOS
    ```
4. Run the application:
    ```bash
    uvicorn main:app --reload
    ```
5. Perform a POST request to the API:
    ```bash
    curl -X POST http://127.0.0.1:8000/process ^
         -H "Content-Type: application/json" ^
         -d "{\"prompt\": \"Cancel my order #9921 and email me the confirmation at user@example.com\"}"
    ```
    (Note: Using `^` and escaped quotes for Windows CMD. For bash/zsh, use `\` and single quotes.)

## Architectural Choices

### State Handling & Workflow Async Execution
- **Concurrency via FastAPI**: The application leverages `asyncio` built into Python and uses FastAPI as its underlying handler routing requests asynchronously.
- **Async Execution**: The `Orchestrator` internally awaits async processes allowing mock steps (which replicate I/O API wait times using `asyncio.sleep()`) to run without blocking the web server thread loop.
- **Execution State**: Tracks step executions continuously using a mutable local `results` list aggregated chronologically in memory per request lifecycle payload constraint.

### Short-Circuiting and Guarding Failures
Workflows usually embody step dependencies. A subsequent step (e.g. email notice) implicitly relies on a predecessor establishing a truth paradigm first (e.g. cancellation execution).
When `cancel_order` simulates a failure (20% rate):
1. The Orchestrator halts traversing through further `PlanStep` tasks instantly.
2. The user sees a clear status detailing exact partial failures and reasons why steps aborted.

### Managing LLM Unreliability
- **Fallback Planning**: Direct network issues, exhausted quotas, or disabled API keys transparently fallback towards an integrated deterministic regex mechanism ensuring the application validates testing without 100% LLM uptime dependency.
- **Strict Format Prompts**: Restricts open-ended hallucination variables via "Zero-Shot" rigid structured JSON instructions mapped to local defined boundaries (`AVAILABLE_TOOLS`). Schema compliance operates gracefully natively. 

## Clean Architecture Note
Instead of bulky frameworks like Langchain, this enforces bare separation of concerns: `planner.py` extracts intents, `orchestrator.py` conducts state, and endpoints exist completely agnostic of prompt orchestration syntax.
