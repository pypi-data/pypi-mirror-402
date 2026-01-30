
import wrapt
import uuid

class LiteLLMIntegration:
    @staticmethod
    def patch(client):
        try:
            import litellm
            # Patch litellm.completion
            wrapt.wrap_function_wrapper(
                litellm,
                "completion",
                _create_wrapper(client)
            )
            print("[Lightcurve] LiteLLM patched successfully.")
        except ImportError:
            pass
        except Exception as e:
            print(f"[Lightcurve] Error patching LiteLLM: {e}")

def _create_wrapper(lc_client):
    def wrapper(wrapped, instance, args, kwargs):
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        
        # Start Run
        agent_id = getattr(lc_client, 'default_agent_id', 'litellm-agent')
        run_id = str(uuid.uuid4())
        run = lc_client.start_run(agent_id=agent_id, run_id=run_id)
        
        run.log_input(user_input=str(messages))

        try:
            response = wrapped(*args, **kwargs)
            
            # LiteLLM normalizes responses to OpenAI format! Easy.
            choices = response.choices
            content = choices[0].message.content if choices else ""
            usage = response.usage
            
            run.log_tool(
                tool_name="litellm_completion",
                input={"model": model, "messages": messages},
                output={"content": content, "usage": usage.model_dump() if hasattr(usage, 'model_dump') else usage},
                success=True
            )
            
            run.log_output(content=content)
            
        except Exception as e:
            run.log_tool(
                 tool_name="litellm_completion", 
                 input={"model": model, "messages": messages},
                 output={"error": str(e)},
                 success=False
            )
            run.end()
            raise e
        
        run.end()
        return response

    return wrapper
