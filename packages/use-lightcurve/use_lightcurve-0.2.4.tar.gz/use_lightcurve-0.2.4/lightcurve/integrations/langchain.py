
import wrapt
import uuid

class LangChainIntegration:
    @staticmethod
    def patch(client):
        try:
            import langchain.chat_models.base
            # Patch BaseChatModel.invoke (synchronous)
            # This covers ChatOpenAI.invoke, ChatAnthropic.invoke, etc.
            wrapt.wrap_function_wrapper(
                langchain.chat_models.base.BaseChatModel,
                "invoke",
                _create_wrapper(client)
            )
            print("[Lightcurve] LangChain patched successfully.")
        except ImportError:
            pass
        except Exception as e:
            print(f"[Lightcurve] Error patching LangChain: {e}")

def _create_wrapper(lc_client):
    def wrapper(wrapped, instance, args, kwargs):
        # LangChain invoke(input, config=None, **kwargs)
        input_val = args[0] if len(args) > 0 else kwargs.get("input")
        
        # Start Run
        agent_id = getattr(lc_client, 'default_agent_id', 'langchain-agent')
        run_id = str(uuid.uuid4())
        run = lc_client.start_run(agent_id=agent_id, run_id=run_id)
        
        # Input might be a string or list of messages
        run.log_input(user_input=str(input_val))

        try:
            response = wrapped(*args, **kwargs)
            
            # Request output content
            # AIMessage(content='...')
            content = ""
            if hasattr(response, 'content'):
                content = response.content
            
            # Usage
            usage = {}
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})

            run.log_tool(
                tool_name="langchain_invoke",
                input={"input": str(input_val)},
                output={"content": content, "usage": usage},
                success=True
            )
            
            run.log_output(content=content)
            
        except Exception as e:
            run.log_tool(
                 tool_name="langchain_invoke", 
                 input={"input": str(input_val)},
                 output={"error": str(e)},
                 success=False
            )
            run.end()
            raise e
        
        run.end()
        return response

    return wrapper
