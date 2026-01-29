"""
LangChain Integration Example
=============================

This example demonstrates using HyperX with LangChain:
- Creating a toolkit
- Building a ReAct agent
- Conversational RAG
"""

from hyperx import HyperX
from hyperx.agents.langchain import HyperXToolkit

# Requires: pip install hyperxdb[langchain]
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# ===================
# Creating the Toolkit
# ===================

# Create HyperX toolkit for LangChain
toolkit = HyperXToolkit(
    client=client,
    access_level="explore"  # read, explore, or full
)

# Get LangChain tools
tools = toolkit.get_tools()

print("=== HyperX LangChain Tools ===")
for tool in tools:
    print(f"  {tool.name}: {tool.description[:60]}...")

# ===================
# Building a ReAct Agent
# ===================

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Get the ReAct prompt
prompt = hub.pull("hwchase17/react")

# Create the agent
agent = create_react_agent(llm, tools, prompt)

# Create executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# ===================
# Running the Agent
# ===================

# Ask a question that requires graph exploration
response = agent_executor.invoke({
    "input": "What is the relationship between BERT and the Transformer architecture? "
             "Find the connection path and explain it."
})

print("\n=== Agent Response ===")
print(response["output"])

# ===================
# Multi-Turn Conversation
# ===================

from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Agent with memory
conversational_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)

# First question
response1 = conversational_agent.invoke({
    "input": "Find all papers about attention mechanisms"
})
print(f"\nQ1 Response: {response1['output'][:200]}...")

# Follow-up question (uses memory)
response2 = conversational_agent.invoke({
    "input": "Which of those papers has the most citations?"
})
print(f"\nQ2 Response: {response2['output'][:200]}...")

# ===================
# Custom Tool Configuration
# ===================

# Create toolkit with custom settings
custom_toolkit = HyperXToolkit(
    client=client,
    access_level="full",
    max_results=20,  # Limit search results
    include_quality_signals=True  # Include quality info in responses
)

custom_tools = custom_toolkit.get_tools()

# ===================
# Using with LangGraph
# ===================

# For more complex workflows, use LangGraph
try:
    from langgraph.graph import StateGraph, END

    # Define state
    class AgentState:
        messages: list
        entities: list
        paths: list

    # Create graph
    workflow = StateGraph(AgentState)

    def search_node(state):
        """Search for relevant entities."""
        search_tool = next(t for t in tools if t.name == "hyperx_search")
        result = search_tool.invoke({"query": state["messages"][-1]})
        return {"entities": result}

    def explore_node(state):
        """Explore entity relationships."""
        explore_tool = next(t for t in tools if t.name == "hyperx_explorer")
        results = []
        for entity in state["entities"][:3]:  # Top 3
            result = explore_tool.invoke({"entity_id": entity["id"], "depth": 2})
            results.append(result)
        return {"paths": results}

    workflow.add_node("search", search_node)
    workflow.add_node("explore", explore_node)

    workflow.set_entry_point("search")
    workflow.add_edge("search", "explore")
    workflow.add_edge("explore", END)

    app = workflow.compile()

    # Run workflow
    result = app.invoke({"messages": ["Find connections to transformer models"]})
    print("\n=== LangGraph Workflow Result ===")
    print(f"Found {len(result.get('entities', []))} entities")
    print(f"Explored {len(result.get('paths', []))} paths")

except ImportError:
    print("\nNote: Install langgraph for advanced workflows: pip install langgraph")

# ===================
# Streaming Responses
# ===================

# Stream agent responses
print("\n=== Streaming Response ===")
for chunk in agent_executor.stream({
    "input": "Explain the evolution of language models from RNNs to Transformers"
}):
    if "output" in chunk:
        print(chunk["output"], end="", flush=True)
print()
