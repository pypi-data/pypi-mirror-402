# Prerequisites:
# 1. Install package: pip install -e ..
# 2. Ollama: https://ollama.com/ (pull a model like 'llama3' or 'nemotron-3-nano')
# 3. LangSmith: Set LANGCHAIN_API_KEY environment variable.

import os
import uuid
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_middleware_notepad import NotePadMiddleware
from langchain_core.messages import HumanMessage

# 1. Enable LangSmith Tracing
# Ensure LANGCHAIN_API_KEY is set in your environment
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "NotepadMiddlewareBenchmark"


def main():
    print("--- Starting Notepad Middleware Benchmark ---")

    # 2. Initialize Model (Ollama)
    # Using 'nemotron-3-nano:30b-cloud' as a reasonable default, user can change if they have something else pulled
    llm = ChatOllama(model="nemotron-3-nano:30b-cloud", temperature=0)

    # 4. Create Agent
    # We pass an empty list of tools usually, but the middleware adds its own tools.
    # We can also add a dummy tool if we want, but not strictly necessary for this test.
    agent = create_agent(
        model=llm,
        tools=[],
        middleware=[NotePadMiddleware()],
    )

    # 5. Run the Agent
    # We give it a task that forces it to use the notepad tools.
    prompt = (
        "We are going to write a story together iteratively. "
        "Loop 20 times. For each loop/turn:"
        "\n1. Read the current notepad to see the story so far."
        "\n2. Write a NEW short paragraph continuing the story."
        "\n3. Append the new paragraph to the notepad."
        "\n4. Repeat until you have done this 20 times."
        "\nStart now. Provide the final full story at the end."
        "\nYou MUST actually call the tools 20 times."
    )
    
    # Since we want it to loop 20 times, we might need a higher recursion limit 
    # if it tries to do it all in one go or we might need to invoke it in a loop 
    # if the agent stops after one tool call. 
    # However, standard agents might stop after a few steps or hit max iterations.
    # Let's increase recursion limit just in case.
    
    response = agent.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        config={
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 100  # Allow enough steps for 20 loops (read+append = 40 steps minimum)
        }
    )

    print("\n--- Benchmark Finished ---")
    print("Final Agent Response:")
    # The response format depends on the agent type, but usually it's the final message content
    # or the full state. create_agent (LangGraph) returns the state.
    
    messages = response.get("messages", [])
    if messages:
        print(messages[-1].content)
    else:
        print(response)

if __name__ == "__main__":
    main()
