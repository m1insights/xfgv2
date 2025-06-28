"""
Streamlined Rithmic Client for xFGv2
Focused on login, live market data for ES/NQ, async architecture, error handling & reconnection.
No order management or trading functionality.
"""

import asyncio
import ssl
import pathlib
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import websockets
from dataclasses import dataclass
from enum import Enum

# Import Rithmic protocol buffer messages
try:
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
    # Fall back to absolute imports for testing
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


class ConnectionState(Enum):
    """Connection state tracking."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class MarketData:
    """Market data structure."""
    symbol: str
    price: float
    volume: int
    bid: float = 0.0
    ask: float = 0.0
    timestamp: str = ""
    trade_side: str = "unknown"  # 'buy', 'sell', 'unknown'


@dataclass
class RithmicConfig:
    """Rithmic connection configuration."""
    username: str
    password: str
    app_name: str = "mash:mananfutures"
    uri: str = "wss://rituz00100.rithmic.com:443"
    system_name: str = "Rithmic Test"
    symbols: List[str] = None
    exchanges: List[str] = None
    heartbeat_interval: int = 30
    max_reconnect_attempts: int = 5
    reconnect_delay: int = 5
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ['ES', 'NQ']  # Default to ES and NQ
        if self.exchanges is None:
            self.exchanges = ['CME', 'CME']  # Both on CME


class RithmicClientV2:
    """
    Streamlined Rithmic client for xFGv2.
    
    Features:
    - Login and authentication
    - Live market data for ES/NQ
    - Async architecture
    - Error handling and reconnection
    - No trading/order management
    """
    
    def __init__(self, config: RithmicConfig):
        """Initialize the Rithmic client."""
        self.config = config
        
        # Connection state
        self.state = ConnectionState.DISCONNECTED
        self.ws = None
        self.last_heartbeat = None
        self.reconnect_count = 0
        
        # Market data storage
        self.current_prices = {}  # {symbol: price}
        self.bid_prices = {}      # {symbol: bid}
        self.ask_prices = {}      # {symbol: ask}
        self.last_trades = {}     # {symbol: MarketData}
        
        # Callbacks for market data
        self.market_data_callbacks = {}  # {symbol: [callbacks]}
        self.connection_callbacks = []   # Connection state callbacks
        
        # Tasks for background operations
        self.heartbeat_task = None
        self.consumer_task = None
        self.reconnect_task = None
        
        # Statistics
        self.stats = {
            'trades_received': 0,
            'quotes_received': 0,
            'connection_attempts': 0,
            'last_data_time': None,
            'start_time': datetime.now()
        }
        
        logger.info(f"RithmicClientV2 initialized for symbols: {config.symbols}")
    
    async def connect(self) -> bool:
        """Connect and authenticate with Rithmic."""
        if self.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]:
            logger.warning("Already connected")
            return True
            
        logger.info("Starting Rithmic connection...")
        self.state = ConnectionState.CONNECTING
        self.stats['connection_attempts'] += 1
        
        try:
            # Setup SSL context
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            cert_path = pathlib.Path(__file__).parent / "rithmic_proto" / "rithmic_ssl_cert_auth_params"
            
            if cert_path.exists():
                ssl_context.load_verify_locations(cert_path)
                logger.debug("Loaded Rithmic SSL certificate")
            else:
                logger.warning("SSL certificate not found, using default context")
                ssl_context = ssl.create_default_context()
            
            # Connect with ping interval to keep connection alive (same as old system)
            self.ws = await websockets.connect(
                self.config.uri,
                ssl=ssl_context,
                ping_interval=3
            )
            
            self.state = ConnectionState.CONNECTED
            logger.info(f"Connected to Rithmic server: {self.config.uri}")
            
            # Start message consumer
            self.consumer_task = asyncio.create_task(self._consume_messages())
            
            # Authenticate
            if await self._authenticate():
                # Subscribe to market data for configured symbols
                await self._subscribe_market_data()
                
                # Start heartbeat
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
                # Notify connection callbacks
                await self._notify_connection_state(ConnectionState.AUTHENTICATED)
                
                return True
            else:
                await self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = ConnectionState.FAILED
            await self._notify_connection_state(ConnectionState.FAILED)
            return False
    
    async def disconnect(self):
        """Disconnect from Rithmic."""
        logger.info("Disconnecting from Rithmic...")
        
        # Cancel background tasks
        for task in [self.heartbeat_task, self.consumer_task, self.reconnect_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close websocket
        if self.ws:
            try:
                await self.ws.close(1000, "Client disconnect")
            except Exception as e:
                logger.warning(f"Error closing websocket: {e}")
        
        self.state = ConnectionState.DISCONNECTED
        self.ws = None
        self.last_heartbeat = None
        
        await self._notify_connection_state(ConnectionState.DISCONNECTED)
        logger.info("Disconnected from Rithmic")
    
    async def _authenticate(self) -> bool:
        """Authenticate with Rithmic."""
        try:
            self.state = ConnectionState.AUTHENTICATING
            logger.info("Authenticating with Rithmic...")
            
            # Create login request
            login_req = request_login_pb2.RequestLogin()
            login_req.template_id = 10
            login_req.template_version = "3.9"
            login_req.user = self.config.username
            login_req.password = self.config.password
            login_req.app_name = self.config.app_name
            login_req.app_version = "1.0.0"
            login_req.system_name = self.config.system_name
            login_req.infra_type = request_login_pb2.RequestLogin.SysInfraType.ORDER_PLANT
            
            await self._send_message(login_req)
            
            # Wait for authentication response (30 second timeout)
            for _ in range(30):
                if self.state == ConnectionState.AUTHENTICATED:
                    logger.info("Authentication successful")
                    return True
                elif self.state == ConnectionState.FAILED:
                    logger.error("Authentication failed")
                    return False
                await asyncio.sleep(1)
            
            logger.error("Authentication timed out")
            self.state = ConnectionState.FAILED
            return False
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.state = ConnectionState.FAILED
            return False
    
    async def _subscribe_market_data(self):
        """Subscribe to market data for configured symbols."""
        try:
            for i, symbol in enumerate(self.config.symbols):
                exchange = self.config.exchanges[i] if i < len(self.config.exchanges) else 'CME'
                
                # Subscribe to market data
                market_req = request_market_data_update_pb2.RequestMarketDataUpdate()
                market_req.template_id = 100
                market_req.symbol = symbol
                market_req.exchange = exchange
                market_req.request = request_market_data_update_pb2.RequestMarketDataUpdate.Request.SUBSCRIBE
                
                # Request both trades and quotes
                market_req.update_bits = (
                    request_market_data_update_pb2.RequestMarketDataUpdate.UpdateBits.LAST_TRADE |
                    request_market_data_update_pb2.RequestMarketDataUpdate.UpdateBits.BBO
                )
                
                await self._send_message(market_req)
                logger.info(f"Subscribed to market data: {symbol} on {exchange}")
                
                # Small delay between subscriptions
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Market data subscription failed: {e}")
    
    async def _send_message(self, message):
        """Send a protobuf message to Rithmic."""
        if not self.ws:
            raise Exception("Not connected")
        
        serialized = message.SerializeToString()
        await self.ws.send(serialized)
    
    async def _consume_messages(self):
        """Consume messages from websocket."""
        try:
            while self.ws and not self.ws.closed:
                try:
                    # Wait for message with timeout
                    msg_buf = await asyncio.wait_for(self.ws.recv(), timeout=10)
                    
                    # Parse base message to get template ID
                    base = base_pb2.Base()
                    base.ParseFromString(msg_buf)
                    
                    # Route message based on template ID
                    await self._route_message(base.template_id, msg_buf)
                    
                except asyncio.TimeoutError:
                    # Check if connection is still alive
                    if self.ws and self.ws.closed:
                        logger.warning("WebSocket connection closed")
                        break
                    # Continue on timeout - heartbeat will handle keep-alive
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed by server")
                    break
                    
        except Exception as e:
            logger.error(f"Message consumer error: {e}")
        
        # Connection lost - trigger reconnect if we were authenticated
        if self.state == ConnectionState.AUTHENTICATED:
            logger.warning("Connection lost, scheduling reconnection...")
            await self._schedule_reconnect()
    
    async def _route_message(self, template_id: int, msg_buf: bytes):
        """Route message based on template ID."""
        try:
            if template_id == 11:  # Login response
                await self._handle_login_response(msg_buf)
            elif template_id == 19:  # Heartbeat response
                self.last_heartbeat = datetime.now()
                logger.debug("Heartbeat acknowledged")
            elif template_id == 101:  # Market data subscription response
                await self._handle_market_data_response(msg_buf)
            elif template_id == 150:  # Last trade
                await self._handle_last_trade(msg_buf)
            elif template_id == 151:  # Best bid/offer
                await self._handle_best_bid_offer(msg_buf)
            else:
                logger.debug(f"Unhandled message type: {template_id}")
                
        except Exception as e:
            logger.error(f"Error routing message {template_id}: {e}")
    
    async def _handle_login_response(self, msg_buf: bytes):
        """Handle login response."""
        try:
            response = response_login_pb2.ResponseLogin()
            response.ParseFromString(msg_buf)
            
            if len(response.rp_code) > 0 and response.rp_code[0] == "0":
                self.state = ConnectionState.AUTHENTICATED
                self.reconnect_count = 0  # Reset on successful auth
                logger.info("Rithmic authentication successful")
            else:
                self.state = ConnectionState.FAILED
                logger.error(f"Authentication failed: {response.rp_code}")
                
        except Exception as e:
            logger.error(f"Error handling login response: {e}")
    
    async def _handle_market_data_response(self, msg_buf: bytes):
        """Handle market data subscription response."""
        try:
            response = response_market_data_update_pb2.ResponseMarketDataUpdate()
            response.ParseFromString(msg_buf)
            
            if len(response.rp_code) > 0:
                if response.rp_code[0] == "0":
                    logger.debug(f"Market data subscription confirmed: {response.symbol}")
                else:
                    logger.warning(f"Market data subscription failed: {response.symbol} - {response.rp_code}")
                    
        except Exception as e:
            logger.error(f"Error handling market data response: {e}")
    
    async def _handle_last_trade(self, msg_buf: bytes):
        """Handle last trade message."""
        try:
            trade = last_trade_pb2.LastTrade()
            trade.ParseFromString(msg_buf)
            
            symbol = trade.symbol
            price = trade.trade_price if hasattr(trade, 'trade_price') else 0.0
            volume = trade.trade_size if hasattr(trade, 'trade_size') else 0
            
            # Skip invalid trades
            if price <= 0 or volume <= 0:
                return
            
            # Update statistics
            self.stats['trades_received'] += 1
            self.stats['last_data_time'] = datetime.now()
            
            # Update current price
            self.current_prices[symbol] = price
            
            # Determine trade side based on bid/ask
            trade_side = self._determine_trade_side(symbol, price)
            
            # Create market data object
            market_data = MarketData(
                symbol=symbol,
                price=price,
                volume=volume,
                bid=self.bid_prices.get(symbol, 0.0),
                ask=self.ask_prices.get(symbol, 0.0),
                timestamp=datetime.now().isoformat(),
                trade_side=trade_side
            )
            
            # Store last trade
            self.last_trades[symbol] = market_data
            
            # Notify callbacks
            await self._notify_market_data(symbol, market_data)
            
            # Log periodic updates (every 50th trade to reduce spam)
            if self.stats['trades_received'] % 50 == 0:
                logger.info(f"Market data: {symbol} @ {price} x {volume} ({trade_side})")
                
        except Exception as e:
            logger.error(f"Error handling last trade: {e}")
    
    async def _handle_best_bid_offer(self, msg_buf: bytes):
        """Handle best bid/offer message."""
        try:
            bbo = best_bid_offer_pb2.BestBidOffer()
            bbo.ParseFromString(msg_buf)
            
            symbol = bbo.symbol
            
            # Update bid/ask prices
            self.bid_prices[symbol] = bbo.bid_price
            self.ask_prices[symbol] = bbo.ask_price
            
            # Update statistics
            self.stats['quotes_received'] += 1
            self.stats['last_data_time'] = datetime.now()
            
            # Create market data object for quote
            market_data = MarketData(
                symbol=symbol,
                price=self.current_prices.get(symbol, 0.0),
                volume=0,  # No volume for quotes
                bid=bbo.bid_price,
                ask=bbo.ask_price,
                timestamp=datetime.now().isoformat(),
                trade_side="quote"
            )
            
            # Notify callbacks
            await self._notify_market_data(symbol, market_data)
            
        except Exception as e:
            logger.error(f"Error handling BBO: {e}")
    
    def _determine_trade_side(self, symbol: str, price: float) -> str:
        """Determine if trade was a buy or sell based on bid/ask."""
        bid = self.bid_prices.get(symbol, 0)
        ask = self.ask_prices.get(symbol, 0)
        
        if bid > 0 and ask > 0:
            if price <= bid:
                return 'sell'
            elif price >= ask:
                return 'buy'
            else:
                # Between bid/ask - use price movement
                prev_price = self.current_prices.get(symbol, price)
                if price > prev_price:
                    return 'buy'
                elif price < prev_price:
                    return 'sell'
                else:
                    # Same price - use distance from bid/ask
                    return 'sell' if abs(price - bid) < abs(price - ask) else 'buy'
        else:
            # No bid/ask - use price movement
            prev_price = self.current_prices.get(symbol, price)
            if price > prev_price:
                return 'buy'
            elif price < prev_price:
                return 'sell'
            else:
                return 'unknown'
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to keep connection alive."""
        try:
            while self.state == ConnectionState.AUTHENTICATED:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                if self.state == ConnectionState.AUTHENTICATED and self.ws:
                    try:
                        heartbeat = request_heartbeat_pb2.RequestHeartbeat()
                        heartbeat.template_id = 18
                        await self._send_message(heartbeat)
                        logger.debug("Sent heartbeat")
                    except Exception as e:
                        logger.warning(f"Heartbeat failed: {e}")
                        break
                        
        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
    
    async def _schedule_reconnect(self):
        """Schedule automatic reconnection."""
        if self.reconnect_count >= self.config.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.config.max_reconnect_attempts}) exceeded")
            self.state = ConnectionState.FAILED
            await self._notify_connection_state(ConnectionState.FAILED)
            return
        
        self.state = ConnectionState.RECONNECTING
        await self._notify_connection_state(ConnectionState.RECONNECTING)
        
        self.reconnect_count += 1
        delay = self.config.reconnect_delay * self.reconnect_count  # Exponential backoff
        
        logger.info(f"Reconnecting in {delay} seconds (attempt {self.reconnect_count}/{self.config.max_reconnect_attempts})")
        
        try:
            await asyncio.sleep(delay)
            await self.disconnect()  # Clean disconnect first
            await asyncio.sleep(1)
            await self.connect()     # Reconnect
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            await self._schedule_reconnect()  # Try again
    
    # Public API Methods
    
    def add_market_data_callback(self, symbol: str, callback: Callable[[MarketData], Any]):
        """Add a callback for market data updates."""
        if symbol not in self.market_data_callbacks:
            self.market_data_callbacks[symbol] = []
        self.market_data_callbacks[symbol].append(callback)
        logger.debug(f"Added market data callback for {symbol}")
    
    def add_connection_callback(self, callback: Callable[[ConnectionState], Any]):
        """Add a callback for connection state changes."""
        self.connection_callbacks.append(callback)
        logger.debug("Added connection state callback")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        return self.current_prices.get(symbol)
    
    def get_bid_ask(self, symbol: str) -> tuple[float, float]:
        """Get current bid/ask for a symbol."""
        return (self.bid_prices.get(symbol, 0.0), self.ask_prices.get(symbol, 0.0))
    
    def get_last_trade(self, symbol: str) -> Optional[MarketData]:
        """Get last trade data for a symbol."""
        return self.last_trades.get(symbol)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection and data statistics."""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'connection_state': self.state.value,
            'reconnect_count': self.reconnect_count,
            'uptime_seconds': int(uptime.total_seconds()),
            'symbols_tracked': list(self.current_prices.keys()),
            'is_connected': self.state == ConnectionState.AUTHENTICATED
        }
    
    def is_connected(self) -> bool:
        """Check if client is connected and authenticated."""
        return self.state == ConnectionState.AUTHENTICATED
    
    # Internal callback notification methods
    
    async def _notify_market_data(self, symbol: str, data: MarketData):
        """Notify market data callbacks."""
        if symbol in self.market_data_callbacks:
            for callback in self.market_data_callbacks[symbol]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Market data callback error: {e}")
    
    async def _notify_connection_state(self, state: ConnectionState):
        """Notify connection state callbacks."""
        for callback in self.connection_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                logger.error(f"Connection callback error: {e}")


# Utility functions for easy configuration

def create_rithmic_client(username: str, 
                         password: str, 
                         symbols: List[str] = None,
                         environment: str = "test") -> RithmicClientV2:
    """Create a Rithmic client with standard configuration."""
    if symbols is None:
        symbols = ['ES', 'NQ']
    
    # Set URI based on environment
    if environment == "prod":
        uri = "wss://rithmic01.rithmic.com:443"
    else:
        uri = "wss://rituz00100.rithmic.com:443"  # Test environment
    
    config = RithmicConfig(
        username=username,
        password=password,
        symbols=symbols,
        uri=uri
    )
    
    return RithmicClientV2(config)


def create_rithmic_client_from_env() -> RithmicClientV2:
    """Create a Rithmic client from environment variables (using original naming convention)."""
    username = os.getenv('RITHMIC_USERNAME')
    password = os.getenv('RITHMIC_PASSWORD')
    system_name = os.getenv('RITHMIC_SYSTEM_NAME', 'Rithmic Test')
    uri = os.getenv('RITHMIC_URI', 'wss://rituz00100.rithmic.com:443')
    environment = os.getenv('RITHMIC_ENVIRONMENT', 'test')
    symbols = os.getenv('RITHMIC_SYMBOLS', 'ES,NQ').split(',')
    
    if not username or not password:
        raise ValueError("RITHMIC_USERNAME and RITHMIC_PASSWORD environment variables required")
    
    config = RithmicConfig(
        username=username,
        password=password,
        uri=uri,
        system_name=system_name,
        symbols=symbols,
        exchanges=['CME'] * len(symbols)  # Default all to CME
    )
    
    return RithmicClientV2(config)