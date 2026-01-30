"""
Market data examples for TCBS SDK

These are read-only operations and safe to test.
"""

import os
from tcbs import TCBSClient, TCBSAPIError


def main():
    api_key = os.getenv("TCBS_API_KEY")
    if not api_key:
        print("Error: Set TCBS_API_KEY environment variable")
        return
    
    client = TCBSClient(api_key=api_key)
    
    try:
        # Get market info for multiple tickers
        print("Fetching market info for FPT, VNM, HPG...")
        market_info = client.get_market_info(tickers="FPT,VNM,HPG")
        print(f"Market info: {market_info}\n")
        
        # Get price history
        print("Fetching price history for FPT...")
        history = client.get_price_history(ticker="FPT", page=0, size=10)
        print(f"Price history: {history}\n")
        
        # Get foreign room
        print("Fetching foreign room for VNINDEX...")
        foreign_room = client.get_foreign_room(index="VNINDEX")
        print(f"Foreign room: {foreign_room}")
        
    except TCBSAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
