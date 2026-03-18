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
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        try:
            return _parse_with_openai(prompt, api_key)
        except Exception as e:
            print(f"OpenAI API failed ({e}). Falling back to mock parser...")
            return _parse_with_mock(prompt)
    else:
        return _parse_with_mock(prompt)

def _parse_with_openai(prompt: str, api_key: str) -> List[PlanStep]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
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
        model="gpt-3.5-turbo",
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
    
    # Extract order_id if present
    order_match = re.search(r'(?:order\s*#?|#)(\w+)', lower_prompt)
    if "cancel" in lower_prompt and order_match:
        order_id = order_match.group(1)
        steps.append(PlanStep(
            action="cancel_order",
            parameters={"order_id": order_id}
        ))
        
    # Extract email if present
    email_match = re.search(r'([\w\.-]+@[\w\.-]+)', lower_prompt)
    if "email" in lower_prompt and email_match:
        email = email_match.group(1)
        
        # Simple message generation referencing order if available
        message = "Your request has been processed."
        if order_match:
            message = f"Your order #{order_match.group(1)} has been cancelled successfully."
            
        steps.append(PlanStep(
            action="send_email",
            parameters={"email": email, "message": message}
        ))
        
    # Default fallback
    if not steps:
        raise ValueError("Could not parse actionable steps from the prompt. Please mention an order to cancel and an email address.")
        
    return steps
