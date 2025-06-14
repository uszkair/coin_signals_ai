#!/usr/bin/env python3
"""
Check ETHUSDT position details directly from Binance API
"""

import os
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_eth_position():
    """Check ETHUSDT position details"""
    try:
        # Get API credentials for testnet
        api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
        api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")
        
        if not api_key or not api_secret:
            print("❌ No Binance testnet API credentials found")
            return
        
        # Initialize client
        client = Client(api_key=api_key, api_secret=api_secret, testnet=True)
        
        # Get ETHUSDT position
        positions = client.futures_position_information(symbol='ETHUSDT')
        
        for pos in positions:
            position_amt = float(pos.get('positionAmt', 0))
            if position_amt != 0:
                print("🔍 ETHUSDT Position Details:")
                print(f"   Position Amount: {position_amt} ETH")
                print(f"   Entry Price: {pos.get('entryPrice')} USDT")
                print(f"   Mark Price: {pos.get('markPrice')} USDT")
                print(f"   Unrealized PnL: {pos.get('unRealizedProfit')} USDT")
                print(f"   Leverage: {pos.get('leverage')}x")
                print(f"   Margin Type: {pos.get('marginType')}")
                print(f"   Update Time: {pos.get('updateTime')}")
                
                # Calculate expected PnL manually
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                manual_pnl = position_amt * (mark_price - entry_price)
                
                print(f"\n📊 Manual Calculation:")
                print(f"   {position_amt} ETH × ({mark_price} - {entry_price}) = {manual_pnl:.8f} USDT")
                
                # Calculate percentage
                if entry_price > 0 and position_amt != 0:
                    position_value = abs(position_amt) * entry_price
                    pnl_percentage = (float(pos.get('unRealizedProfit', 0)) / position_value) * 100
                    print(f"   Position Value: {position_value:.2f} USDT")
                    print(f"   PnL Percentage: {pnl_percentage:.2f}%")
                
                break
        else:
            print("❌ No active ETHUSDT position found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_eth_position()