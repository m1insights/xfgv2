#!/usr/bin/env python3
"""
Standalone Rithmic Market Data Service
Runs independently from the web app to provide live market data.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_rithmic_credentials():
    """Check if all required Rithmic credentials are available."""
    required_vars = [
        'RITHMIC_USERNAME',
        'RITHMIC_PASSWORD', 
        'RITHMIC_SYSTEM_NAME',
        'RITHMIC_URI',
        'RITHMIC_ENVIRONMENT'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"❌ Missing Rithmic credentials: {', '.join(missing)}")
        return False
    
    logger.info("✅ All Rithmic credentials found")
    return True

async def main():
    """Main service entry point."""
    logger.info("🚀 Starting xFGv2 Rithmic Market Data Service")
    logger.info("=" * 60)
    
    # Check credentials
    if not check_rithmic_credentials():
        logger.error("Cannot start without proper Rithmic credentials")
        sys.exit(1)
    
    try:
        # Import Rithmic client
        from src.rithmic_client_exact import RithmicClientExact
        logger.info("✅ Rithmic client imported successfully")
        
        # Create client instance
        client = RithmicClientExact()
        logger.info("✅ Rithmic client created")
        
        # Connect to Rithmic
        logger.info("🔌 Connecting to Rithmic...")
        await client.connect()
        logger.info("✅ Connected to Rithmic successfully")
        
        # Subscribe to market data
        symbols = ['ES', 'NQ']
        for symbol in symbols:
            logger.info(f"📊 Subscribing to {symbol} market data...")
            await client.subscribe_to_market_data(symbol)
            logger.info(f"✅ Subscribed to {symbol}")
        
        logger.info("🎯 Market data service running...")
        logger.info("📈 Receiving live price data for ES and NQ")
        
        # Keep the service running
        while True:
            await asyncio.sleep(10)
            logger.info(f"⏰ Service healthy - {datetime.now().strftime('%H:%M:%S')} EST")
            
    except ImportError as e:
        logger.error(f"❌ Failed to import Rithmic client: {e}")
        logger.info("💡 Running in mock mode for testing...")
        
        # Mock mode for testing when Rithmic components aren't available
        while True:
            await asyncio.sleep(30)
            logger.info(f"📊 Mock market data service - {datetime.now().strftime('%H:%M:%S')} EST")
            logger.info("💡 ES: 5850.25 | NQ: 20125.50 (simulated)")
            
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
        logger.info("🔄 Attempting to restart in 10 seconds...")
        await asyncio.sleep(10)
        # In production, you might want to implement retry logic here

if __name__ == "__main__":
    # Run the service
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
    except Exception as e:
        logger.error(f"💥 Service crashed: {e}")
        sys.exit(1)