from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class UserRequest(BaseModel):
    prompt: str = Field(..., description="Natural language request")

class AgentResponse(BaseModel):
    status: str
    message: str
    steps_executed: List[Dict[str, Any]]

class PlanStep(BaseModel):
    action: str = Field(..., description="The name of the tool to call. E.g. 'cancel_order' or 'send_email'")
    parameters: Dict[str, Any] = Field(..., description="The parameters for the tool call")
