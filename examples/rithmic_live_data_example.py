"""
Example: Using RithmicClientV2 for Live ES/NQ Market Data
Demonstrates connecting to Rithmic and receiving live price feeds.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.rithmic_client_v2 import RithmicClientV2, RithmicConfig, MarketData, ConnectionState, create_rithmic_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class LiveDataHandler:
    """Example handler for live market data."""
    
    def __init__(self):
        self.trade_count = 0
        self.quote_count = 0
        
    async def on_market_data(self, data: MarketData):
        """Handle market data updates."""
        self.trade_count += 1
        
        # Log every 10th trade to avoid spam
        if self.trade_count % 10 == 0:
            logger.info(f"📊 {data.symbol}: {data.price} x {data.volume} "
                       f"({data.trade_side}) | Bid: {data.bid} Ask: {data.ask}")
    
    async def on_connection_state(self, state: ConnectionState):
        """Handle connection state changes."""
        logger.info(f"🔗 Connection State: {state.value}")
        
        if state == ConnectionState.AUTHENTICATED:
            logger.info("✅ Ready to receive live market data!")
        elif state == ConnectionState.FAILED:
            logger.error("❌ Connection failed")
        elif state == ConnectionState.RECONNECTING:
            logger.warning("🔄 Reconnecting...")


async def main():
    """Main example function."""
    logger.info("🚀 Starting Rithmic Live Data Example")
    
    # Get credentials from environment (using original working variable names)
    import os
    username = os.getenv('RITHMIC_USERNAME')
    password = os.getenv('RITHMIC_PASSWORD')
    system_name = os.getenv('RITHMIC_SYSTEM_NAME', 'Rithmic Test')
    uri = os.getenv('RITHMIC_URI', 'wss://rituz00100.rithmic.com:443')
    
    if not username or not password:
        logger.error("❌ Please set RITHMIC_USERNAME and RITHMIC_PASSWORD environment variables")
        logger.info("Example (using original working variable names):")
        logger.info("export RITHMIC_USERNAME='your_username'")
        logger.info("export RITHMIC_PASSWORD='your_password'")
        logger.info("export RITHMIC_SYSTEM_NAME='Rithmic Test'")
        logger.info("export RITHMIC_URI='wss://rituz00100.rithmic.com:443'")
        logger.info("export RITHMIC_ENVIRONMENT='test'")
        return
    
    # Create data handler
    handler = LiveDataHandler()
    
    # Create Rithmic client with custom configuration (using working parameters)
    config = RithmicConfig(
        username=username,
        password=password,
        uri=uri,
        system_name=system_name,
        symbols=['ES', 'NQ'],  # Track both ES and NQ
        exchanges=['CME', 'CME'],
        heartbeat_interval=30,
        max_reconnect_attempts=3,
        reconnect_delay=5
    )
    
    client = RithmicClientV2(config)
    
    # Add callbacks
    client.add_market_data_callback('ES', handler.on_market_data)
    client.add_market_data_callback('NQ', handler.on_market_data)
    client.add_connection_callback(handler.on_connection_state)
    
    try:
        # Connect to Rithmic
        logger.info("📡 Connecting to Rithmic...")
        if await client.connect():
            logger.info("✅ Connected successfully!")
            
            # Run for 60 seconds to demonstrate live data
            logger.info("📈 Receiving live market data for 60 seconds...")
            
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < 60:
                await asyncio.sleep(1)
                
                # Print periodic stats
                if int(asyncio.get_event_loop().time() - start_time) % 10 == 0:
                    stats = client.get_statistics()
                    logger.info(f"📊 Stats: {stats['trades_received']} trades, "
                               f"{stats['quotes_received']} quotes received")
                    
                    # Show current prices
                    es_price = client.get_current_price('ES')
                    nq_price = client.get_current_price('NQ')
                    if es_price:
                        logger.info(f"💰 ES: {es_price}, NQ: {nq_price}")
            
            logger.info("✅ Example completed successfully!")
            
        else:
            logger.error("❌ Failed to connect to Rithmic")
            
    except KeyboardInterrupt:
        logger.info("⏹️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Example error: {e}")
    finally:
        # Clean disconnect
        await client.disconnect()
        logger.info("👋 Disconnected from Rithmic")


async def simple_price_monitor():
    """Simplified example - just monitor current prices."""
    logger.info("🔍 Simple Price Monitor Example")
    
    # Use environment variables with original naming
    username = os.getenv('RITHMIC_USERNAME', 'demo')
    password = os.getenv('RITHMIC_PASSWORD', 'demo')
    
    if username == 'demo':
        logger.warning("⚠️  Demo mode - using fake data (set RITHMIC_USERNAME/PASSWORD for real data)")
        
        # Simulate price updates
        for i in range(10):
            es_price = 5825.75 + (i * 0.25)
            nq_price = 18275.50 + (i * 0.75)
            logger.info(f"📊 Simulated Prices - ES: {es_price}, NQ: {nq_price}")
            await asyncio.sleep(2)
        return
    
    # Real Rithmic connection using environment variables
    try:
        client = create_rithmic_client_from_env()
    except ValueError as e:
        logger.error(f"❌ Environment setup error: {e}")
        return
    
    try:
        if await client.connect():
            logger.info("✅ Connected - monitoring prices...")
            
            for _ in range(10):
                es_price = client.get_current_price('ES')
                nq_price = client.get_current_price('NQ')
                es_bid, es_ask = client.get_bid_ask('ES')
                nq_bid, nq_ask = client.get_bid_ask('NQ')
                
                logger.info(f"💰 ES: {es_price} (Bid: {es_bid}, Ask: {es_ask})")
                logger.info(f"💰 NQ: {nq_price} (Bid: {nq_bid}, Ask: {nq_ask})")
                await asyncio.sleep(3)
                
    finally:
        await client.disconnect()


if __name__ == "__main__":
    print("="*60)
    print("🚀 Rithmic Live Data Example for xFGv2")
    print("="*60)
    print("1. Full example with callbacks")
    print("2. Simple price monitor")
    print("="*60)
    
    choice = input("Select example (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(simple_price_monitor())
    else:
        asyncio.run(main())