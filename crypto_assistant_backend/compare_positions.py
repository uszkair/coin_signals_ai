"""
Compare Binance Active Positions with Local Database
This script compares real Binance positions with our local trading history
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

from app.services.binance_trading import initialize_global_trader
from app.services.database_service import DatabaseService
from app.database import AsyncSessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_binance_positions() -> Dict[str, Any]:
    """Get active positions from Binance API"""
    try:
        trader = initialize_global_trader()
        positions = await trader.get_active_positions()
        
        logger.info(f"📊 Binance API: Found {len(positions)} active positions")
        
        for pos_id, pos in positions.items():
            logger.info(f"  Position {pos_id}:")
            logger.info(f"    Symbol: {pos['symbol']}")
            logger.info(f"    Direction: {pos['direction']}")
            logger.info(f"    Quantity: {pos['quantity']}")
            logger.info(f"    Entry Price: ${pos['entry_price']:.6f}")
            logger.info(f"    Current Price: ${pos.get('current_price', 0):.6f}")
            logger.info(f"    Unrealized P&L: ${pos.get('unrealized_pnl', 0):.2f}")
            logger.info(f"    Main Order ID: {pos.get('main_order_id')}")
        
        return positions
        
    except Exception as e:
        logger.error(f"❌ Error getting Binance positions: {e}")
        return {}


async def get_database_pending_trades() -> List[Dict[str, Any]]:
    """Get pending trades from local database"""
    try:
        async with AsyncSessionLocal() as db:
            pending_trades = await DatabaseService.get_pending_trading_performances(db)
            
            logger.info(f"💾 Database: Found {len(pending_trades)} pending trades")
            
            formatted_trades = []
            for trade in pending_trades:
                trade_info = {
                    'id': trade.id,
                    'signal_id': trade.signal_id,
                    'symbol': trade.signal.symbol if trade.signal else 'Unknown',
                    'signal_type': trade.signal.signal_type if trade.signal else 'Unknown',
                    'entry_price': float(trade.signal.price) if trade.signal else 0,
                    'quantity': float(trade.quantity) if trade.quantity else 0,
                    'position_size_usd': float(trade.position_size_usd) if trade.position_size_usd else 0,
                    'main_order_id': trade.main_order_id,
                    'stop_loss_order_id': trade.stop_loss_order_id,
                    'take_profit_order_id': trade.take_profit_order_id,
                    'result': trade.result,
                    'created_at': trade.created_at,
                    'profit_loss': float(trade.profit_loss) if trade.profit_loss else 0,
                    'testnet_mode': trade.testnet_mode
                }
                formatted_trades.append(trade_info)
                
                logger.info(f"  Trade {trade.id}:")
                logger.info(f"    Symbol: {trade_info['symbol']}")
                logger.info(f"    Direction: {trade_info['signal_type']}")
                logger.info(f"    Quantity: {trade_info['quantity']}")
                logger.info(f"    Entry Price: ${trade_info['entry_price']:.6f}")
                logger.info(f"    Position Size: ${trade_info['position_size_usd']:.2f}")
                logger.info(f"    Main Order ID: {trade_info['main_order_id']}")
                logger.info(f"    Current P&L: ${trade_info['profit_loss']:.2f}")
                logger.info(f"    Testnet: {trade_info['testnet_mode']}")
            
            return formatted_trades
            
    except Exception as e:
        logger.error(f"❌ Error getting database trades: {e}")
        return []


async def compare_positions_and_trades(binance_positions: Dict[str, Any], db_trades: List[Dict[str, Any]]):
    """Compare Binance positions with database trades"""
    logger.info("\n🔍 COMPARISON ANALYSIS:")
    logger.info("=" * 60)
    
    # Create lookup dictionaries
    binance_by_order_id = {}
    for pos_id, pos in binance_positions.items():
        order_id = pos.get('main_order_id')
        if order_id:
            binance_by_order_id[str(order_id)] = pos
    
    db_by_order_id = {}
    for trade in db_trades:
        order_id = trade.get('main_order_id')
        if order_id:
            db_by_order_id[str(order_id)] = trade
    
    # Find matches and mismatches
    matched_orders = []
    binance_only = []
    database_only = []
    
    # Check Binance positions against database
    for order_id, binance_pos in binance_by_order_id.items():
        if order_id in db_by_order_id:
            matched_orders.append((order_id, binance_pos, db_by_order_id[order_id]))
        else:
            binance_only.append((order_id, binance_pos))
    
    # Check database trades not in Binance
    for order_id, db_trade in db_by_order_id.items():
        if order_id not in binance_by_order_id:
            database_only.append((order_id, db_trade))
    
    # Report results
    logger.info(f"✅ MATCHED POSITIONS: {len(matched_orders)}")
    for order_id, binance_pos, db_trade in matched_orders:
        logger.info(f"  Order ID: {order_id}")
        logger.info(f"    Binance: {binance_pos['symbol']} {binance_pos['direction']} qty={binance_pos['quantity']} P&L=${binance_pos.get('unrealized_pnl', 0):.2f}")
        logger.info(f"    Database: {db_trade['symbol']} {db_trade['signal_type']} qty={db_trade['quantity']} P&L=${db_trade['profit_loss']:.2f}")
        
        # Check for discrepancies
        if abs(binance_pos['quantity'] - db_trade['quantity']) > 0.001:
            logger.warning(f"    ⚠️  QUANTITY MISMATCH: Binance={binance_pos['quantity']}, DB={db_trade['quantity']}")
        
        if binance_pos['symbol'] != db_trade['symbol']:
            logger.warning(f"    ⚠️  SYMBOL MISMATCH: Binance={binance_pos['symbol']}, DB={db_trade['symbol']}")
    
    logger.info(f"\n🔴 BINANCE ONLY (not in database): {len(binance_only)}")
    for order_id, binance_pos in binance_only:
        logger.warning(f"  Order ID: {order_id}")
        logger.warning(f"    Binance: {binance_pos['symbol']} {binance_pos['direction']} qty={binance_pos['quantity']} P&L=${binance_pos.get('unrealized_pnl', 0):.2f}")
        logger.warning(f"    ❌ Missing from database!")
    
    logger.info(f"\n🔵 DATABASE ONLY (not in Binance): {len(database_only)}")
    for order_id, db_trade in database_only:
        logger.warning(f"  Order ID: {order_id}")
        logger.warning(f"    Database: {db_trade['symbol']} {db_trade['signal_type']} qty={db_trade['quantity']} P&L=${db_trade['profit_loss']:.2f}")
        logger.warning(f"    ❌ Missing from Binance! (Position may have been closed)")
    
    # Summary
    logger.info(f"\n📊 SUMMARY:")
    logger.info(f"  Total Binance Positions: {len(binance_positions)}")
    logger.info(f"  Total Database Pending: {len(db_trades)}")
    logger.info(f"  Matched: {len(matched_orders)}")
    logger.info(f"  Binance Only: {len(binance_only)}")
    logger.info(f"  Database Only: {len(database_only)}")
    
    if len(matched_orders) == len(binance_positions) == len(db_trades) and len(binance_only) == 0 and len(database_only) == 0:
        logger.info("✅ PERFECT SYNC: All positions match!")
    else:
        logger.warning("⚠️  SYNC ISSUES DETECTED: Manual review needed")
    
    return {
        'matched': len(matched_orders),
        'binance_only': len(binance_only),
        'database_only': len(database_only),
        'total_binance': len(binance_positions),
        'total_database': len(db_trades),
        'sync_status': 'PERFECT' if len(binance_only) == 0 and len(database_only) == 0 else 'ISSUES'
    }


async def get_recent_order_history():
    """Get recent order history from Binance for additional context"""
    try:
        trader = initialize_global_trader()
        if not trader.client:
            logger.warning("⚠️  No Binance client available for order history")
            return
        
        logger.info("\n📋 RECENT BINANCE ORDER HISTORY:")
        logger.info("=" * 60)
        
        # Get recent orders for main symbols
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
        all_orders = []
        
        for symbol in symbols:
            try:
                if trader.use_futures:
                    orders = trader.client.futures_get_all_orders(symbol=symbol, limit=5)
                else:
                    orders = trader.client.get_all_orders(symbol=symbol, limit=5)
                
                for order in orders:
                    order_info = {
                        'symbol': order['symbol'],
                        'order_id': order['orderId'],
                        'side': order['side'],
                        'type': order['type'],
                        'status': order['status'],
                        'original_qty': float(order['origQty']),
                        'executed_qty': float(order['executedQty']),
                        'price': float(order['price']) if order['price'] != '0' else None,
                        'time': datetime.fromtimestamp(order['time'] / 1000),
                        'update_time': datetime.fromtimestamp(order['updateTime'] / 1000)
                    }
                    all_orders.append(order_info)
                    
            except Exception as e:
                logger.warning(f"Could not get orders for {symbol}: {e}")
        
        # Sort by time and show recent orders
        all_orders.sort(key=lambda x: x['time'], reverse=True)
        
        logger.info(f"Recent orders (last 10):")
        for order in all_orders[:10]:
            logger.info(f"  {order['time'].strftime('%Y-%m-%d %H:%M:%S')} | {order['symbol']} | {order['side']} | {order['status']} | ID: {order['order_id']}")
        
    except Exception as e:
        logger.error(f"❌ Error getting order history: {e}")


async def main():
    """Main comparison function"""
    logger.info("🚀 STARTING POSITION COMPARISON")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get data from both sources
        logger.info("\n1️⃣ Getting Binance active positions...")
        binance_positions = await get_binance_positions()
        
        logger.info("\n2️⃣ Getting database pending trades...")
        db_trades = await get_database_pending_trades()
        
        logger.info("\n3️⃣ Comparing positions...")
        comparison_result = await compare_positions_and_trades(binance_positions, db_trades)
        
        logger.info("\n4️⃣ Getting recent order history for context...")
        await get_recent_order_history()
        
        logger.info(f"\n🎯 FINAL RESULT: {comparison_result['sync_status']}")
        
        return comparison_result
        
    except Exception as e:
        logger.error(f"❌ Error in main comparison: {e}")
        return None


if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\n🏁 Comparison completed: {result['sync_status']}")
    else:
        print("\n❌ Comparison failed")