"""
LLM Monitoring Wrapper

Automatically tracks LLM API calls (tokens, cost, latency, errors).
"""

import time
import functools


class LLMMonitor:
    """
    Wraps an LLM client to automatically send check-ins to FailSense AI Tracer.
    Captures metadata (tokens, cost, latency) by default.
    Captures full context (prompts, responses) only on errors.
    """
    
    def __init__(self, client, fs_client, tracer_id):
        self._client = client
        self._fs_client = fs_client
        self._tracer_id = tracer_id
        
    def __getattr__(self, name):
        original = getattr(self._client, name)
        if name == "chat":
            return ChatWrapper(original, self._fs_client, self._tracer_id)
        return original


class ChatWrapper:
    """Wraps chat interface."""
    
    def __init__(self, chat_obj, fs_client, tracer_id):
        self._chat_obj = chat_obj
        self._fs_client = fs_client
        self._tracer_id = tracer_id

    def __getattr__(self, name):
        original = getattr(self._chat_obj, name)
        if name == "completions":
            return CompletionsWrapper(original, self._fs_client, self._tracer_id)
        return original


class CompletionsWrapper:
    """Wraps completions interface and tracks API calls."""
    
    def __init__(self, completions_obj, fs_client, tracer_id):
        self._completions_obj = completions_obj
        self._fs_client = fs_client
        self._tracer_id = tracer_id

    def __getattr__(self, name):
        original = getattr(self._completions_obj, name)
        if name == "create":
            return self._wrap_create(original)
        return original

    def _wrap_create(self, original_create):
        @functools.wraps(original_create)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            
            response = None
            metadata = {}
            usage = {}
            status = "ok"
            
            try:
                response = original_create(*args, **kwargs)
                
                if hasattr(response, "usage") and response.usage:
                    usage = {
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                
            except Exception as e:
                status = "error"
                usage = {}
                
                metadata = {
                    "error": str(e),
                    "model": model,
                    "input": messages,
                    "error_type": type(e).__name__
                }
                
                raise e
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                
                cost_micro_cents = self._calculate_cost(model, usage)
                
                checkin_data = {
                    "status": status,
                    "metadata": metadata,
                    "duration_ms": duration_ms,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "model_name": model,
                    "estimated_cost": cost_micro_cents
                }
                
                self._fs_client.checkin_ai_tracer(self._tracer_id, checkin_data)
            
            return response
                
        return wrapper

    def _calculate_cost(self, model: str, usage: dict) -> int:
        """
        Calculate estimated cost in micro-cents.
        
        Returns:
            Cost in micro-cents (1/1,000,000 of a dollar)
        """
        if not usage:
            return 0
            
        m = model.lower()
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        
        if "gpt-4" in m:
            return int((inp * 30 + out * 60) / 1000)
        elif "gpt-3.5" in m:
            return int((inp * 0.5 + out * 1.5) / 1000)
        elif "claude-3-opus" in m:
            return int((inp * 15 + out * 75) / 1000)
        elif "gemini" in m:
            return int((inp * 0.125 + out * 0.375) / 1000)
        
        return 0
