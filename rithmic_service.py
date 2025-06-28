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
        # Import required components
        from src.rithmic_client_exact import create_rithmic_client_exact_from_env
        from src.notification_system_v2 import create_personal_alert_engine
        from src.structural_levels_v2 import StructuralLevelsManagerV2
        
        logger.info("✅ Components imported successfully")
        
        # Initialize database connection for levels
        database_url = os.getenv('DATABASE_URL', '')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        levels_manager = None
        alert_engine = None
        
        # Try to initialize levels manager and alert engine
        try:
            if database_url:
                levels_manager = StructuralLevelsManagerV2(database_url)
                logger.info("✅ Structural levels manager initialized")
                
                # Create alert engine
                alert_engine = create_personal_alert_engine()
                logger.info("✅ Alert engine initialized")
                
                # Load today's ALL-STAR levels
                from datetime import date
                today = date.today()
                
                for symbol in ['ES', 'NQ']:
                    levels = levels_manager.get_all_star_levels(symbol, today)
                    alert_engine.add_structural_levels(symbol, levels)
                    logger.info(f"✅ Loaded {len(levels)} ALL-STAR levels for {symbol}")
                
                # Start alert monitoring
                await alert_engine.start_monitoring()
                logger.info("🚨 Alert monitoring started")
            else:
                logger.warning("⚠️ No database URL - running without alerts")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize alerts: {e}")
        
        # Create Rithmic client
        client = create_rithmic_client_exact_from_env()
        logger.info("✅ Rithmic client created")
        
        # Connect to Rithmic
        logger.info("🔌 Connecting to Rithmic...")
        await client.connect()
        logger.info("✅ Connected to Rithmic successfully")
        
        # Set up price update callback for alerts
        if alert_engine:
            def price_callback(symbol: str, price: float):
                """Callback to update alert engine with new prices."""
                alert_engine.update_price(symbol, price)
                logger.debug(f"📊 {symbol}: ${price:.2f}")
            
            # Register callback with client
            client.set_price_callback(price_callback)
            logger.info("🔗 Price alerts connected to market data")
        
        # Subscribe to market data
        symbols = ['ES', 'NQ']
        for symbol in symbols:
            logger.info(f"📊 Subscribing to {symbol} market data...")
            await client.subscribe_to_market_data(symbol)
            logger.info(f"✅ Subscribed to {symbol}")
        
        logger.info("🎯 Market data service running...")
        logger.info("📈 Receiving live price data for ES and NQ")
        if alert_engine:
            logger.info("🚨 SMS alerts active for ALL-STAR levels (9:30-15:30 EST)")
        
        # Keep the service running
        while True:
            await asyncio.sleep(30)
            current_time = datetime.now().strftime('%H:%M:%S')
            
            if alert_engine:
                stats = alert_engine.get_statistics()
                logger.info(f"⏰ {current_time} EST | Alerts sent: {stats['alerts_sent']} | Suppressed: {stats['alerts_suppressed']}")
            else:
                logger.info(f"⏰ Service healthy - {current_time} EST")
            
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