
import wrapt
import uuid

class GeminiIntegration:
    @staticmethod
    def patch(client):
        try:
            import google.generativeai as genai
            # Patch: google.generativeai.GenerativeModel.generate_content
            # This is the main entry point for most Gemini calls
            wrapt.wrap_function_wrapper(
                genai.GenerativeModel,
                "generate_content",
                _create_wrapper(client)
            )
            print("[Lightcurve] Gemini patched successfully.")
        except ImportError:
            pass
        except Exception as e:
            print(f"[Lightcurve] Error patching Gemini: {e}")

def _create_wrapper(lc_client):
    def wrapper(wrapped, instance, args, kwargs):
        # Args[0] might be content
        content_input = args[0] if len(args) > 0 else kwargs.get("contents", "")
        model_name = "gemini-unknown" 
        if hasattr(instance, 'model_name'):
             model_name = instance.model_name
        
        # Start Run
        agent_id = getattr(lc_client, 'default_agent_id', 'gemini-agent')
        run_id = str(uuid.uuid4())
        run = lc_client.start_run(agent_id=agent_id, run_id=run_id)
        
        run.log_input(user_input=str(content_input))

        try:
            response = wrapped(*args, **kwargs)
            
            # Gemini response handling is complex (streaming, etc.)
            # Assuming simple response object for now
            text_content = ""
            try:
                text_content = response.text
            except:
                text_content = "[Non-text or Safety Blocked]"

            # Usage extraction (if available in response candidates/metadata)
            usage = {}
            if hasattr(response, 'usage_metadata'):
                 usage = {
                     "prompt_token_count": response.usage_metadata.prompt_token_count,
                     "candidates_token_count": response.usage_metadata.candidates_token_count
                 }

            run.log_tool(
                tool_name="gemini_generate_content",
                input={"model": model_name, "contents": str(content_input)},
                output={"content": text_content, "usage": usage},
                success=True
            )
            
            run.log_output(content=text_content)
            
        except Exception as e:
            run.log_tool(
                 tool_name="gemini_generate_content", 
                 input={"model": model_name},
                 output={"error": str(e)},
                 success=False
            )
            run.end()
            raise e
        
        run.end()
        return response

    return wrapper
