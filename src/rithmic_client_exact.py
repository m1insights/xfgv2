"""
Exact Copy of Working Rithmic Client for xFGv2
This is a line-by-line copy of the working connection logic from the old system,
with only order management removed. Everything else is preserved exactly.
"""

import asyncio
import ssl
import pathlib
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import websockets

# Import all the protocol buffer messages from Rithmic (exact same imports)
try:
    # Try relative imports first (for when running as module)
    from .rithmic_proto import base_pb2
    from .rithmic_proto import request_login_pb2
    from .rithmic_proto import response_login_pb2
    from .rithmic_proto import request_heartbeat_pb2
    from .rithmic_proto import response_heartbeat_pb2
    from .rithmic_proto import request_market_data_update_pb2
    from .rithmic_proto import response_market_data_update_pb2
    from .rithmic_proto import last_trade_pb2
    from .rithmic_proto import best_bid_offer_pb2
except ImportError:
    # Fall back to absolute imports
    import src.rithmic_proto.base_pb2 as base_pb2
    import src.rithmic_proto.request_login_pb2 as request_login_pb2
    import src.rithmic_proto.response_login_pb2 as response_login_pb2
    import src.rithmic_proto.request_heartbeat_pb2 as request_heartbeat_pb2
    import src.rithmic_proto.response_heartbeat_pb2 as response_heartbeat_pb2
    import src.rithmic_proto.request_market_data_update_pb2 as request_market_data_update_pb2
    import src.rithmic_proto.response_market_data_update_pb2 as response_market_data_update_pb2
    import src.rithmic_proto.last_trade_pb2 as last_trade_pb2
    import src.rithmic_proto.best_bid_offer_pb2 as best_bid_offer_pb2

logger = logging.getLogger(__name__)


class RithmicClientExact:
    """
    EXACT copy of working Rithmic client implementation.
    Preserves all working connection logic, removes only order management.
    """
    
    def __init__(self, 
                 username: str, 
                 password: str,
                 app_name: str = "mash:mananfutures",
                 uri: str = None,
                 system_name: str = "Rithmic Test"):
        """
        Initialize the Rithmic client (EXACT copy of working version).
        
        Args:
            username: Your Rithmic username
            password: Your Rithmic password
            app_name: Your approved application name
            uri: Rithmic server URI
            system_name: Rithmic system to connect to
        """
        self.username = username
        self.password = password
        self.app_name = app_name
        # Use provided URI or get from environment, fallback to test (EXACT copy)
        if uri:
            self.uri = uri
        else:
            self.uri = os.getenv('RITHMIC_URI', 'wss://rituz00100.rithmic.com:443')
        self.system_name = system_name
        
        # Connection state (EXACT copy)
        self.ws = None
        self.is_connected = False
        self.is_authenticated = False
        
        # Market data (EXACT copy from old system)
        self.current_prices = {}
        self.bid_prices = {}  # Track bid prices for trade side determination
        self.ask_prices = {}  # Track ask prices for trade side determination
        
        # Callbacks (same pattern as old system)
        self.callbacks = {
            'market_data': {},
        }
    
    async def connect(self) -> bool:
        """Connect to Rithmic server (EXACT copy of working method)."""
        try:
            logger.info(f"Connecting to {self.uri}...")
            
            # Set up SSL context (EXACT copy)
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            cert_path = pathlib.Path(__file__).parent / "rithmic_proto" / "rithmic_ssl_cert_auth_params"
            
            if cert_path.exists():
                ssl_context.load_verify_locations(cert_path)
            else:
                logger.warning("SSL certificate not found, using default context")
                ssl_context = ssl.create_default_context()
            
            # Connect with ping interval to keep connection alive (EXACT copy)
            self.ws = await websockets.connect(
                self.uri, 
                ssl=ssl_context, 
                ping_interval=3
            )
            
            self.is_connected = True
            logger.info("Connected to Rithmic server")
            
            # Start message consumer (EXACT copy)
            asyncio.create_task(self._consume_messages())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with Rithmic (EXACT copy of working method)."""
        if not self.is_connected:
            logger.error("Cannot authenticate: Not connected")
            return False
        
        try:
            # Create login request (EXACT copy)
            rq = request_login_pb2.RequestLogin()
            rq.template_id = 10
            rq.template_version = "3.9"
            rq.user = self.username
            rq.password = self.password
            rq.app_name = self.app_name
            rq.app_version = "1.0.0"
            rq.system_name = self.system_name
            # Use ORDER_PLANT for both trading and market data (EXACT copy)
            rq.infra_type = request_login_pb2.RequestLogin.SysInfraType.ORDER_PLANT
            
            # Send login request (EXACT copy)
            await self._send_message(rq)
            
            # Wait for login response (EXACT copy)
            for _ in range(30):  # 30 second timeout
                if self.is_authenticated:
                    logger.info("Authentication successful")
                    return True
                await asyncio.sleep(1)
            
            logger.error("Authentication timed out")
            return False
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def subscribe_market_data(self, 
                                    symbol: str, 
                                    exchange: str, 
                                    data_type: str = "TRADES",
                                    callback: Optional[Callable] = None) -> bool:
        """Subscribe to market data (EXACT copy of working method)."""
        if not self.is_authenticated:
            logger.error("Cannot subscribe: Not authenticated")
            return False
        
        try:
            rq = request_market_data_update_pb2.RequestMarketDataUpdate()
            rq.template_id = 100
            rq.symbol = symbol
            rq.exchange = exchange
            rq.request = request_market_data_update_pb2.RequestMarketDataUpdate.Request.SUBSCRIBE
            
            # Request both trades and quotes (EXACT copy)
            rq.update_bits = (request_market_data_update_pb2.RequestMarketDataUpdate.UpdateBits.LAST_TRADE | 
                            request_market_data_update_pb2.RequestMarketDataUpdate.UpdateBits.BBO)
            
            if callback:
                self.callbacks['market_data'][symbol] = callback
            
            await self._send_message(rq)
            
            logger.info(f"Subscribed to {symbol} on {exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Market data subscription failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Rithmic (EXACT copy)."""
        self.is_connected = False
        self.is_authenticated = False
        
        if self.ws:
            await self.ws.close(1000, "Closing connection")
            logger.info("Disconnected from Rithmic")
    
    async def _send_message(self, message):
        """Send a protobuf message (EXACT copy)."""
        if not self.ws:
            raise Exception("Not connected")
        
        serialized = message.SerializeToString()
        await self.ws.send(serialized)
    
    async def _send_heartbeat(self):
        """Send heartbeat to keep connection alive (EXACT copy)."""
        try:
            rq = request_heartbeat_pb2.RequestHeartbeat()
            rq.template_id = 18
            await self._send_message(rq)
            logger.debug("Sent heartbeat")
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    async def _consume_messages(self):
        """Consume messages from websocket (EXACT copy of working logic)."""
        try:
            while self.is_connected:
                try:
                    # Wait for message with timeout (EXACT copy)
                    msg_buf = await asyncio.wait_for(self.ws.recv(), timeout=5)
                    
                    # Parse base message to get template ID (EXACT copy)
                    base = base_pb2.Base()
                    base.ParseFromString(msg_buf)
                    
                    # Route based on template ID (EXACT copy)
                    await self._route_message(base.template_id, msg_buf)
                    
                except asyncio.TimeoutError:
                    # Send heartbeat on timeout (EXACT copy)
                    if self.ws:
                        try:
                            await self._send_heartbeat()
                        except (websockets.exceptions.ConnectionClosed, 
                                websockets.exceptions.ConnectionClosedError,
                                websockets.exceptions.ConnectionClosedOK,
                                AttributeError) as e:
                            logger.warning(f"Connection closed: {e}")
                            self.is_connected = False
                            break
                    else:
                        logger.warning("No websocket connection")
                        self.is_connected = False
                        break
                        
        except Exception as e:
            logger.error(f"Message consumer error: {e}")
            self.is_connected = False
    
    async def _route_message(self, template_id: int, msg_buf: bytes):
        """Route message based on template ID (EXACT copy of working logic)."""
        # Only log non-frequent template IDs (EXACT copy)
        if template_id not in [150, 151, 19]:  # Skip trades, quotes, and heartbeats
            logger.info(f"RITHMIC MESSAGE: Template ID {template_id}")
        
        try:
            if template_id == 11:  # Login response
                await self._handle_login_response(msg_buf)
            elif template_id == 19:  # Heartbeat response
                logger.debug("Received heartbeat response")
            elif template_id == 100:  # Market data subscription response
                await self._handle_market_data_response(msg_buf)
            elif template_id == 101:  # Market data response
                logger.info("Market data subscription confirmed")
            elif template_id == 150:  # Last trade
                await self._handle_last_trade(msg_buf)
            elif template_id == 151:  # Best bid/offer
                await self._handle_best_bid_offer(msg_buf)
            else:
                logger.debug(f"Unhandled message type: {template_id}")
                
        except Exception as e:
            logger.error(f"Error routing message: {e}")
    
    async def _handle_login_response(self, msg_buf: bytes):
        """Handle login response (EXACT copy)."""
        try:
            rp = response_login_pb2.ResponseLogin()
            rp.ParseFromString(msg_buf)
            
            if len(rp.rp_code) > 0 and rp.rp_code[0] == "0":
                self.is_authenticated = True
                logger.info("Login successful")
            else:
                logger.error(f"Login failed: {rp.rp_code}")
                self.is_authenticated = False
                
        except Exception as e:
            logger.error(f"Error handling login response: {e}")
    
    async def _handle_last_trade(self, msg_buf: bytes):
        """Handle last trade message (EXACT copy of working logic)."""
        try:
            trade = last_trade_pb2.LastTrade()
            trade.ParseFromString(msg_buf)
            
            symbol = trade.symbol
            
            # Get price and volume from the correct fields (EXACT copy)
            price = trade.trade_price if hasattr(trade, 'trade_price') else 0.0
            volume = trade.trade_size if hasattr(trade, 'trade_size') else 0
            
            # Skip trades with 0 price or volume (EXACT copy)
            if price == 0 or volume == 0:
                return
                
            # Debug logging (only log every 10th trade to reduce spam) (EXACT copy)
            if not hasattr(self, '_trade_count'):
                self._trade_count = 0
            self._trade_count += 1
            if self._trade_count % 10 == 0:
                logger.info(f"RITHMIC LAST TRADE: {symbol} @ {price} x {volume}")
            
            # Update current price (EXACT copy)
            self.current_prices[symbol] = price
            
            # Determine trade side based on bid/ask (EXACT copy)
            trade_side = 'unknown'
            bid_price = self.bid_prices.get(symbol, 0)
            ask_price = self.ask_prices.get(symbol, 0)
            
            # Log if bid/ask are missing (debug) (EXACT copy)
            if self._trade_count % 100 == 0:
                logger.info(f"Trade side determination - Symbol: {symbol}, Price: {price}, Bid: {bid_price}, Ask: {ask_price}")
            
            if bid_price > 0 and ask_price > 0:
                if price <= bid_price:
                    trade_side = 'sell'
                elif price >= ask_price:
                    trade_side = 'buy'
                else:
                    # Price between bid/ask - use uptick/downtick rule (EXACT copy)
                    if symbol not in self.current_prices:
                        # First trade - use midpoint
                        mid = (bid_price + ask_price) / 2
                        trade_side = 'buy' if price > mid else 'sell'
                    else:
                        prev_price = self.current_prices[symbol]
                        if price > prev_price:
                            trade_side = 'buy'
                        elif price < prev_price:
                            trade_side = 'sell'
                        else:
                            # Same price - use distance from bid/ask (EXACT copy)
                            bid_dist = abs(price - bid_price)
                            ask_dist = abs(price - ask_price)
                            trade_side = 'sell' if bid_dist < ask_dist else 'buy'
            else:
                # No bid/ask available - use tick direction (EXACT copy)
                if symbol in self.current_prices:
                    prev_price = self.current_prices[symbol]
                    if price > prev_price:
                        trade_side = 'buy'
                    elif price < prev_price:
                        trade_side = 'sell'
                    else:
                        # Same price - alternate or use volume patterns (EXACT copy)
                        # For now, let's use a simple alternating pattern
                        if not hasattr(self, '_last_trade_side'):
                            self._last_trade_side = {}
                        last_side = self._last_trade_side.get(symbol, 'sell')
                        trade_side = 'buy' if last_side == 'sell' else 'sell'
                        self._last_trade_side[symbol] = trade_side
                else:
                    # Very first trade with no reference - default to buy (EXACT copy)
                    trade_side = 'buy'
            
            # Never leave as unknown (EXACT copy)
            if trade_side == 'unknown':
                logger.warning(f"Trade side still unknown for {symbol} @ {price}, defaulting to buy")
                trade_side = 'buy'
            
            # Call market data callback (EXACT copy)
            if symbol in self.callbacks['market_data']:
                data = {
                    'type': 'trade',
                    'symbol': symbol,
                    'price': price,
                    'volume': volume,
                    'timestamp': datetime.now().isoformat(),
                    'trade_side': trade_side
                }
                callback = self.callbacks['market_data'][symbol]
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
                
        except Exception as e:
            logger.error(f"Error handling last trade: {e}")
    
    async def _handle_best_bid_offer(self, msg_buf: bytes):
        """Handle best bid/offer message (EXACT copy)."""
        try:
            bbo = best_bid_offer_pb2.BestBidOffer()
            bbo.ParseFromString(msg_buf)
            
            symbol = bbo.symbol
            
            # Store bid/ask prices for trade side determination (EXACT copy)
            self.bid_prices[symbol] = bbo.bid_price
            self.ask_prices[symbol] = bbo.ask_price
            
            # Call market data callback (EXACT copy)
            if symbol in self.callbacks['market_data']:
                data = {
                    'type': 'quote',
                    'symbol': symbol,
                    'bid': bbo.bid_price,
                    'ask': bbo.ask_price,
                    'bid_size': bbo.bid_size,
                    'ask_size': bbo.ask_size,
                    'timestamp': datetime.now().isoformat()
                }
                callback = self.callbacks['market_data'][symbol]
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
                    
        except Exception as e:
            logger.error(f"Error handling BBO: {e}")
    
    async def _handle_market_data_response(self, msg_buf: bytes):
        """Handle market data subscription response (EXACT copy)."""
        try:
            rp = response_market_data_update_pb2.ResponseMarketDataUpdate()
            rp.ParseFromString(msg_buf)
            
            # Log the response details (EXACT copy)
            if len(rp.rp_code) > 0:
                logger.info(f"Market data response - Code: {rp.rp_code}, Symbol: {rp.symbol}, Exchange: {rp.exchange}")
                if len(rp.text) > 0:
                    logger.info(f"Market data response text: {rp.text}")
                    
                if rp.rp_code[0] != "0":
                    logger.error(f"Market data subscription failed: Code={rp.rp_code}, Text={rp.text}")
            else:
                logger.info(f"Market data response received for {rp.symbol} on {rp.exchange}")
                
        except Exception as e:
            logger.error(f"Error handling market data response: {e}")
    
    # Public API methods for compatibility
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        return self.current_prices.get(symbol)
    
    def get_bid_ask(self, symbol: str) -> tuple[float, float]:
        """Get current bid/ask for a symbol."""
        return (self.bid_prices.get(symbol, 0.0), self.ask_prices.get(symbol, 0.0))
    
    def add_market_data_callback(self, symbol: str, callback: Callable):
        """Add a callback for market data updates."""
        self.callbacks['market_data'][symbol] = callback
        logger.debug(f"Added market data callback for {symbol}")


# Factory function using environment variables (matching old system pattern)
def create_rithmic_client_exact_from_env() -> RithmicClientExact:
    """Create exact copy Rithmic client from environment variables."""
    username = os.getenv('RITHMIC_USERNAME')
    password = os.getenv('RITHMIC_PASSWORD')
    system_name = os.getenv('RITHMIC_SYSTEM_NAME', 'Rithmic Test')
    uri = os.getenv('RITHMIC_URI', 'wss://rituz00100.rithmic.com:443')
    app_name = os.getenv('RITHMIC_APP_NAME', 'mash:mananfutures')
    
    if not username or not password:
        raise ValueError("RITHMIC_USERNAME and RITHMIC_PASSWORD environment variables required")
    
    return RithmicClientExact(
        username=username,
        password=password,
        app_name=app_name,
        uri=uri,
        system_name=system_name
    )


def create_rithmic_client_exact(username: str, password: str, 
                               uri: str = None, system_name: str = "Rithmic Test") -> RithmicClientExact:
    """Create exact copy Rithmic client with parameters."""
    return RithmicClientExact(
        username=username,
        password=password,
        uri=uri,
        system_name=system_name
    )