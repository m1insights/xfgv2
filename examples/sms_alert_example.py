"""
Example: SMS Alert System with xFGv2 Structural Levels
Demonstrates how to set up SMS notifications for structural level alerts.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.notification_system_v2 import (
    AlertEngine, StructuralLevel, AlertRule, AlertPriority, AlertType,
    create_personal_alert_engine
)
from src.rithmic_client_exact import create_rithmic_client_exact_from_env

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class LiveAlertDemo:
    """Demonstrates live SMS alerts with real market data."""
    
    def __init__(self):
        self.alert_engine = None
        self.rithmic_client = None
        
    async def setup_alert_engine(self):
        """Set up the alert engine with example levels."""
        try:
            # Create alert engine
            self.alert_engine = create_personal_alert_engine()
            
            # Add structural levels for ES
            es_levels = [
                StructuralLevel(
                    symbol="ES",
                    price=4450.0,
                    level_type="support",
                    priority=AlertPriority.HIGH,
                    timeframe="1h",
                    strength=0.9,
                    alert_distance=3.0,
                    created_at=datetime.now()
                ),
                StructuralLevel(
                    symbol="ES",
                    price=4480.0,
                    level_type="resistance",
                    priority=AlertPriority.HIGH,
                    timeframe="4h",
                    strength=0.8,
                    alert_distance=2.5,
                    created_at=datetime.now()
                ),
                StructuralLevel(
                    symbol="ES",
                    price=4465.0,
                    level_type="pivot",
                    priority=AlertPriority.MEDIUM,
                    timeframe="1h",
                    strength=0.7,
                    alert_distance=2.0,
                    created_at=datetime.now()
                )
            ]
            
            # Add structural levels for NQ
            nq_levels = [
                StructuralLevel(
                    symbol="NQ",
                    price=15750.0,
                    level_type="support",
                    priority=AlertPriority.HIGH,
                    timeframe="1h",
                    strength=0.85,
                    alert_distance=5.0,
                    created_at=datetime.now()
                ),
                StructuralLevel(
                    symbol="NQ",
                    price=15820.0,
                    level_type="resistance",
                    priority=AlertPriority.HIGH,
                    timeframe="4h",
                    strength=0.9,
                    alert_distance=4.0,
                    created_at=datetime.now()
                )
            ]
            
            # Add all levels to engine
            for level in es_levels + nq_levels:
                self.alert_engine.add_structural_level(level)
            
            # Add custom breakout rules
            breakout_rules = [
                AlertRule(
                    rule_id="es_daily_high_break",
                    symbol="ES",
                    alert_type=AlertType.CUSTOM,
                    priority=AlertPriority.CRITICAL,
                    conditions={'price_above': 4485.0},
                    cooldown_minutes=30
                ),
                AlertRule(
                    rule_id="nq_daily_low_break", 
                    symbol="NQ",
                    alert_type=AlertType.CUSTOM,
                    priority=AlertPriority.CRITICAL,
                    conditions={'price_below': 15700.0},
                    cooldown_minutes=30
                )
            ]
            
            for rule in breakout_rules:
                self.alert_engine.add_alert_rule(rule)
            
            logger.info("Alert engine configured with structural levels and rules")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup alert engine: {e}")
            return False
    
    async def setup_rithmic_connection(self):
        """Set up Rithmic connection for live data."""
        try:
            # Create Rithmic client
            self.rithmic_client = create_rithmic_client_exact_from_env()
            
            # Add callbacks to update alert engine with live prices
            self.rithmic_client.add_market_data_callback('ES', self._on_market_data)
            self.rithmic_client.add_market_data_callback('NQ', self._on_market_data)
            
            # Connect and authenticate
            if await self.rithmic_client.connect():
                if await self.rithmic_client.authenticate():
                    # Subscribe to market data
                    await self.rithmic_client.subscribe_market_data('ES', 'CME')
                    await self.rithmic_client.subscribe_market_data('NQ', 'CME')
                    
                    logger.info("Connected to Rithmic and subscribed to ES/NQ data")
                    return True
                else:
                    logger.error("Rithmic authentication failed")
                    return False
            else:
                logger.error("Rithmic connection failed")
                return False
                
        except ValueError as e:
            logger.error(f"Rithmic setup error: {e}")
            logger.info("Make sure Rithmic environment variables are set:")
            logger.info("RITHMIC_USERNAME, RITHMIC_PASSWORD, RITHMIC_SYSTEM_NAME, RITHMIC_URI")
            return False
        except Exception as e:
            logger.error(f"Failed to setup Rithmic: {e}")
            return False
    
    async def _on_market_data(self, data):
        """Handle market data updates from Rithmic."""
        if data['type'] == 'trade' and self.alert_engine:
            symbol = data['symbol']
            price = data['price']
            
            # Update alert engine with new price
            self.alert_engine.update_price(symbol, price)
            
            # Log price updates (every 20th trade to reduce spam)
            if not hasattr(self, '_trade_count'):
                self._trade_count = {}
            
            if symbol not in self._trade_count:
                self._trade_count[symbol] = 0
            
            self._trade_count[symbol] += 1
            if self._trade_count[symbol] % 20 == 0:
                logger.info(f"Price update: {symbol} @ {price}")
    
    async def run_live_demo(self):
        """Run live demo with real market data."""
        logger.info("🚀 Starting Live SMS Alert Demo")
        logger.info("=" * 50)
        
        # Setup alert engine
        if not await self.setup_alert_engine():
            return
        
        # Setup Rithmic connection
        if not await self.setup_rithmic_connection():
            logger.warning("Running in simulation mode without live data")
            await self.run_simulation_demo()
            return
        
        # Start alert monitoring
        await self.alert_engine.start_monitoring()
        
        try:
            logger.info("📡 Monitoring live market data for alerts...")
            logger.info("📱 SMS alerts will be sent when price approaches structural levels")
            logger.info("Press Ctrl+C to stop")
            
            # Monitor for alerts - runs indefinitely
            while True:
                await asyncio.sleep(10)
                
                # Print periodic status
                stats = self.alert_engine.get_statistics()
                current_prices = self.alert_engine.current_prices
                
                if current_prices:
                    logger.info(f"Status - ES: {current_prices.get('ES', 'N/A')}, "
                               f"NQ: {current_prices.get('NQ', 'N/A')} | "
                               f"Alerts sent: {stats['alerts_sent']}")
                
        except KeyboardInterrupt:
            logger.info("🛑 Demo stopped by user")
        
        finally:
            # Cleanup
            await self.alert_engine.stop_monitoring()
            if self.rithmic_client:
                await self.rithmic_client.disconnect()
            
            # Print final statistics
            final_stats = self.alert_engine.get_statistics()
            logger.info("📊 Final Statistics:")
            for key, value in final_stats.items():
                logger.info(f"  {key}: {value}")
    
    async def run_simulation_demo(self):
        """Run simulation demo with fake price data."""
        logger.info("🎮 Running Simulation Mode")
        
        await self.alert_engine.start_monitoring()
        
        try:
            # Simulate ES price movement toward support
            logger.info("Simulating ES approaching support at 4450...")
            for price in [4460.0, 4455.0, 4452.0, 4449.0, 4447.0]:
                self.alert_engine.update_price("ES", price)
                logger.info(f"ES price update: {price}")
                await asyncio.sleep(3)
            
            # Simulate NQ approaching resistance
            logger.info("Simulating NQ approaching resistance at 15820...")
            for price in [15810.0, 15815.0, 15818.0, 15822.0]:
                self.alert_engine.update_price("NQ", price)
                logger.info(f"NQ price update: {price}")
                await asyncio.sleep(3)
            
            # Simulate breakout
            logger.info("Simulating ES breakout above 4485...")
            self.alert_engine.update_price("ES", 4487.0)
            await asyncio.sleep(3)
            
            logger.info("✅ Simulation complete")
            
        except KeyboardInterrupt:
            logger.info("🛑 Simulation stopped by user")
        
        finally:
            await self.alert_engine.stop_monitoring()


async def test_sms_setup():
    """Test SMS service setup."""
    logger.info("🧪 Testing SMS Setup")
    
    try:
        from src.notification_system_v2 import create_sms_service_from_env
        sms_service = create_sms_service_from_env()
        
        # Send test message
        test_message = f"xFGv2 SMS Alert Test - {datetime.now().strftime('%H:%M:%S')}"
        success = await sms_service.send_sms(test_message, AlertPriority.LOW)
        
        if success:
            logger.info("✅ SMS test successful! Check your phone.")
        else:
            logger.error("❌ SMS test failed")
        
        return success
        
    except Exception as e:
        logger.error(f"SMS setup error: {e}")
        logger.info("Make sure Twilio environment variables are set:")
        logger.info("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE, TWILIO_TO_PHONE")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 xFGv2 SMS Alert System Demo")
    print("=" * 60)
    print("Choose an option:")
    print("1. Test SMS setup")
    print("2. Run live alert demo (requires Rithmic)")
    print("3. Run simulation demo")
    print("=" * 60)
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_sms_setup())
    elif choice == "2":
        demo = LiveAlertDemo()
        asyncio.run(demo.run_live_demo())
    elif choice == "3":
        demo = LiveAlertDemo()
        asyncio.run(demo.run_simulation_demo())
    else:
        print("Invalid choice. Exiting.")