
import wrapt
import uuid
from ..logger import logger

class AnthropicIntegration:
    @staticmethod
    def patch(client):
        try:
            import anthropic
            # Patch sync client: anthropic.resources.messages.Messages.create
            wrapt.wrap_function_wrapper(
                anthropic.resources.messages.Messages,
                "create",
                _create_wrapper(client)
            )
            logger.debug("Anthropic patched successfully.")
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Error patching Anthropic: {e}")

def _create_wrapper(lc_client):
    def wrapper(wrapped, instance, args, kwargs):
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        
        # Start Run (Auto)
        agent_id = getattr(lc_client, 'default_agent_id', 'anthropic-agent')
        run_id = str(uuid.uuid4())
        run = lc_client.start_run(agent_id=agent_id, run_id=run_id)
        
        run.log_input(user_input=str(messages))

        try:
            response = wrapped(*args, **kwargs)
            
            # Extract Content
            content = ""
            if hasattr(response, 'content') and len(response.content) > 0:
                if response.content[0].type == 'text':
                    content = response.content[0].text
            
            # Extract Usage
            usage = {}
            if hasattr(response, 'usage'):
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }

            run.log_tool(
                tool_name="anthropic_completion",
                input={"model": model, "messages": messages},
                output={"content": content, "usage": usage},
                success=True
            )
            
            run.log_output(content=content)
            
        except Exception as e:
            run.log_tool(
                 tool_name="anthropic_completion", 
                 input={"model": model, "messages": messages},
                 output={"error": str(e)},
                 success=False
            )
            run.end()
            raise e
        
        run.end()
        return response

    return wrapper
