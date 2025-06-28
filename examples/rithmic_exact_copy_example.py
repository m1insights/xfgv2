"""
Example: Using RithmicClientExact for Live ES/NQ Market Data
This uses the EXACT COPY of your working Rithmic connection code.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.rithmic_client_exact import RithmicClientExact, create_rithmic_client_exact_from_env, create_rithmic_client_exact

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ExactDataHandler:
    """Example handler for live market data using exact copy."""
    
    def __init__(self):
        self.trade_count = 0
        
    async def on_market_data(self, data):
        """Handle market data updates."""
        if data['type'] == 'trade':
            self.trade_count += 1
            
            # Log every 10th trade to avoid spam
            if self.trade_count % 10 == 0:
                logger.info(f"📊 {data['symbol']}: {data['price']} x {data['volume']} "
                           f"({data['trade_side']})")
        
        elif data['type'] == 'quote':
            # Log quotes less frequently
            if self.trade_count % 50 == 0:
                logger.info(f"💰 {data['symbol']}: Bid {data['bid']} Ask {data['ask']}")


async def main_exact():
    """Main example using EXACT copy of working Rithmic code."""
    logger.info("🚀 Starting Rithmic EXACT Copy Example")
    
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
        return
    
    # Create data handler
    handler = ExactDataHandler()
    
    # Create EXACT copy Rithmic client
    client = RithmicClientExact(
        username=username,
        password=password,
        uri=uri,
        system_name=system_name
    )
    
    # Add callbacks for both ES and NQ
    client.add_market_data_callback('ES', handler.on_market_data)
    client.add_market_data_callback('NQ', handler.on_market_data)
    
    try:
        # Connect to Rithmic (EXACT same logic as working system)
        logger.info("📡 Connecting to Rithmic (exact copy logic)...")
        if await client.connect():
            logger.info("✅ Connected successfully!")
            
            # Authenticate (EXACT same logic as working system)
            if await client.authenticate():
                logger.info("🔐 Authenticated successfully!")
                
                # Subscribe to market data for ES and NQ (EXACT same logic)
                await client.subscribe_market_data('ES', 'CME')
                await client.subscribe_market_data('NQ', 'CME')
                
                logger.info("📈 Receiving live market data for 60 seconds...")
                
                # Monitor for 60 seconds
                start_time = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_time < 60:
                    await asyncio.sleep(1)
                    
                    # Print periodic status
                    if int(asyncio.get_event_loop().time() - start_time) % 10 == 0:
                        es_price = client.get_current_price('ES')
                        nq_price = client.get_current_price('NQ')
                        if es_price:
                            logger.info(f"💰 Current - ES: {es_price}, NQ: {nq_price}")
                
                logger.info("✅ EXACT copy example completed successfully!")
                
            else:
                logger.error("❌ Authentication failed")
        else:
            logger.error("❌ Connection failed")
            
    except KeyboardInterrupt:
        logger.info("⏹️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Example error: {e}")
    finally:
        # Clean disconnect
        await client.disconnect()
        logger.info("👋 Disconnected from Rithmic")


async def simple_exact_test():
    """Simple test using environment variables with exact copy."""
    logger.info("🔍 Simple EXACT Copy Test")
    
    try:
        # Use exact copy from environment
        client = create_rithmic_client_exact_from_env()
        
        # Test connection
        if await client.connect():
            if await client.authenticate():
                logger.info("✅ EXACT copy connection test successful!")
                
                # Subscribe to ES only for quick test
                await client.subscribe_market_data('ES', 'CME')
                
                # Monitor for 10 seconds
                await asyncio.sleep(10)
                
                es_price = client.get_current_price('ES')
                if es_price:
                    logger.info(f"📊 ES Price from exact copy: {es_price}")
                else:
                    logger.warning("⚠️  No price data received yet")
                    
            else:
                logger.error("❌ Authentication failed")
        else:
            logger.error("❌ Connection failed")
            
        await client.disconnect()
        
    except ValueError as e:
        logger.error(f"❌ Environment setup error: {e}")
    except Exception as e:
        logger.error(f"❌ Test error: {e}")


if __name__ == "__main__":
    print("="*70)
    print("🚀 Rithmic EXACT Copy Example for xFGv2")
    print("="*70)
    print("This uses the EXACT SAME connection logic from your working system")
    print("="*70)
    print("1. Full example with live data monitoring")
    print("2. Simple connection test")
    print("="*70)
    
    choice = input("Select example (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(simple_exact_test())
    else:
        asyncio.run(main_exact())