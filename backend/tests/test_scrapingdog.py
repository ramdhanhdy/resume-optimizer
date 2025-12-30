"""Quick test script for ScrapingDog LinkedIn profile fetching."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.api.scrapingdog_client import (
    fetch_linkedin_profile,
    fetch_linkedin_profile_text,
    _extract_linkedin_username,
)

def test_username_extraction():
    """Test LinkedIn username extraction from various formats."""
    test_cases = [
        ("ramdhanhdy", "ramdhanhdy"),
        ("https://www.linkedin.com/in/ramdhanhdy", "ramdhanhdy"),
        ("https://linkedin.com/in/ramdhanhdy/", "ramdhanhdy"),
        ("linkedin.com/in/john-doe", "john-doe"),
        ("https://www.linkedin.com/in/jane-smith-123456/", "jane-smith-123456"),
    ]
    
    print("Testing username extraction...")
    for input_val, expected in test_cases:
        result = _extract_linkedin_username(input_val)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{input_val}' -> '{result}' (expected: '{expected}')")
    print()


def test_fetch_profile():
    """Test actual API call (requires SCRAPINGDOG_API_KEY)."""
    api_key = os.getenv("SCRAPINGDOG_API_KEY")
    if not api_key:
        print("⚠️ SCRAPINGDOG_API_KEY not set - skipping API test")
        return
    
    print("Testing LinkedIn profile fetch...")
    print("Note: This may take 1-3 minutes if the profile needs to be scraped fresh.")
    print()
    
    try:
        # Test with a username
        profile_text = fetch_linkedin_profile_text(
            "ramdhanhdy",
            max_retries=5,
            initial_delay=30.0,
        )
        print(f"✅ Profile fetched successfully!")
        print(f"   Length: {len(profile_text)} characters")
        print(f"\n--- Profile Preview (first 500 chars) ---")
        print(profile_text[:500])
        print("...")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_username_extraction()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        test_fetch_profile()
    else:
        print("Run with --api flag to test actual API call:")
        print("  python test_scrapingdog.py --api")
