#!/usr/bin/env python3
"""
Script to check Gemini model capabilities and token limits
"""

import google.generativeai as genai
import os
from config import Config

def check_model_limits():
    """Check available models and their token limits"""
    config = Config()
    genai.configure(api_key=config.gemini_api_key)
    
    print("=== Available Gemini Models ===")
    try:
        models = genai.list_models()
        for model in models:
            print(f"\nModel: {model.name}")
            print(f"Display Name: {model.display_name}")
            print(f"Description: {model.description}")
            
            # Check if model has input/output token limits
            if hasattr(model, 'input_token_limit'):
                print(f"Input Token Limit: {model.input_token_limit:,}")
            if hasattr(model, 'output_token_limit'):
                print(f"Output Token Limit: {model.output_token_limit:,}")
            
            # Check supported generation methods
            if hasattr(model, 'supported_generation_methods'):
                print(f"Supported Methods: {model.supported_generation_methods}")
                
            print("-" * 50)
            
    except Exception as e:
        print(f"Error fetching models: {e}")

def test_generation_config():
    """Test different generation configurations to understand limits"""
    config = Config()
    genai.configure(api_key=config.gemini_api_key)
    
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    print(f"\n=== Testing Generation Config for {model_name} ===")
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Test with different max_output_tokens values
        test_values = [1000, 2000, 4000, 8000, 16000, 32000]
        
        for max_tokens in test_values:
            try:
                config = genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7
                )
                
                # Try to create the config (this will fail if tokens exceed limit)
                print(f"✓ max_output_tokens={max_tokens:,} - Config created successfully")
                
                # Optionally test with a simple prompt
                response = model.generate_content(
                    ["What is AI?"], 
                    generation_config=config
                )
                print(f"  - Generation test passed")
                
            except Exception as e:
                print(f"✗ max_output_tokens={max_tokens:,} - Error: {str(e)}")
                
    except Exception as e:
        print(f"Error testing generation config: {e}")

def check_quota_usage():
    """Check current API quota usage (if available)"""
    print("\n=== Quota Information ===")
    print("For detailed quota usage, check:")
    print("1. Google Cloud Console: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas")
    print("2. Google AI Studio: https://aistudio.google.com/")
    print("3. Your Google Cloud project's API dashboard")

if __name__ == "__main__":
    print("Checking Gemini API Model Limits and Capabilities")
    print("=" * 60)
    
    check_model_limits()
    test_generation_config()
    check_quota_usage()
