
import wrapt
from contextlib import contextmanager
import uuid
from ..logger import logger

# Helper to track active run context (basic thread-local simulation for now)
# In production, use contextvars
_current_run_context = None

@contextmanager
def run_context(run):
    global _current_run_context
    prev = _current_run_context
    _current_run_context = run
    try:
        yield run
    finally:
        _current_run_context = prev

class OpenAIIntegration:
    @staticmethod
    def patch(client):
        try:
            import openai
            # Patch v1.x resources.chat.completions.create
            wrapt.wrap_function_wrapper(
                openai.resources.chat.completions.Completions,
                "create",
                _create_wrapper(client)
            )
            logger.debug("OpenAI patched successfully.")
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Error patching OpenAI: {e}")

def _create_wrapper(lc_client):
    def wrapper(wrapped, instance, args, kwargs):
        # 1. Capture Input
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        
        # Check if we are inside an existing Manual Run?
        # For this MVP, we assume every OpenAI call is a standalone unit 
        # unless a global context is active (future feature).
        
        # Start a Run (Implicitly)
        agent_id = getattr(lc_client, 'default_agent_id', 'openai-agent')
        run_id = str(uuid.uuid4())
        
        run = lc_client.start_run(agent_id=agent_id, run_id=run_id)
        
        # Log Input
        # Naively stringify messages for now
        run.log_input(user_input=str(messages))

        # 2. Call Original Function
        try:
            response = wrapped(*args, **kwargs)
        except Exception as e:
            # Capture Error
            run.log_tool(
                 tool_name="openai_completion", 
                 input={"model": model, "messages": messages},
                 output={"error": str(e)},
                 success=False
            )
            run.end()
            raise e

        # 3. Capture Output
        try:
            choices = response.choices
            content = choices[0].message.content if choices else ""
            usage = response.usage
            
            # Log Tool/LLM Call Details
            run.log_tool(
                tool_name="openai_completion",
                input={"model": model, "messages": messages},
                output={"content": content, "usage": usage.model_dump() if usage else {}},
                success=True
            )
            
            # Log Final Output
            run.log_output(content=content)
            
        except Exception as e:
             logger.error(f"Error parsing OpenAI response: {e}")
        
        run.end()
        return response

    return wrapper
