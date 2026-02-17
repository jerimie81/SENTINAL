from google.adk.agents import Agent
from google.adk.tools import google_search

root_agent = Agent(
    name="sentinel_adk_server",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant.",
    tools=[google_search]
)
