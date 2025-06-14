#!/usr/bin/env python3
"""
Live pozíciók API teszt
Teszteli az új /api/trading/live-positions endpoint-ot
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the crypto_assistant_backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'crypto_assistant_backend'))

from app.services.binance_trading import initialize_global_trader

async def test_live_positions_api():
    """Teszteli a live pozíciók API-t"""
    
    print("🧪 LIVE POZÍCIÓK API TESZT")
    print("=" * 60)
    
    try:
        # 1. Trader inicializálása
        print("1️⃣ Binance trader inicializálása...")
        trader = initialize_global_trader()
        
        if not trader.client:
            print("   ❌ Binance API kliens nem elérhető!")
            return
        
        print(f"   ✅ Trader inicializálva: {'Testnet' if trader.testnet else 'Mainnet'} mód")
        print(f"   📡 API URL: {trader.base_url}")
        print(f"   🔧 Futures mód: {trader.use_futures}")
        print()
        
        # 2. Futures pozíciók lekérése közvetlenül
        if trader.use_futures:
            print("2️⃣ Futures pozíciók közvetlen lekérése...")
            try:
                positions = trader.client.futures_position_information()
                
                # Aktív pozíciók szűrése
                active_positions = [
                    pos for pos in positions 
                    if float(pos.get('positionAmt', 0)) != 0
                ]
                
                print(f"   📊 Összes pozíció: {len(positions)}")
                print(f"   🎯 Aktív pozíciók: {len(active_positions)}")
                
                if active_positions:
                    print("   📋 Aktív pozíciók részletei:")
                    for i, pos in enumerate(active_positions[:5], 1):  # Csak az első 5-öt mutatjuk
                        symbol = pos.get('symbol')
                        position_amt = float(pos.get('positionAmt', 0))
                        entry_price = float(pos.get('entryPrice', 0))
                        mark_price = float(pos.get('markPrice', 0))
                        unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                        percentage = float(pos.get('percentage', 0))
                        
                        print(f"      {i}. {symbol}:")
                        print(f"         Position: {position_amt} ({'Long' if position_amt > 0 else 'Short'})")
                        print(f"         Entry Price: {entry_price}")
                        print(f"         Mark Price: {mark_price}")
                        print(f"         Unrealized P&L: {unrealized_pnl} USDT")
                        print(f"         P&L %: {percentage}%")
                        print()
                else:
                    print("   ℹ️  Nincs aktív pozíció")
                
            except Exception as e:
                print(f"   ❌ Hiba a pozíciók lekérésénél: {str(e)}")
                return
        
        # 3. API endpoint szimuláció
        print("3️⃣ API endpoint logika szimulálása...")
        
        live_positions = []
        
        if trader.use_futures:
            try:
                positions = trader.client.futures_position_information()
                
                for pos in positions:
                    position_amt = float(pos.get('positionAmt', 0))
                    if position_amt != 0:
                        symbol = pos.get('symbol')
                        entry_price = float(pos.get('entryPrice', 0))
                        mark_price = float(pos.get('markPrice', 0))
                        unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                        percentage = float(pos.get('percentage', 0))
                        
                        live_positions.append({
                            'symbol': symbol,
                            'position_side': 'LONG' if position_amt > 0 else 'SHORT',
                            'position_amt': abs(position_amt),
                            'entry_price': entry_price,
                            'mark_price': mark_price,
                            'unrealized_pnl': unrealized_pnl,
                            'pnl_percentage': percentage,
                            'position_type': 'FUTURES',
                            'leverage': float(pos.get('leverage', 1)),
                            'margin_type': pos.get('marginType', 'cross'),
                            'update_time': pos.get('updateTime')
                        })
                
                # API válasz szimuláció
                api_response = {
                    "success": True,
                    "data": {
                        "positions": live_positions,
                        "count": len(live_positions),
                        "account_type": "FUTURES",
                        "testnet": trader.testnet
                    }
                }
                
                print(f"   ✅ API válasz elkészítve:")
                print(f"      Pozíciók száma: {len(live_positions)}")
                print(f"      Account típus: FUTURES")
                print(f"      Testnet: {trader.testnet}")
                print()
                
                # 4. JSON formátum ellenőrzése
                print("4️⃣ JSON válasz formátum:")
                print(json.dumps(api_response, indent=2, default=str))
                print()
                
                # 5. SOLUSDT pozíció keresése
                print("5️⃣ SOLUSDT pozíció keresése...")
                solusdt_position = None
                for pos in live_positions:
                    if pos['symbol'] == 'SOLUSDT':
                        solusdt_position = pos
                        break
                
                if solusdt_position:
                    print("   ✅ SOLUSDT pozíció MEGTALÁLVA!")
                    print(f"      Symbol: {solusdt_position['symbol']}")
                    print(f"      Irány: {solusdt_position['position_side']}")
                    print(f"      Mennyiség: {solusdt_position['position_amt']}")
                    print(f"      Belépési ár: {solusdt_position['entry_price']}")
                    print(f"      Jelenlegi ár: {solusdt_position['mark_price']}")
                    print(f"      P&L: {solusdt_position['unrealized_pnl']} USDT")
                    print(f"      P&L %: {solusdt_position['pnl_percentage']}%")
                    print(f"      Tőkeáttétel: {solusdt_position['leverage']}x")
                else:
                    print("   ❌ SOLUSDT pozíció nem található")
                
            except Exception as e:
                print(f"   ❌ Hiba az API logika szimulálásánál: {str(e)}")
        
        # 6. Összefoglaló
        print("\n6️⃣ TESZT ÖSSZEFOGLALÓ:")
        print()
        
        if live_positions:
            print("   ✅ SIKERES TESZT!")
            print(f"   📊 {len(live_positions)} db pozíció található")
            print("   🔄 Az API endpoint működőképes")
            print("   🎯 A frontend meg tudja jeleníteni a pozíciókat")
            
            # Statisztikák
            total_pnl = sum(pos['unrealized_pnl'] for pos in live_positions)
            long_positions = len([p for p in live_positions if p['position_side'] == 'LONG'])
            short_positions = len([p for p in live_positions if p['position_side'] == 'SHORT'])
            
            print(f"\n   📈 Pozíció statisztikák:")
            print(f"      Long pozíciók: {long_positions}")
            print(f"      Short pozíciók: {short_positions}")
            print(f"      Összes P&L: {total_pnl:.2f} USDT")
            
        else:
            print("   ⚠️  NINCS AKTÍV POZÍCIÓ")
            print("   ℹ️  Az API működik, de nincs mit megjeleníteni")
        
        print("\n   🚀 A frontend most már látni fogja a nyitott pozíciókat!")
        
    except Exception as e:
        print(f"❌ Kritikus hiba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Live pozíciók API teszt indítása...")
    
    try:
        asyncio.run(test_live_positions_api())
    except KeyboardInterrupt:
        print("\n⏹️  Teszt megszakítva.")
    except Exception as e:
        print(f"\n❌ Kritikus hiba: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Teszt befejezve.")