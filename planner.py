import os
import json
import re
from typing import List
from models import PlanStep
from dotenv import load_dotenv

# Load variables from .env file into os.environ
load_dotenv()

def parse_request(prompt: str) -> List[PlanStep]:
    """
    Parses a natural language prompt into a list of actionable steps.
    If OPENAI_API_KEY is available in the environment, it uses OpenAI.
    Otherwise, it uses a regex-based mock parser.
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if api_key:
        try:
            return _parse_with_openai(prompt, api_key)
        except Exception as e:
            print(f"Groq API failed ({e}). Falling back to mock parser...")
            return _parse_with_mock(prompt)
    else:
        return _parse_with_mock(prompt)

def _parse_with_openai(prompt: str, api_key: str) -> List[PlanStep]:
    from groq import Groq
    
    # Using Groq API for faster, cost-effective LLM inference
    model_name = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    client = Groq(api_key=api_key)
    
    system_prompt = """
    You are an intelligent order processing planner. 
    You must convert a user's natural language request into a sequence of actionable steps using the available tools.
    Available tools:
    1. cancel_order(order_id: string)
    2. send_email(email: string, message: string)
    
    Return ONLY a JSON array of objects, where each object has an 'action' (tool name) and 'parameters' (JSON object).
    Example for "Cancel order #123 and email user@test.com":
    [
      {"action": "cancel_order", "parameters": {"order_id": "123"}},
      {"action": "send_email", "parameters": {"email": "user@test.com", "message": "Your order #123 was cancelled."}}
    ]
    """
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    # Optional: basic escaping for LLM markdown formatting
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()
        
    data = json.loads(content)
    steps = [PlanStep(**item) for item in data]
    return steps

def _parse_with_mock(prompt: str) -> List[PlanStep]:
    """
    A simple mock parser using regex algorithms instead of requiring an API key. 
    Ideal for local evaluation scenarios where an API key is not ready.
    """
    steps = []
    lower_prompt = prompt.lower()
    
    # Extract order_id if present (handles #123, 123, order 123, order#123)
    order_match = re.search(r'(?:order\s*#?\s*|#)(\w+)', lower_prompt)
    
    # 1. Detect cancellation intent
    cancel_verbs = ["cancel", "delete", "remove", "stop", "abort", "close", "void"]
    found_cancel = any(verb in lower_prompt for verb in cancel_verbs)
    
    if found_cancel and order_match:
        order_id = order_match.group(1)
        steps.append(PlanStep(
            action="cancel_order",
            parameters={"order_id": order_id}
        ))
    
    # 2. Extract email if present
    email_match = re.search(r'([\w\.-]+@[\w\.-]+\.\w+)', lower_prompt)
    email_verbs = ["email", "mail", "send", "notify", "message", "contact"]
    found_notify = any(verb in lower_prompt for verb in email_verbs) or email_match

    if found_notify and email_match:
        email = email_match.group(1)
        
        # Robust message generation based on actual context
        if found_cancel:
            message = f"Your order #{order_match.group(1)} has been cancelled successfully."
        elif order_match:
            # Dynamically find the verb used before the word 'order' or '#'
            verb_match = re.search(r'(\w+)\s+(?:order|#)', lower_prompt)
            unsupported_verb = verb_match.group(1) if verb_match else "unknown_action"
            
            message = f"We received your request to '{unsupported_verb}' an order, but that action is currently unsupported."
            steps.append(PlanStep(
                action=unsupported_verb, # This will report correctly in the orchestrator
                parameters={"order_id": order_match.group(1)}
            ))
        else:
            message = "Your request has been processed."
            
        steps.append(PlanStep(
            action="send_email",
            parameters={"email": email, "message": message}
        ))
        
    # 3. Handle cases where the main intent is completely unknown to the mock parser
    if not steps:
        raise ValueError("I understood your intent, but I cannot perform that action yet.Apologies !!!")
        
    return steps
