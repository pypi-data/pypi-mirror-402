"""
OpenAI Function Calling Example
===============================

This example demonstrates using HyperX tools with OpenAI's function calling:
- Getting function definitions
- Calling functions from LLM responses
- Building a chat loop
"""

import json
from openai import OpenAI as OpenAIClient
from hyperx import HyperX
from hyperx.agents import create_tools

# Initialize clients
hyperx = HyperX("https://api.hyperxdb.dev", api_key="your-hyperx-api-key")
openai = OpenAIClient(api_key="your-openai-api-key")

# Create HyperX tools
tools = create_tools(hyperx, access_level="explore")

# ===================
# Get Function Definitions
# ===================

# Get OpenAI-compatible function definitions
functions = tools.get_openai_functions()

print("=== OpenAI Function Definitions ===")
for func in functions:
    print(f"  {func['name']}: {func['description'][:50]}...")

# Convert to OpenAI tools format
openai_tools = [
    {"type": "function", "function": func}
    for func in functions
]

# ===================
# Single Turn with Function Calling
# ===================

def chat_with_functions(user_message: str) -> str:
    """Send a message and handle function calls."""

    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to a knowledge graph. Use the available functions to answer questions."},
        {"role": "user", "content": user_message}
    ]

    # First API call
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=openai_tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message

    # Check if the model wants to call a function
    if assistant_message.tool_calls:
        messages.append(assistant_message)

        # Execute each function call
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"\n  Calling: {function_name}")
            print(f"  Args: {function_args}")

            # Execute the function
            result = tools.call_function(function_name, **function_args)

            # Add function result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result.data) if result.success else f"Error: {result.error}"
            })

        # Second API call with function results
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )

        return response.choices[0].message.content

    return assistant_message.content

# Test it
print("\n=== Single Turn Example ===")
result = chat_with_functions(
    "What entities are related to 'transformer architecture' in the knowledge graph?"
)
print(f"\nResponse: {result}")

# ===================
# Multi-Turn Chat Loop
# ===================

def chat_loop():
    """Interactive chat with function calling."""

    messages = [
        {"role": "system", "content": """You are a helpful assistant with access to a knowledge graph database.
Use the available functions to:
- Search for entities and concepts
- Find paths between entities
- Explore entity neighborhoods
- Explain relationships

Always use the functions when the user asks about knowledge in the graph."""}
    ]

    print("\n=== Interactive Chat (type 'quit' to exit) ===\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'quit':
            break

        messages.append({"role": "user", "content": user_input})

        # Get response with potential function calls
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # Handle function calls
        while assistant_message.tool_calls:
            messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"  [Calling {function_name}...]")

                result = tools.call_function(function_name, **function_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result.data) if result.success else f"Error: {result.error}"
                })

            # Get next response
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )
            assistant_message = response.choices[0].message

        # Add final response
        messages.append(assistant_message)
        print(f"\nAssistant: {assistant_message.content}\n")

# Run interactive loop (uncomment to use)
# chat_loop()

# ===================
# Parallel Function Calls
# ===================

def parallel_function_example():
    """Example of handling parallel function calls."""

    messages = [
        {"role": "system", "content": "You are a knowledge graph assistant."},
        {"role": "user", "content": "Compare the concepts 'BERT' and 'GPT' - search for both and explain their relationship"}
    ]

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=openai_tools,
        tool_choice="auto",
        parallel_tool_calls=True  # Enable parallel calls
    )

    assistant_message = response.choices[0].message

    if assistant_message.tool_calls:
        print(f"\n=== Parallel Function Calls ({len(assistant_message.tool_calls)} calls) ===")

        messages.append(assistant_message)

        # Execute all functions (could be parallelized with asyncio)
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"  Executing: {function_name}({function_args})")
            result = tools.call_function(function_name, **function_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result.data) if result.success else f"Error: {result.error}"
            })

        # Get final response
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages
        )

        print(f"\nFinal response: {response.choices[0].message.content[:500]}...")

parallel_function_example()

# ===================
# Streaming with Functions
# ===================

def streaming_with_functions(user_message: str):
    """Stream responses while handling function calls."""

    messages = [
        {"role": "system", "content": "You are a knowledge graph assistant."},
        {"role": "user", "content": user_message}
    ]

    print("\n=== Streaming Response ===")

    stream = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=openai_tools,
        stream=True
    )

    collected_calls = []
    current_call = {}

    for chunk in stream:
        delta = chunk.choices[0].delta

        # Handle function call chunks
        if delta.tool_calls:
            for tc in delta.tool_calls:
                if tc.index not in [c.get('index') for c in collected_calls]:
                    collected_calls.append({'index': tc.index, 'id': tc.id, 'name': '', 'arguments': ''})

                call = next(c for c in collected_calls if c['index'] == tc.index)
                if tc.function.name:
                    call['name'] = tc.function.name
                if tc.function.arguments:
                    call['arguments'] += tc.function.arguments

        # Handle content chunks
        if delta.content:
            print(delta.content, end="", flush=True)

    print()

    # Execute collected function calls
    if collected_calls:
        print(f"\n  [Executing {len(collected_calls)} function(s)...]")
        for call in collected_calls:
            args = json.loads(call['arguments'])
            result = tools.call_function(call['name'], **args)
            print(f"  {call['name']}: {'Success' if result.success else 'Failed'}")

streaming_with_functions("Find entities related to deep learning")
