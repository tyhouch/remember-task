import anthropic
import json
import asyncio
from typing import Dict, Any, List, Optional
import sys

class LLMService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-latest"
        self.system_prompt = """
        You are a helpful AI assistant with memory capabilities. You can remember information about users across conversations.
        
        Available memory tools:
        - add_memory: Store new information about the user
        - get_memory: Retrieve specific information by key
        - list_memories: List all stored memories
        - search_memories: Search for memories by content
        - update_memory: Update existing memories
        
        Use these tools when appropriate to provide a personalized experience. When you learn something important about the user
        that might be useful in future conversations (like their name, location, preferences, etc.), store it using add_memory.
        
        When the user introduces themselves or shares a name, ALWAYS use add_memory to store this information with key "name".
        When asked about what you know about the user, ALWAYS use list_memories.
        When asked about a specific piece of information (like "do you know my name?"), use get_memory with the appropriate key.
        
        Always be helpful, friendly, and respectful of user privacy.
        """
        self.memory_tools = [
            {
                "name": "add_memory",
                "description": "Store new information about the user. Use this when you learn important information that should be remembered for future conversations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "memory_type": {
                            "type": "string",
                            "description": "Category of memory (e.g., 'personal_info', 'preference')"
                        },
                        "key": {
                            "type": "string",
                            "description": "Unique identifier for this memory (e.g., 'name', 'location', 'favorite_color')"
                        },
                        "content": {
                            "type": "string",
                            "description": "The actual information to remember"
                        }
                    },
                    "required": ["memory_type", "key", "content"]
                }
            },
            {
                "name": "get_memory",
                "description": "Retrieve a specific memory by its key. Use this when you need to recall specific information about the user.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "The key of the memory to retrieve"
                        }
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "list_memories",
                "description": "List all stored memories about the user. Use this when you need an overview of what you know about the user.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "search_memories",
                "description": "Search memories by content. Use this when you want to find memories related to a specific topic.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search term to look for in memories"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "update_memory",
                "description": "Update an existing memory with new content. Use this when information about the user changes.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "The key of the memory to update"
                        },
                        "new_content": {
                            "type": "string",
                            "description": "The new content for this memory"
                        }
                    },
                    "required": ["key", "new_content"]
                }
            }
        ]
    
    async def generate_response(self, message: str, memory_service=None) -> str:
        """Generate a response using the LLM with tool support"""
        try:
            messages = [
                {"role": "user", "content": message}
            ]
            
            # Check for name patterns in the message to force memory storage
            name_mentioned = False
            name_value = None
            
            # Basic name detection
            if "I am " in message or "my name is " in message or "I'm " in message:
                parts = message.split("I am " if "I am " in message else "my name is " if "my name is " in message else "I'm ")
                if len(parts) > 1:
                    potential_name = parts[1].strip().split()[0].strip(".,!?")
                    name_mentioned = True
                    name_value = potential_name
                    print(f"Detected name: {name_value}", file=sys.stderr)
            
            # If name is detected, store it directly
            if name_mentioned and name_value and memory_service:
                try:
                    result = memory_service.add_memory(
                        "personal_info",
                        "name",
                        name_value
                    )
                    print(f"Pre-stored name memory: {result}", file=sys.stderr)
                except Exception as e:
                    print(f"Error pre-storing name: {str(e)}", file=sys.stderr)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=self.system_prompt,
                messages=messages,
                tools=self.memory_tools
            )
            
            print(f"Response stop reason: {response.stop_reason}", file=sys.stderr)
            
            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                # Get the tool use details
                tool_use = None
                for block in response.content:
                    if block.type == "tool_use":
                        tool_use = block
                        break
                
                if tool_use:
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    tool_use_id = tool_use.id
                    
                    print(f"Tool use requested: {tool_name} with input {tool_input}", file=sys.stderr)
                    
                    # Execute the appropriate tool function
                    tool_result = await self._execute_tool(tool_name, tool_input, memory_service)
                    print(f"Tool result: {tool_result}", file=sys.stderr)
                    
                    # Send the tool result back to Claude
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps(tool_result)
                            }
                        ]
                    })
                    
                    # Get Claude's final response that incorporates the tool result
                    final_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=1000,
                        system=self.system_prompt,
                        messages=messages,
                        tools=self.memory_tools
                    )
                    
                    return final_response.content[0].text
            
            return response.content[0].text
        except Exception as e:
            print(f"Error in generate_response: {str(e)}", file=sys.stderr)
            # In a real app, you'd want to log this
            return f"Error generating response: {str(e)}"
    
    async def stream_response(self, message: str, memory_service=None):
        """Stream a response from the LLM with tool support"""
        try:
            # Check for name patterns in the message to force memory storage
            name_mentioned = False
            name_value = None
            
            # Basic name detection 
            if "I am " in message or "my name is " in message or "I'm " in message:
                parts = message.split("I am " if "I am " in message else "my name is " if "my name is " in message else "I'm ")
                if len(parts) > 1:
                    potential_name = parts[1].strip().split()[0].strip(".,!?")
                    name_mentioned = True
                    name_value = potential_name
                    print(f"Detected name in streaming: {name_value}", file=sys.stderr)
            
            # If name is detected, store it directly
            if name_mentioned and name_value and memory_service:
                try:
                    result = memory_service.add_memory(
                        "personal_info",
                        "name",
                        name_value
                    )
                    print(f"Pre-stored name memory in streaming: {result}", file=sys.stderr)
                except Exception as e:
                    print(f"Error pre-storing name in streaming: {str(e)}", file=sys.stderr)
            
            # For simplicity, we'll use non-streaming for tool usage cases
            # This avoids complexity in handling streaming with tools
            # Stream is maintained only for the final response
            
            # First check if we need to use a tool
            messages = [
                {"role": "user", "content": message}
            ]
            
            # Get the initial response to check for tool use
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=self.system_prompt,
                messages=messages,
                tools=self.memory_tools
            )
            
            print(f"Streaming response stop reason: {response.stop_reason}", file=sys.stderr)
            
            # If tool use is needed, handle it non-streaming
            if response.stop_reason == "tool_use":
                # Get the tool use details
                tool_use = None
                for block in response.content:
                    if block.type == "tool_use":
                        tool_use = block
                        break
                
                if tool_use and memory_service:
                    # Extract tool details
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    tool_use_id = tool_use.id
                    
                    print(f"Tool use requested in streaming: {tool_name} with input {tool_input}", file=sys.stderr)
                    
                    # Execute the tool
                    tool_result = await self._execute_tool(tool_name, tool_input, memory_service)
                    print(f"Tool result in streaming: {tool_result}", file=sys.stderr)
                    
                    # Send the tool result back to Claude
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps(tool_result)
                            }
                        ]
                    })
                    
                    # Get the final response directly (non-streaming) first to avoid issues
                    final_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=1000,
                        system=self.system_prompt,
                        messages=messages,
                        tools=self.memory_tools
                    )
                    
                    # Now stream the pre-generated final response
                    yield "event: start\ndata: \n\n"
                    
                    for text_block in final_response.content:
                        if text_block.type == "text":
                            # Split the text into smaller chunks to simulate streaming
                            text = text_block.text
                            chunk_size = 10  # characters per chunk
                            for i in range(0, len(text), chunk_size):
                                chunk = text[i:i+chunk_size]
                                yield f"data: {json.dumps({'text': chunk})}\n\n"
                                await asyncio.sleep(0.01)
                    
                    yield "event: end\ndata: \n\n"
                    return
            
            # If no tool use, just stream the initial response
            yield "event: start\ndata: \n\n"
            
            # For non-tool use cases, stream the text directly
            for text_block in response.content:
                if text_block.type == "text":
                    # Split the text into smaller chunks to simulate streaming
                    text = text_block.text
                    chunk_size = 10  # characters per chunk
                    for i in range(0, len(text), chunk_size):
                        chunk = text[i:i+chunk_size]
                        yield f"data: {json.dumps({'text': chunk})}\n\n"
                        await asyncio.sleep(0.01)
            
            yield "event: end\ndata: \n\n"
                
        except Exception as e:
            print(f"Error in stream_response: {str(e)}", file=sys.stderr)
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            yield "event: end\ndata: \n\n"
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any], memory_service) -> Dict[str, Any]:
        """Execute the appropriate memory tool function"""
        if not memory_service:
            return {"error": "Memory service not available"}
            
        try:
            if tool_name == "add_memory":
                result = memory_service.add_memory(
                    tool_input.get("memory_type"),
                    tool_input.get("key"),
                    tool_input.get("content")
                )
                print(f"Add memory result: {result}", file=sys.stderr)
                return result
            elif tool_name == "get_memory":
                result = memory_service.get_memory(tool_input.get("key"))
                print(f"Get memory result: {result}", file=sys.stderr)
                return result
            elif tool_name == "list_memories":
                result = memory_service.list_memories()
                print(f"List memories result: {result}", file=sys.stderr)
                return result
            elif tool_name == "search_memories":
                result = memory_service.search_memories(tool_input.get("query"))
                print(f"Search memories result: {result}", file=sys.stderr)
                return result
            elif tool_name == "update_memory":
                result = memory_service.update_memory(
                    tool_input.get("key"),
                    tool_input.get("new_content")
                )
                print(f"Update memory result: {result}", file=sys.stderr)
                return result
            else:
                print(f"Unknown tool: {tool_name}", file=sys.stderr)
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            print(f"Error executing tool {tool_name}: {str(e)}", file=sys.stderr)
            return {"error": f"Error executing tool {tool_name}: {str(e)}"} 