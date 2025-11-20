#!/usr/bin/env python3
"""
Test script to verify DCF Model setup
"""

import os
import sys

def test_setup():
    """Test if the environment is properly configured"""

    print("=" * 60)
    print("DCF Model Setup Test")
    print("=" * 60)
    print()

    all_passed = True

    # Test 1: Check Python version
    print("1. Checking Python version...")
    if sys.version_info >= (3, 7):
        print(f"   [OK] Python {sys.version_info.major}.{sys.version_info.minor} detected")
    else:
        print(f"   [ERROR] Python {sys.version_info.major}.{sys.version_info.minor} detected (3.7+ required)")
        all_passed = False
    print()

    # Test 2: Check dependencies
    print("2. Checking dependencies...")
    try:
        import flask
        print(f"   [OK] Flask {flask.__version__} installed")
    except ImportError:
        print("   [ERROR] Flask not installed (run: pip install flask)")
        all_passed = False

    try:
        import requests
        print(f"   [OK] Requests {requests.__version__} installed")
    except ImportError:
        print("   [ERROR] Requests not installed (run: pip install requests)")
        all_passed = False
    print()

    # Test 3: Check API key
    print("3. Checking Alpha Vantage API key...")
    api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    if api_key:
        print(f"   [OK] API key is set: {api_key[:10]}...")
        print()

        # Test 4: Try API call
        print("4. Testing API connection...")
        try:
            import requests
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": "AAPL",
                    "apikey": api_key
                },
                timeout=10
            )
            data = response.json()

            if "Global Quote" in data:
                print("   [OK] Successfully connected to Alpha Vantage API")
                price = data["Global Quote"].get("05. price", "N/A")
                print(f"   [OK] Test query returned AAPL price: ${price}")
            elif "Note" in data:
                print("   [WARNING] API rate limit reached (wait a minute)")
                print(f"   Message: {data['Note']}")
            elif "Error Message" in data:
                print(f"   [ERROR] API error: {data['Error Message']}")
                all_passed = False
            else:
                print(f"   [WARNING] Unexpected response: {data}")
        except Exception as e:
            print(f"   [ERROR] Failed to connect: {str(e)}")
            all_passed = False
    else:
        print("   [ERROR] ALPHAVANTAGE_API_KEY environment variable is not set")
        print()
        print("   To fix this, run:")
        print("   Windows PowerShell:  $env:ALPHAVANTAGE_API_KEY=\"your_key\"")
        print("   Windows CMD:         set ALPHAVANTAGE_API_KEY=your_key")
        print("   Mac/Linux:           export ALPHAVANTAGE_API_KEY=\"your_key\"")
        print()
        print("   Get a free key at: https://www.alphavantage.co/support/#api-key")
        all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed! You're ready to run the DCF model.")
        print()
        print("Start the application with: python dcf_model.py")
        print("Then open your browser to: http://localhost:5000")
    else:
        print("[FAILED] Some tests failed. Please fix the issues above.")
    print("=" * 60)

    return all_passed

if __name__ == '__main__':
    success = test_setup()
    sys.exit(0 if success else 1)
