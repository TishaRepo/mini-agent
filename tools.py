import asyncio
import random

async def cancel_order(order_id: str) -> dict:
    """Mock asynchronous tool to cancel an order."""
    # Simulate a network call
    await asyncio.sleep(0.5)
    
    # Simulate a 20% failure rate
    if random.random() < 0.2:
        return {"success": False, "error": f"Failed to cancel order {order_id}. System timeout."}
    
    return {"success": True, "message": f"Order {order_id} successfully cancelled."}

async def send_email(email: str, message: str) -> dict:
    """Mock asynchronous tool to send an email."""
    # Simulate sending an email (async sleep for 1 sec)
    await asyncio.sleep(1.0)
    
    return {"success": True, "message": f"Email sent to {email}."}

# Map string tool names to actual functions for the Orchestrator
AVAILABLE_TOOLS = {
    "cancel_order": cancel_order,
    "send_email": send_email
}
