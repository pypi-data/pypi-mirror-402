"""
Basic usage example for TCBS SDK

⚠️ SECURITY WARNING:
- Replace placeholder values with your actual credentials
- Use environment variables for API keys
- Test with read-only operations first
"""

import os
from tcbs import TCBSClient, TCBSAuthError, TCBSAPIError


def main():
    # ✅ GOOD: Use environment variable
    api_key = os.getenv("TCBS_API_KEY")
    
    if not api_key:
        print("Error: TCBS_API_KEY environment variable not set")
        print("Set it with: export TCBS_API_KEY='your_api_key'")
        return
    
    # Initialize client
    client = TCBSClient(api_key=api_key)
    
    try:
        # Get account profile (read-only, safe to test)
        print("Fetching account profile...")
        profile = client.get_profile(
            custody_code="105C334455",  # Replace with your custody code
            fields="basicInfo,personalInfo"
        )
        print(f"Profile: {profile}")
        
        # Get purchasing power (read-only, safe to test)
        print("\nFetching purchasing power...")
        power = client.get_purchasing_power(
            account_no="0001170730"  # Replace with your account number
        )
        print(f"Purchasing power: {power}")
        
    except TCBSAuthError as e:
        print(f"Authentication error: {e}")
        print("Make sure your API key is correct and OTP is valid")
    except TCBSAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
