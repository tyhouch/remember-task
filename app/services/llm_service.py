import anthropic
import json
import asyncio
import datetime

class LLMService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-latest"

       
        self.system_prompt = """You are an AI assistant. Just be chill. Dont tell people what tools you have access to unless they ask."""
        
      
        self.tools = [
            {
                "name": "get_current_time",
                "description": "Get the current time",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def get_current_time(self):
        """Return the current time in readable format"""
        current_time = datetime.datetime.now().strftime("%H:%M on %B %d, %Y")
        return {"time": current_time}
    
    async def stream_response(self, message: str):
        """Stream a response from the LLM with tool use support"""
        try:
            # Start the SSE response
            yield "event: start\ndata: \n\n"
            
            # STEP 1: Send the initial request with tools - non-streaming first
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": message}
                ],
                tools=self.tools
            )
            
            # Check if the response indicates tool use
            if response.stop_reason == "tool_use":
                # Find the tool use block
                tool_use = None
                for content in response.content:
                    if content.type == "tool_use":
                        tool_use = content
                        break
                
                if tool_use:
                    # STEP 3: Process the tool call
                    tool_result = None
                    if tool_use.name == "get_current_time":
                        tool_result = self.get_current_time()
                    
                    # STEP 4: Send the result back and get final response
                    final_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=1000,
                        system=self.system_prompt,
                        messages=[
                            {"role": "user", "content": message},
                            {"role": "assistant", "content": [
                                {"type": "tool_use", "id": tool_use.id, "name": tool_use.name, "input": tool_use.input}
                            ]},
                            {"role": "user", "content": [
                                {"type": "tool_result", "tool_use_id": tool_use.id, "content": json.dumps(tool_result)}
                            ]}
                        ]
                    )
                    
                    # Stream the final response
                    for content in final_response.content:
                        if content.type == "text":
                            yield f"data: {json.dumps({'text': content.text})}\n\n"
            else:
                # Just stream the regular response
                for content in response.content:
                    if content.type == "text":
                        yield f"data: {json.dumps({'text': content.text})}\n\n"
            
            # End of stream
            yield "event: end\ndata: \n\n"
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            yield "event: end\ndata: \n\n" 