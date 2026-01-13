# from google.adk.agents.llm_agent import Agent

# root_agent = Agent(
#     name="greeting_agent",
#     model="gemini-2.5-flash",
#     description="Greeting agent that greets the user",
#     instructions="""
#     You are a helpful Assistant that greets the user,
#     Ask for the user's name and then greet them by name.
#     """
# )



from google.adk.agents import Agent

root_agent = Agent(
    name="greeting_agent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.5-flash", 
    description="Greeting agent",
    instruction="""
    You are a helpful assistant that greets the user. 
    Ask for the user's name and greet them by name.
    """,
)