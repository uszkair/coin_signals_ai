#!/usr/bin/env python3
"""
Test Binance API connection and check positions directly
"""

import sys
import os
import asyncio
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_binance_connection():
    """Test direct Binance API connection"""
    try:
        # Get API credentials for testnet
        api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
        api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")
        
        if not api_key or not api_secret:
            print("❌ No Binance testnet API credentials found in environment")
            return
        
        print(f"🔑 Using API Key: {api_key[:8]}...")
        
        # Initialize client
        client = Client(api_key=api_key, api_secret=api_secret, testnet=True)
        
        print("✅ Binance client initialized")
        
        # Test connection
        try:
            account = client.futures_account()
            print("✅ Futures account connection successful")
            print(f"   Total Wallet Balance: {account.get('totalWalletBalance', 'N/A')} USDT")
            print(f"   Can Trade: {account.get('canTrade', False)}")
        except Exception as e:
            print(f"❌ Futures account error: {e}")
            return
        
        # Get positions
        try:
            positions = client.futures_position_information()
            active_positions = [pos for pos in positions if float(pos.get('positionAmt', 0)) != 0]
            
            print(f"\n📊 Active Positions: {len(active_positions)}")
            
            for pos in active_positions:
                symbol = pos.get('symbol')
                position_amt = float(pos.get('positionAmt', 0))
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                
                print(f"\n🔸 {symbol}")
                print(f"   Amount: {position_amt}")
                print(f"   Side: {'LONG' if position_amt > 0 else 'SHORT'}")
                print(f"   Entry Price: {entry_price}")
                print(f"   Mark Price: {mark_price}")
                print(f"   Unrealized PnL: {unrealized_pnl}")
                
                # Check open orders for this symbol
                try:
                    open_orders = client.futures_get_open_orders(symbol=symbol)
                    print(f"   Open Orders: {len(open_orders)}")
                    
                    stop_loss_found = False
                    take_profit_found = False
                    
                    for order in open_orders:
                        order_type = order.get('type', '')
                        side = order.get('side', '')
                        stop_price = float(order.get('stopPrice', 0)) if order.get('stopPrice') else None
                        price = float(order.get('price', 0)) if order.get('price') else None
                        
                        print(f"     Order: {order_type} {side}")
                        if stop_price:
                            print(f"       Stop Price: {stop_price}")
                        if price:
                            print(f"       Price: {price}")
                        
                        # Check if this is a stop loss
                        if order_type in ['STOP_MARKET', 'STOP', 'STOP_LOSS_LIMIT']:
                            trigger_price = stop_price or price
                            if position_amt > 0 and side == 'SELL' and trigger_price and trigger_price < entry_price:
                                stop_loss_found = True
                                print(f"       ✅ STOP LOSS identified: {trigger_price}")
                            elif position_amt < 0 and side == 'BUY' and trigger_price and trigger_price > entry_price:
                                stop_loss_found = True
                                print(f"       ✅ STOP LOSS identified: {trigger_price}")
                        
                        # Check if this is a take profit
                        elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT']:
                            trigger_price = stop_price or price
                            if position_amt > 0 and side == 'SELL' and trigger_price and trigger_price > entry_price:
                                take_profit_found = True
                                print(f"       ✅ TAKE PROFIT identified: {trigger_price}")
                            elif position_amt < 0 and side == 'BUY' and trigger_price and trigger_price < entry_price:
                                take_profit_found = True
                                print(f"       ✅ TAKE PROFIT identified: {trigger_price}")
                    
                    if not stop_loss_found:
                        print(f"   ⚠️  NO STOP LOSS ORDER FOUND")
                    if not take_profit_found:
                        print(f"   ⚠️  NO TAKE PROFIT ORDER FOUND")
                        
                except Exception as e:
                    print(f"   ❌ Error getting open orders: {e}")
        
        except Exception as e:
            print(f"❌ Error getting positions: {e}")
            
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    test_binance_connection()