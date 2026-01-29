"""
LlamaIndex Integration Example
==============================

This example demonstrates using HyperX with LlamaIndex:
- Creating a tool spec
- Building an agent
- Query engine integration
"""

from hyperx import HyperX
from hyperx.agents.llamaindex import HyperXToolSpec

# Requires: pip install hyperxdb[llamaindex]
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# ===================
# Creating Tool Spec
# ===================

# Create HyperX tool specification for LlamaIndex
tool_spec = HyperXToolSpec(
    client=client,
    access_level="explore"
)

# Get LlamaIndex tools
tools = tool_spec.to_tool_list()

print("=== HyperX LlamaIndex Tools ===")
for tool in tools:
    print(f"  {tool.metadata.name}: {tool.metadata.description[:60]}...")

# ===================
# Building a ReAct Agent
# ===================

# Configure LLM
Settings.llm = OpenAI(model="gpt-4", temperature=0)

# Create agent
agent = ReActAgent.from_tools(
    tools,
    verbose=True
)

# ===================
# Running the Agent
# ===================

# Ask a question
response = agent.chat(
    "What are the key concepts related to attention mechanisms in deep learning? "
    "Find the connections between them."
)

print("\n=== Agent Response ===")
print(response)

# ===================
# Multi-Turn Chat
# ===================

# Continue the conversation
response2 = agent.chat(
    "Can you find papers that discuss these concepts?"
)
print(f"\nFollow-up: {response2}")

# Reset chat history
agent.reset()

# ===================
# Using with Query Engine
# ===================

from llama_index.core import VectorStoreIndex, Document
from llama_index.core.tools import QueryEngineTool

# Create a simple index (for comparison)
documents = [
    Document(text="Transformers use self-attention mechanisms..."),
    Document(text="BERT is a bidirectional transformer model..."),
]
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# Combine HyperX tools with a query engine tool
query_tool = QueryEngineTool.from_defaults(
    query_engine,
    name="document_search",
    description="Search through local documents"
)

# Agent with both HyperX and document tools
combined_tools = tools + [query_tool]
combined_agent = ReActAgent.from_tools(combined_tools, verbose=True)

response = combined_agent.chat(
    "Compare what the local documents say about transformers with "
    "the knowledge graph information"
)
print(f"\n=== Combined Agent Response ===")
print(response)

# ===================
# Streaming
# ===================

print("\n=== Streaming Response ===")
streaming_response = agent.stream_chat(
    "Explain the relationship between BERT, GPT, and the original Transformer"
)
for token in streaming_response.response_gen:
    print(token, end="", flush=True)
print()

# ===================
# Function Calling Agent
# ===================

from llama_index.agent.openai import OpenAIAgent

# OpenAI function calling agent (more structured)
openai_agent = OpenAIAgent.from_tools(
    tools,
    verbose=True
)

response = openai_agent.chat(
    "Find all entities related to 'neural networks' and their connections"
)
print(f"\n=== OpenAI Agent Response ===")
print(response)

# ===================
# Custom Tool Spec
# ===================

# Create with custom settings
custom_spec = HyperXToolSpec(
    client=client,
    access_level="full",
    include_quality_signals=True,
    max_search_results=25
)

# Get specific tools only
search_tool = custom_spec.get_tool("search")
paths_tool = custom_spec.get_tool("paths")

# Use tools directly
search_result = search_tool("machine learning algorithms")
print(f"\n=== Direct Tool Usage ===")
print(f"Search found: {len(search_result.get('entities', []))} entities")

# ===================
# With Quality Signals
# ===================

# The tool responses include quality signals for agent decision-making
result = custom_spec.search(
    query="transformer architecture",
    limit=10
)

print(f"\n=== Quality Signals ===")
print(f"Confidence: {result.quality.confidence}")
print(f"Should retrieve more: {result.quality.should_retrieve_more}")
if result.quality.suggested_refinements:
    print(f"Suggestions: {result.quality.suggested_refinements}")
