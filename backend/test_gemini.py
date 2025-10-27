"""Quick test script for Gemini API integration."""

import os
from src.api.gemini import GeminiClient
from src.api.client_factory import get_client
from src.api.model_registry import get_provider_for_model, get_api_model

def test_gemini_direct():
    """Test direct GeminiClient usage."""
    print("Testing direct GeminiClient...")
    
    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set in environment. Skipping direct test.")
        return False
    
    try:
        client = GeminiClient(api_key=api_key)
        print("✓ GeminiClient initialized successfully")
        
        # Test streaming
        print("\nTesting streaming with gemini-2.5-flash...")
        response_text = ""
        metadata = None
        
        stream = client.stream_completion(
            prompt="You are a helpful assistant.",
            model="gemini-2.5-flash",
            text_content="Say 'Hello from Gemini!' in exactly 5 words.",
            temperature=0.7,
            max_tokens=50,
        )
        
        for chunk in stream:
            if isinstance(chunk, str):
                response_text += chunk
                print(chunk, end="", flush=True)
            else:
                metadata = chunk
        
        print("\n")
        
        if metadata:
            print(f"✓ Response received: {len(response_text)} chars")
            print(f"  Input tokens: {metadata.get('input_tokens', 0)}")
            print(f"  Output tokens: {metadata.get('output_tokens', 0)}")
            print(f"  Cost: ${metadata.get('cost', 0):.6f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_model_registry():
    """Test model registry configuration."""
    print("\nTesting model registry...")
    
    test_models = [
        "gemini::gemini-2.5-flash",
        "gemini::gemini-2.5-pro",
        "gemini::gemini-2.5-flash-lite",
    ]
    
    for model in test_models:
        provider = get_provider_for_model(model)
        api_model = get_api_model(model)
        print(f"  {model}")
        print(f"    → Provider: {provider}")
        print(f"    → API model: {api_model}")
        
        if provider != "gemini":
            print(f"    ✗ Expected provider 'gemini', got '{provider}'")
            return False
    
    print("✓ Model registry configured correctly")
    return True

def test_client_factory():
    """Test client factory."""
    print("\nTesting client factory...")
    
    try:
        client = get_client("gemini::gemini-2.5-flash")
        print(f"  Client type: {type(client).__name__}")
        
        if type(client).__name__ != "GeminiClient":
            print(f"  ✗ Expected GeminiClient, got {type(client).__name__}")
            return False
        
        print("✓ Client factory returns correct client type")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Gemini API Integration Test")
    print("=" * 60)
    
    # Test registry first (doesn't need API key)
    test_model_registry()
    test_client_factory()
    
    # Test actual API call if key is available
    test_gemini_direct()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
