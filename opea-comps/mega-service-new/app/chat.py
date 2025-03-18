from typing import Dict, Any, Optional
from fastapi import Request, FastAPI, HTTPException
from comps import ServiceOrchestrator, MicroService
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest, 
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo
)
from comps.cores.proto.docarray import LLMParams
import uvicorn
import logging

logger = logging.getLogger(__name__)

class ChatServiceError(Exception):
    """Base exception for Chat service"""
    pass

class Chat:
    """
    Chat service implementation using OPEA framework.
    
    Handles chat completion requests through a REST API interface.
    """
    
    def __init__(self) -> None:
        self.megaservice: ServiceOrchestrator = ServiceOrchestrator()
        self.endpoint: str = '/v1/chat/completions'
        self.host: str = '0.0.0.0'
        self.port: int = 8889
        self.app: FastAPI = FastAPI()
        
    def add_remote_services(self) -> None:
        """Configure and add remote LLM service to the orchestrator."""
        llm = MicroService(
            name="llm",
            host="0.0.0.0",
            port=9000,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type="LLM",
        )
        self.megaservice.add(llm)
        
    async def handle_request(self, request: Request) -> ChatCompletionResponse:
        """
        Handle incoming chat completion requests.
        
        Args:
            request: FastAPI Request object containing chat completion parameters
            
        Returns:
            ChatCompletionResponse with generated text and usage statistics
            
        Raises:
            HTTPException: If request processing fails
        """
        try:
            data = await request.json()
            chat_request = ChatCompletionRequest.model_validate(data)
            
            stream_opt = data.get("stream", False)
            
            parameters = LLMParams(
                max_tokens=chat_request.max_tokens or 1024,
                top_k=chat_request.top_k or 10,
                top_p=chat_request.top_p or 0.95,
                temperature=chat_request.temperature or 0.01,
                frequency_penalty=chat_request.frequency_penalty or 0.0,
                presence_penalty=chat_request.presence_penalty or 0.0,
            )
            
            initial_inputs = {
                "messages": chat_request.messages,
            }
            
            result_dict, runtime_graph = await self.megaservice.schedule(
                initial_inputs=initial_inputs,
                llm_parameters=parameters
            )
            
            response = "This is a test response"  # TODO: Implement actual response processing
            
            choices = [
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response),
                    finish_reason="stop",
                )
            ]
            
            usage = UsageInfo(
                prompt_tokens=len(str(chat_request.messages)),
                completion_tokens=len(response),
                total_tokens=len(str(chat_request.messages)) + len(response)
            )
            
            return ChatCompletionResponse(
                model=chat_request.model,
                choices=choices,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"Chat request processing failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
            
    def start(self) -> None:
        """Start the FastAPI server with configured routes."""
        self.app.post(self.endpoint)(self.handle_request)
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port
        )

if __name__ == '__main__':
    logger.info('Starting Chat service...')
    chat = Chat()
    chat.add_remote_services()
    chat.start()