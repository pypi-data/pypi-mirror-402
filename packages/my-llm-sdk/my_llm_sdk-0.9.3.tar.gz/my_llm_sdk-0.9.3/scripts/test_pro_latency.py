import asyncio
import time
from my_llm_sdk.client import LLMClient

def test_pro_latency():
    client = LLMClient()
    prompt = "Reply with exactly 'Latency Test OK'"
    model = "gemini-3.0-pro"
    
    print(f"🚀 Testing {model} Latency...")
    
    t0 = time.time()
    try:
        response = client.generate(prompt, model_alias=model, full_response=True)
        t1 = time.time()
        
        total_wall_time = t1 - t0
        sdk_timing = response.timing.get("total", 0)
        
        print("\n--- Latency Report ---")
        print(f"Content:      {response.content}")
        print(f"SDK Internal: {sdk_timing:.4f}s")
        print(f"Total Wall:   {total_wall_time:.4f}s")
        print(f"Tokens:       {response.usage.total_tokens}")
        print("----------------------")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pro_latency()
