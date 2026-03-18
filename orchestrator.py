from models import PlanStep
from tools import AVAILABLE_TOOLS
from typing import Dict, Any, List

class Orchestrator:
    async def execute_plan(self, plan: List[PlanStep]) -> Dict[str, Any]:
        """
        Executes a plan (list of steps) sequentially.
        If a step fails (e.g., cancel_order), short-circuits the rest of the plan.
        """
        results = []
        
        for i, step in enumerate(plan):
            if step.action not in AVAILABLE_TOOLS:
                return {
                    "status": "error",
                    "message": f"Unknown tool requested: {step.action}",
                    "steps_executed": results
                }
                
            tool_func = AVAILABLE_TOOLS[step.action]
            
            try:
                # Execute the tool asynchronously
                tool_result = await tool_func(**step.parameters)
                
                # Append execution record
                results.append({
                    "action": step.action,
                    "parameters": step.parameters,
                    "result": tool_result,
                    "status": "completed" if tool_result.get("success") else "failed"
                })
                
                # Guardrail: Check for failure based on the mock return schema
                if not tool_result.get("success", False):
                    # Identify remaining steps that will be skipped
                    skipped_steps = [s.action for s in plan[i+1:]]
                    skip_msg = f" Secondary tasks skipped: {', '.join(skipped_steps)}." if skipped_steps else ""
                    
                    return {
                        "status": "failed",
                        "message": f"Primary action '{step.action}' failed. Workflow halted.{skip_msg}",
                        "steps_executed": results
                    }
                    
            except Exception as e:
                # Handle unexpected runtime errors in tool
                results.append({
                    "action": step.action,
                    "parameters": step.parameters,
                    "result": {"success": False, "error": str(e)},
                    "status": "error"
                })
                return {
                    "status": "error",
                    "message": f"Exception encountered during '{step.action}': {str(e)}",
                    "steps_executed": results
                }
                
        # Successful full execution if the loop didn't short-circuit
        return {
            "status": "success",
            "message": "All steps executed successfully.",
            "steps_executed": results
        }
