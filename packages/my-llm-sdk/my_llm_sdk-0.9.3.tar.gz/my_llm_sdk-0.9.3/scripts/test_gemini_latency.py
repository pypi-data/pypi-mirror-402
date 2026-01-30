import asyncio
import time
from my_llm_sdk.client import LLMClient

def test_latency():
    client = LLMClient()
    prompt = "Reply with exactly 'Latency Test OK'"
    models = ["gemini-3.0-flash", "gemini-3.0-pro"]
    
    print(f"🚀 Testing Gemini 3.0 Latency Comparison...")
    print(f"{'Model':<20} | {'SDK Int.':<10} | {'Wall':<10} | {'Tokens':<6}")
    print("-" * 55)

    for model in models:
        try:
            t0 = time.time()
            response = client.generate(prompt, model_alias=model, full_response=True)
            t1 = time.time()
            
            total_wall_time = t1 - t0
            sdk_timing = response.timing.get("total", 0)
            
            print(f"{model:<20} | {sdk_timing:>8.3f}s | {total_wall_time:>8.3f}s | {response.usage.total_tokens:>6}")
            
        except Exception as e:
            print(f"❌ {model:<17} | Failed: {e}")

if __name__ == "__main__":
    test_latency()
