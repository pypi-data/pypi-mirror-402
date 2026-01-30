---
description: Standards for LLM integration, forbidding direct vendor SDK usage.
---
# Rule 02: LLM Integration Standards

This rule governs all AI/LLM capability integration code.

## 1. The ONLY Valid Entry Point
You **MUST** use the `my_llm_sdk` for all LLM interactions.

- **✅ Correct:**
  ```python
  from my_llm_sdk.client import LLMClient
  
  client = LLMClient(user_config_path=..., project_config_path=...)
  response = client.generate(prompt="Hello")
  ```

- **❌ PROHIBITED:**
  ```python
  import openai
  import google.generativeai
  import dashscope
  from langchain_openai import ChatOpenAI
  # Do not use HTTP requests to call LLM APIs directly
  ```

## 2. Model Configuration
- **NEVER** hardcode a specific model ID (e.g., `gpt-4`, `gemini-1.5-pro`) in your business logic.
- **ALWAYS** use the `model_alias` defined in `.context/project_env.yaml` or `llm.project.yaml` (e.g., `default`, `fast`, `complex`).

## 3. Recommended Patterns
- **Streaming**: Prefer `client.stream()` for user-facing interactions to reduce perceived latency.
- **Async**: Use `client.generate_async()` for batch processing or background tasks.
- **Budgeting**: Always ensure `project_config_path` is loaded so the SDK can enforce budget policies.

## 4. Error Handling
- Do not implement custom 429 retries. The SDK handles backoff.
- Do not implement custom cost tracking. The SDK handles ledgers.

---
**Enforcement**: Any code violating these imports or patterns must be rejected during review.
