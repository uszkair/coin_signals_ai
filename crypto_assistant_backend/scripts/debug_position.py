#!/usr/bin/env python3
"""
Debug script to check position and orders for a specific symbol
"""

import sys
import os
import asyncio
import requests

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def debug_position(symbol: str):
    """Debug position and orders for a symbol"""
    try:
        # Make request to debug endpoint
        url = f"http://localhost:8000/api/trading/debug-position/{symbol}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                debug_info = data["data"]
                
                print(f"\n🔍 DEBUG INFO FOR {symbol}")
                print("=" * 50)
                
                # Position info
                if debug_info["position_info"]:
                    pos = debug_info["position_info"]
                    print(f"\n📊 POSITION:")
                    print(f"  Symbol: {pos['symbol']}")
                    print(f"  Amount: {pos['positionAmt']}")
                    print(f"  Side: {'LONG' if pos['positionAmt'] > 0 else 'SHORT'}")
                    print(f"  Entry Price: {pos['entryPrice']}")
                    print(f"  Mark Price: {pos['markPrice']}")
                    print(f"  Unrealized PnL: {pos['unRealizedProfit']}")
                    print(f"  Leverage: {pos['leverage']}x")
                else:
                    print(f"\n❌ NO ACTIVE POSITION FOUND FOR {symbol}")
                    return
                
                # Open orders
                print(f"\n📋 OPEN ORDERS ({len(debug_info['open_orders'])}):")
                if debug_info["open_orders"]:
                    for order in debug_info["open_orders"]:
                        print(f"  Order ID: {order['orderId']}")
                        print(f"    Type: {order['type']}")
                        print(f"    Side: {order['side']}")
                        print(f"    Price: {order['price']}")
                        print(f"    Stop Price: {order['stopPrice']}")
                        print(f"    Quantity: {order['origQty']}")
                        print(f"    Reduce Only: {order['reduceOnly']}")
                        print(f"    Status: {order['status']}")
                        print()
                else:
                    print("  No open orders found")
                
                # Analysis
                if debug_info["analysis"]:
                    analysis = debug_info["analysis"]
                    print(f"\n🔬 ANALYSIS:")
                    print(f"  Position Side: {analysis['position_side']}")
                    print(f"  Entry Price: {analysis['entry_price']}")
                    print(f"  Stop Loss Found: {analysis['stop_loss_found']}")
                    print(f"  Take Profit Found: {analysis['take_profit_found']}")
                    
                    if analysis["stop_loss_candidates"]:
                        print(f"\n🛑 STOP LOSS CANDIDATES:")
                        for sl in analysis["stop_loss_candidates"]:
                            print(f"    Order {sl['orderId']}: {sl['type']} {sl['side']} @ {sl['trigger_price']}")
                            print(f"      Reason: {sl['reason']}")
                    
                    if analysis["take_profit_candidates"]:
                        print(f"\n🎯 TAKE PROFIT CANDIDATES:")
                        for tp in analysis["take_profit_candidates"]:
                            print(f"    Order {tp['orderId']}: {tp['type']} {tp['side']} @ {tp['trigger_price']}")
                            print(f"      Reason: {tp['reason']}")
                    
                    if not analysis["stop_loss_found"] and not analysis["take_profit_found"]:
                        print(f"\n⚠️  NO STOP LOSS OR TAKE PROFIT ORDERS FOUND!")
                        print(f"    This might be why they don't show up in the UI.")
                
                # Recent orders
                if debug_info["all_orders_last_24h"]:
                    print(f"\n📜 RECENT ORDERS (Last 10):")
                    for order in debug_info["all_orders_last_24h"]:
                        print(f"  {order['time']}: {order['type']} {order['side']} - {order['status']}")
                        if order['stopPrice']:
                            print(f"    Stop Price: {order['stopPrice']}")
                        if order['price']:
                            print(f"    Price: {order['price']}")
                
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_position.py <SYMBOL>")
        print("Example: python debug_position.py BTCUSDT")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    asyncio.run(debug_position(symbol))