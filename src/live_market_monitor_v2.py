"""
Live Market Monitor for xFGv2
Integrates RithmicClientV2 with structural levels system to provide:
- Live price monitoring against structural levels
- Level touch detection and logging
- Price proximity alerts
- Real-time level validation
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .rithmic_client_v2 import RithmicClientV2, RithmicConfig, MarketData, ConnectionState
from .structural_levels_v2 import StructuralLevelsManagerV2, LevelType, LevelPriority

logger = logging.getLogger(__name__)


class LevelTouchType(Enum):
    """Types of level interactions."""
    APPROACH = "approach"      # Price approaching level
    TOUCH = "touch"           # Price touching level
    BREACH = "breach"         # Price breaking through level
    BOUNCE = "bounce"         # Price bouncing off level


@dataclass
class LevelInteraction:
    """Level interaction event."""
    symbol: str
    price: float
    level_type: str
    level_price: float
    interaction_type: LevelTouchType
    timestamp: str
    distance: float
    priority: str
    volume: int = 0
    trade_side: str = "unknown"


@dataclass
class MarketMonitorConfig:
    """Configuration for live market monitoring."""
    # Rithmic configuration
    rithmic_config: RithmicConfig
    
    # Database connection
    database_url: str
    
    # Monitoring settings
    proximity_threshold: float = 2.0      # Points for proximity alerts
    touch_threshold: float = 0.25         # Points for touch detection
    breach_threshold: float = 0.5         # Points for breach detection
    
    # Update intervals
    level_check_interval: float = 1.0     # Seconds between level checks
    stats_log_interval: int = 300         # Seconds between stats logs
    
    # Symbols to monitor
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ['ES', 'NQ']


class LiveMarketMonitorV2:
    """
    Live market monitor that integrates Rithmic data with structural levels.
    
    Features:
    - Real-time price monitoring against levels
    - Level touch detection and logging  
    - Proximity alerts for approaching levels
    - Statistics and performance tracking
    - Integration with xFGv2 levels system
    """
    
    def __init__(self, config: MarketMonitorConfig):
        """Initialize the live market monitor."""
        self.config = config
        
        # Initialize components
        self.rithmic_client = RithmicClientV2(config.rithmic_config)
        self.levels_manager = StructuralLevelsManagerV2(config.database_url)
        
        # State tracking
        self.is_monitoring = False
        self.current_levels = {}    # {symbol: {level_type: price}}
        self.level_interactions = []  # Recent interactions
        self.last_prices = {}       # {symbol: price}
        self.last_level_check = {}  # {symbol: datetime}
        
        # Statistics
        self.stats = {
            'level_touches': 0,
            'level_breaches': 0,
            'proximity_alerts': 0,
            'price_updates': 0,
            'start_time': datetime.now()
        }
        
        # Callbacks
        self.level_interaction_callbacks = []
        self.proximity_alert_callbacks = []
        
        # Background tasks
        self.monitor_task = None
        self.stats_task = None
        
        logger.info(f"LiveMarketMonitorV2 initialized for symbols: {config.symbols}")
    
    async def start(self) -> bool:
        """Start live market monitoring."""
        try:
            logger.info("🚀 Starting live market monitoring...")
            
            # Connect to Rithmic
            self.rithmic_client.add_connection_callback(self._on_connection_state)
            
            for symbol in self.config.symbols:
                self.rithmic_client.add_market_data_callback(symbol, self._on_market_data)
            
            if not await self.rithmic_client.connect():
                logger.error("Failed to connect to Rithmic")
                return False
            
            # Load current levels
            await self._load_current_levels()
            
            # Start monitoring tasks
            self.is_monitoring = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            self.stats_task = asyncio.create_task(self._stats_loop())
            
            logger.info("✅ Live market monitoring started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return False
    
    async def stop(self):
        """Stop live market monitoring."""
        logger.info("⏹️ Stopping live market monitoring...")
        
        self.is_monitoring = False
        
        # Cancel background tasks
        for task in [self.monitor_task, self.stats_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Disconnect from Rithmic
        await self.rithmic_client.disconnect()
        
        logger.info("✅ Live market monitoring stopped")
    
    async def _load_current_levels(self):
        """Load current structural levels for all symbols."""
        try:
            today = date.today()
            
            for symbol in self.config.symbols:
                levels = self.levels_manager.get_levels_for_date(symbol, today)
                self.current_levels[symbol] = levels
                
                level_count = len(levels)
                all_star_count = len([l for l in levels.items() if self._get_level_priority(l[0]) == LevelPriority.ALL_STAR])
                
                logger.info(f"📊 Loaded {level_count} levels for {symbol} ({all_star_count} ALL-STAR)")
                
        except Exception as e:
            logger.error(f"Error loading levels: {e}")
    
    def _get_level_priority(self, level_type: str) -> LevelPriority:
        """Get priority for a level type."""
        # ALL-STAR levels from CSV
        all_star_csv = ['mgi_wk_op', 'mgi_pm_vah', 'mgi_pm_val', 'mgi_pw_vah', 'mgi_pw_val', 'mgi_onh', 'mgi_onl']
        
        # ALL-STAR manual levels
        all_star_manual = ['pivot', 'pivot_high', 'pivot_low', 'pivot_ba_high', 'pivot_ba_low', 'weekly_pivot']
        
        if level_type in all_star_csv or level_type in all_star_manual:
            return LevelPriority.ALL_STAR
        elif level_type.startswith('mgi_ib'):
            return LevelPriority.REFERENCE
        else:
            return LevelPriority.STANDARD
    
    async def _on_connection_state(self, state: ConnectionState):
        """Handle Rithmic connection state changes."""
        logger.info(f"🔗 Rithmic connection: {state.value}")
        
        if state == ConnectionState.AUTHENTICATED:
            logger.info("✅ Rithmic authenticated - live data ready")
            await self._load_current_levels()  # Reload levels on reconnection
        elif state == ConnectionState.FAILED:
            logger.error("❌ Rithmic connection failed")
        elif state == ConnectionState.RECONNECTING:
            logger.warning("🔄 Rithmic reconnecting...")
    
    async def _on_market_data(self, data: MarketData):
        """Handle market data updates from Rithmic."""
        try:
            symbol = data.symbol
            price = data.price
            
            # Skip quotes (we only process trades)
            if data.trade_side == "quote":
                return
            
            self.stats['price_updates'] += 1
            
            # Check for level interactions
            if symbol in self.current_levels:
                await self._check_level_interactions(symbol, data)
            
            # Update last price
            self.last_prices[symbol] = price
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    async def _check_level_interactions(self, symbol: str, data: MarketData):
        """Check for interactions with structural levels."""
        try:
            current_price = data.price
            symbol_levels = self.current_levels.get(symbol, {})
            
            if not symbol_levels:
                return
            
            # Check each level for interactions
            for level_type, level_price in symbol_levels.items():
                if level_price is None or level_price <= 0:
                    continue
                
                distance = abs(current_price - level_price)
                priority = self._get_level_priority(level_type)
                
                # Determine interaction type
                interaction_type = None
                
                if distance <= self.config.touch_threshold:
                    interaction_type = LevelTouchType.TOUCH
                    self.stats['level_touches'] += 1
                    
                    # Check for breach
                    last_price = self.last_prices.get(symbol, current_price)
                    if ((last_price < level_price and current_price > level_price + self.config.breach_threshold) or
                        (last_price > level_price and current_price < level_price - self.config.breach_threshold)):
                        interaction_type = LevelTouchType.BREACH
                        self.stats['level_breaches'] += 1
                    
                elif distance <= self.config.proximity_threshold:
                    interaction_type = LevelTouchType.APPROACH
                    self.stats['proximity_alerts'] += 1
                
                # Log significant interactions
                if interaction_type:
                    await self._log_level_interaction(
                        symbol, data, level_type, level_price, 
                        interaction_type, distance, priority
                    )
                    
        except Exception as e:
            logger.error(f"Error checking level interactions: {e}")
    
    async def _log_level_interaction(self, symbol: str, data: MarketData, 
                                   level_type: str, level_price: float,
                                   interaction_type: LevelTouchType, 
                                   distance: float, priority: LevelPriority):
        """Log a level interaction event."""
        try:
            interaction = LevelInteraction(
                symbol=symbol,
                price=data.price,
                level_type=level_type,
                level_price=level_price,
                interaction_type=interaction_type,
                timestamp=data.timestamp,
                distance=distance,
                priority=priority.value,
                volume=data.volume,
                trade_side=data.trade_side
            )
            
            # Add to recent interactions
            self.level_interactions.append(interaction)
            
            # Keep only last 1000 interactions
            if len(self.level_interactions) > 1000:
                self.level_interactions = self.level_interactions[-1000:]
            
            # Log based on priority and interaction type
            if priority == LevelPriority.ALL_STAR or interaction_type == LevelTouchType.BREACH:
                logger.info(f"🎯 {interaction_type.value.upper()}: {symbol} @ {data.price} "
                           f"vs {level_type} @ {level_price} (⭐ {priority.value}, "
                           f"dist: {distance:.2f}, side: {data.trade_side})")
            
            # Update level touch count in database
            if interaction_type in [LevelTouchType.TOUCH, LevelTouchType.BREACH]:
                try:
                    # This would require adding a method to structural_levels_v2.py
                    # self.levels_manager.record_level_touch(symbol, level_type, data.price, data.timestamp)
                    pass
                except Exception as e:
                    logger.debug(f"Could not update level touch count: {e}")
            
            # Notify callbacks
            await self._notify_interaction_callbacks(interaction)
            
        except Exception as e:
            logger.error(f"Error logging level interaction: {e}")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        try:
            while self.is_monitoring:
                await asyncio.sleep(self.config.level_check_interval)
                
                # Reload levels periodically (every 5 minutes)
                if not hasattr(self, '_last_level_reload'):
                    self._last_level_reload = datetime.now()
                
                if (datetime.now() - self._last_level_reload).total_seconds() > 300:
                    await self._load_current_levels()
                    self._last_level_reload = datetime.now()
                    
        except asyncio.CancelledError:
            logger.debug("Monitor loop cancelled")
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
    
    async def _stats_loop(self):
        """Periodic statistics logging."""
        try:
            while self.is_monitoring:
                await asyncio.sleep(self.config.stats_log_interval)
                
                # Log statistics
                rithmic_stats = self.rithmic_client.get_statistics()
                uptime = datetime.now() - self.stats['start_time']
                
                logger.info(f"📈 Monitor Stats - Uptime: {int(uptime.total_seconds())}s, "
                           f"Prices: {self.stats['price_updates']}, "
                           f"Touches: {self.stats['level_touches']}, "
                           f"Breaches: {self.stats['level_breaches']}, "
                           f"Rithmic Trades: {rithmic_stats['trades_received']}")
                
                # Log current prices
                for symbol in self.config.symbols:
                    price = self.rithmic_client.get_current_price(symbol)
                    if price:
                        bid, ask = self.rithmic_client.get_bid_ask(symbol)
                        logger.info(f"💰 {symbol}: {price} (Bid: {bid}, Ask: {ask})")
                        
        except asyncio.CancelledError:
            logger.debug("Stats loop cancelled")
        except Exception as e:
            logger.error(f"Stats loop error: {e}")
    
    async def _notify_interaction_callbacks(self, interaction: LevelInteraction):
        """Notify level interaction callbacks."""
        for callback in self.level_interaction_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(interaction)
                else:
                    callback(interaction)
            except Exception as e:
                logger.error(f"Interaction callback error: {e}")
    
    # Public API Methods
    
    def add_level_interaction_callback(self, callback: Callable[[LevelInteraction], Any]):
        """Add callback for level interactions."""
        self.level_interaction_callbacks.append(callback)
        logger.debug("Added level interaction callback")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        return self.rithmic_client.get_current_price(symbol)
    
    def get_current_levels(self, symbol: str) -> Dict[str, float]:
        """Get current structural levels for symbol."""
        return self.current_levels.get(symbol, {})
    
    def get_recent_interactions(self, symbol: str = None, count: int = 100) -> List[LevelInteraction]:
        """Get recent level interactions."""
        interactions = self.level_interactions
        
        if symbol:
            interactions = [i for i in interactions if i.symbol == symbol]
        
        return interactions[-count:] if len(interactions) > count else interactions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        rithmic_stats = self.rithmic_client.get_statistics()
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            **self.stats,
            'uptime_seconds': int(uptime.total_seconds()),
            'is_monitoring': self.is_monitoring,
            'symbols_monitored': self.config.symbols,
            'levels_loaded': {symbol: len(levels) for symbol, levels in self.current_levels.items()},
            'rithmic_stats': rithmic_stats
        }
    
    def is_connected(self) -> bool:
        """Check if monitoring is active and connected."""
        return self.is_monitoring and self.rithmic_client.is_connected()


# Utility functions

def create_market_monitor(username: str, password: str, database_url: str,
                         symbols: List[str] = None, environment: str = "test") -> LiveMarketMonitorV2:
    """Create a live market monitor with standard configuration."""
    if symbols is None:
        symbols = ['ES', 'NQ']
    
    rithmic_config = RithmicConfig(
        username=username,
        password=password,
        symbols=symbols,
        uri="wss://rituz00100.rithmic.com:443" if environment == "test" else "wss://rithmic01.rithmic.com:443"
    )
    
    monitor_config = MarketMonitorConfig(
        rithmic_config=rithmic_config,
        database_url=database_url,
        symbols=symbols
    )
    
    return LiveMarketMonitorV2(monitor_config)


def create_market_monitor_from_env() -> LiveMarketMonitorV2:
    """Create market monitor from environment variables (using original naming convention)."""
    import os
    
    username = os.getenv('RITHMIC_USERNAME')
    password = os.getenv('RITHMIC_PASSWORD')
    system_name = os.getenv('RITHMIC_SYSTEM_NAME', 'Rithmic Test')
    uri = os.getenv('RITHMIC_URI', 'wss://rituz00100.rithmic.com:443')
    environment = os.getenv('RITHMIC_ENVIRONMENT', 'test')
    database_url = os.getenv('DATABASE_URL')
    symbols = os.getenv('RITHMIC_SYMBOLS', 'ES,NQ').split(',')
    
    if not all([username, password, database_url]):
        raise ValueError("Required environment variables: RITHMIC_USERNAME, RITHMIC_PASSWORD, DATABASE_URL")
    
    rithmic_config = RithmicConfig(
        username=username,
        password=password,
        uri=uri,
        system_name=system_name,
        symbols=symbols,
        exchanges=['CME'] * len(symbols)
    )
    
    monitor_config = MarketMonitorConfig(
        rithmic_config=rithmic_config,
        database_url=database_url,
        symbols=symbols
    )
    
    return LiveMarketMonitorV2(monitor_config)