import anthropic
import json
import asyncio

class LLMService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-latest"
    
    async def generate_response(self, message: str) -> str:
        """Generate a response using the LLM"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            return response.content[0].text
        except Exception as e:
            # In a real app, you'd want to log this
            return f"Error generating response: {str(e)}"
    
    async def stream_response(self, message: str):
        """Stream a response from the LLM"""
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": message}
                ]
            ) as stream:
                # Send the SSE headers
                yield "event: start\ndata: \n\n"
                
                for text in stream.text_stream:
                    # Format as SSE
                    yield f"data: {json.dumps({'text': text})}\n\n"
                    # Small delay to avoid overwhelming the client
                    await asyncio.sleep(0.01)
                
                # End of stream
                yield "event: end\ndata: \n\n"
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            yield "event: end\ndata: \n\n" 