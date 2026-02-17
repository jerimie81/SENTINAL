import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner
from google.genai import types

# It's good practice to have the agent definition in a separate file.
# We are assuming the agent is defined in 'agent.py' and the main object is 'root_agent'.
from agent import root_agent

# Initialize the FastAPI app
app = FastAPI(
    title="Sentinel ADK Server",
    description="A local server to host the Sentinel ADK agent.",
    version="0.1.0",
)

# Initialize the InMemoryRunner with our agent
runner = InMemoryRunner(agent=root_agent)

# Define the request body model for the invoke endpoint
class InvokeRequest(BaseModel):
    message: str

# Define a simple root endpoint for a health check
@app.get("/")
def read_root():
    """A simple health check endpoint."""
    return {"status": "Sentinel ADK Server is running"}

# Define the main endpoint to interact with the agent
@app.post("/invoke")
async def invoke_agent(request: InvokeRequest):
    """
    Invokes the ADK agent with a user message and returns the agent's response.
    """
    try:
        # The run_debug method is for quick experimentation and returns a list of events.
        # We need to extract the final response content from these events.
        events = await runner.run_debug(request.message)
        
        final_response = "No response from agent."
        for event in events:
            if event.content and event.content.parts:
                # Assuming the last event with content is the final response.
                # In a real scenario, you might have more sophisticated logic
                # to determine the final response, e.g., checking event.is_final_response()
                # or content.role == 'model'.
                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
                        break # Take the first text part of the last content event
        
        return {"response": final_response}
    except Exception as e:
        return {"error": f"An unexpected error occurred during agent invocation: {e}"}

# Standard Python entry point to run the server
if __name__ == "__main__":
    # Run the server with uvicorn on localhost, port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

