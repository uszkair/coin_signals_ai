#!/usr/bin/env python3
"""
Script to list all active positions
"""

import sys
import os
import asyncio
import requests

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def list_positions():
    """List all active positions"""
    try:
        # Make request to live positions endpoint
        url = "http://localhost:8000/api/trading/live-positions"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                positions = data["data"]["positions"]
                
                print(f"\n📊 ACTIVE POSITIONS ({len(positions)})")
                print("=" * 60)
                
                if positions:
                    for pos in positions:
                        print(f"\n🔸 {pos['symbol']}")
                        print(f"  Side: {pos['position_side']}")
                        print(f"  Amount: {pos['position_amt']}")
                        print(f"  Entry Price: {pos['entry_price']}")
                        print(f"  Mark Price: {pos['mark_price']}")
                        print(f"  Unrealized PnL: {pos['unrealized_pnl']:.2f} USDT ({pos['pnl_percentage']:.2f}%)")
                        print(f"  Stop Loss: {pos['stop_loss_price'] if pos['stop_loss_price'] else 'NOT SET'}")
                        print(f"  Take Profit: {pos['take_profit_price'] if pos['take_profit_price'] else 'NOT SET'}")
                        print(f"  Leverage: {pos.get('leverage', 'N/A')}x")
                        
                        # Highlight missing stop loss/take profit
                        if not pos['stop_loss_price'] and not pos['take_profit_price']:
                            print(f"  ⚠️  WARNING: No stop loss or take profit set!")
                        elif not pos['stop_loss_price']:
                            print(f"  ⚠️  WARNING: No stop loss set!")
                        elif not pos['take_profit_price']:
                            print(f"  ⚠️  WARNING: No take profit set!")
                else:
                    print("No active positions found.")
                
                print(f"\nAccount Type: {data['data']['account_type']}")
                print(f"Testnet: {data['data']['testnet']}")
                
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(list_positions())