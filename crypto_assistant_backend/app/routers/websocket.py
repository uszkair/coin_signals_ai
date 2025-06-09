"""
WebSocket Router for real-time data streaming
Handles WebSocket connections for live price updates and trading data
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all subscriptions
        for symbol, connections in self.subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    def subscribe_to_symbol(self, websocket: WebSocket, symbol: str):
        """Subscribe a WebSocket to a specific symbol"""
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = []
        
        if websocket not in self.subscriptions[symbol]:
            self.subscriptions[symbol].append(websocket)
            logger.info(f"WebSocket subscribed to {symbol}")
    
    def unsubscribe_from_symbol(self, websocket: WebSocket, symbol: str):
        """Unsubscribe a WebSocket from a specific symbol"""
        if symbol in self.subscriptions and websocket in self.subscriptions[symbol]:
            self.subscriptions[symbol].remove(websocket)
            logger.info(f"WebSocket unsubscribed from {symbol}")
    
    async def send_to_subscribers(self, symbol: str, message: str):
        """Send a message to all subscribers of a specific symbol"""
        if symbol not in self.subscriptions:
            return
        
        disconnected = []
        for connection in self.subscriptions[symbol]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to subscriber: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time data"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established",
            "timestamp": asyncio.get_event_loop().time()
        }), websocket)
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_personal_message(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }), websocket)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message(json.dumps({
                    "type": "error",
                    "message": str(e)
                }), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message: Dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # Subscribe to symbol updates
        symbol = message.get("symbol")
        if symbol:
            manager.subscribe_to_symbol(websocket, symbol)
            await manager.send_personal_message(json.dumps({
                "type": "subscription",
                "status": "subscribed",
                "symbol": symbol
            }), websocket)
    
    elif message_type == "unsubscribe":
        # Unsubscribe from symbol updates
        symbol = message.get("symbol")
        if symbol:
            manager.unsubscribe_from_symbol(websocket, symbol)
            await manager.send_personal_message(json.dumps({
                "type": "subscription",
                "status": "unsubscribed",
                "symbol": symbol
            }), websocket)
    
    elif message_type == "ping":
        # Respond to ping with pong
        await manager.send_personal_message(json.dumps({
            "type": "pong",
            "timestamp": asyncio.get_event_loop().time()
        }), websocket)
    
    elif message_type == "get_status":
        # Send current status
        await manager.send_personal_message(json.dumps({
            "type": "status",
            "connections": len(manager.active_connections),
            "subscriptions": {symbol: len(connections) for symbol, connections in manager.subscriptions.items()}
        }), websocket)
    
    else:
        await manager.send_personal_message(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }), websocket)

# Function to broadcast price updates (can be called from other parts of the application)
async def broadcast_price_update(symbol: str, price: float, change_24h: float = None):
    """Broadcast price update to all subscribers of a symbol"""
    message = json.dumps({
        "type": "price_update",
        "symbol": symbol,
        "price": price,
        "change_24h": change_24h,
        "timestamp": asyncio.get_event_loop().time()
    })
    
    await manager.send_to_subscribers(symbol, message)

# Function to broadcast trading signals
async def broadcast_signal(signal_data: Dict):
    """Broadcast trading signal to all connected clients"""
    message = json.dumps({
        "type": "signal",
        "data": signal_data,
        "timestamp": asyncio.get_event_loop().time()
    })
    
    await manager.broadcast(message)

# Function to broadcast trade execution updates
async def broadcast_trade_update(trade_data: Dict):
    """Broadcast trade execution update to all connected clients"""
    message = json.dumps({
        "type": "trade_update",
        "data": trade_data,
        "timestamp": asyncio.get_event_loop().time()
    })
    
    await manager.broadcast(message)