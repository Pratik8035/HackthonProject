import json
import logging
from fastapi import FastAPI, Header, Body, HTTPException
from agent import StrategicReserveAgent

# Suppress internal logging so it runs silently
logging.getLogger("src.optimization.optimizer").setLevel(logging.ERROR)

app = FastAPI(title="Strategic Reserve Optimization Agent API")
agent = StrategicReserveAgent()

@app.get("/")
def health_check():
    return {"status": "Agent API is running"}

@app.post("/optimize")
def optimize_api(
    agent_input_header: str = Header(None, alias="X-Agent-Input"),
    agent_input_body: dict = Body(None)
):
    """
    Agent call endpoint. 
    Accepts the strict runtime JSON payload either via the 'X-Agent-Input' HTTP header
    OR via a standard JSON request body.
    """
    input_data = None
    
    # 1. Check Header First (per specific user request)
    if agent_input_header:
        try:
            input_data = json.loads(agent_input_header)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in X-Agent-Input header")
            
    # 2. Fallback to Request Body
    elif agent_input_body:
        input_data = agent_input_body
        
    # 3. Fail if neither provided
    if not input_data:
        raise HTTPException(status_code=400, detail="Missing input data. Provide via Body or X-Agent-Input header.")
        
    # Run optimization
    try:
        recommendation = agent.optimize(input_data)
        
        # If the agent returned an error dict, pass it as a 400
        if "error" in recommendation:
            raise HTTPException(status_code=400, detail=recommendation["error"])
            
        return recommendation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
