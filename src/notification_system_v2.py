"""
xFGv2 SMS Notification System
Sends text message alerts when price approaches prioritized structural levels.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import json

# SMS service imports
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio not installed. Install with: pip install twilio")

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    APPROACHING_LEVEL = "approaching"
    LEVEL_BREAK = "break"
    VOLUME_SPIKE = "volume"
    CUSTOM = "custom"


@dataclass
class StructuralLevel:
    """Represents a structural level with alert configuration."""
    symbol: str
    price: float
    level_type: str  # "support", "resistance", "pivot"
    priority: AlertPriority
    timeframe: str  # "1m", "5m", "1h", "1d"
    strength: float  # 0.0 to 1.0
    created_at: datetime
    alert_distance: float = 2.0  # Points from level to trigger alert
    is_active: bool = True
    last_alert_time: Optional[datetime] = None
    alert_cooldown_minutes: int = 15  # Prevent spam


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    symbol: str
    alert_type: AlertType
    priority: AlertPriority
    conditions: Dict[str, Any]
    is_active: bool = True
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None


@dataclass
class Alert:
    """Alert message to be sent."""
    alert_id: str
    symbol: str
    alert_type: AlertType
    priority: AlertPriority
    message: str
    price: float
    level_price: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SMSNotificationService:
    """SMS notification service using Twilio."""
    
    def __init__(self, 
                 account_sid: str = None,
                 auth_token: str = None, 
                 from_phone: str = None,
                 to_phone: str = None):
        """Initialize SMS service."""
        
        # Get credentials from environment if not provided
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_phone = from_phone or os.getenv('TWILIO_FROM_PHONE')
        self.to_phone = to_phone or os.getenv('TWILIO_TO_PHONE')
        
        if not all([self.account_sid, self.auth_token, self.from_phone, self.to_phone]):
            raise ValueError("Missing Twilio credentials. Set environment variables: "
                           "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE, TWILIO_TO_PHONE")
        
        if not TWILIO_AVAILABLE:
            raise ImportError("Twilio not available. Install with: pip install twilio")
        
        self.client = TwilioClient(self.account_sid, self.auth_token)
        self.sent_messages = []  # Track sent messages
        
        logger.info(f"SMS service initialized. Will send to: {self.to_phone}")
    
    async def send_sms(self, message: str, priority: AlertPriority = AlertPriority.MEDIUM) -> bool:
        """Send SMS message."""
        try:
            # Add priority prefix for urgent alerts
            if priority == AlertPriority.CRITICAL:
                message = f"🚨 CRITICAL: {message}"
            elif priority == AlertPriority.HIGH:
                message = f"⚠️ HIGH: {message}"
            
            # Send via Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=self.to_phone
            )
            
            # Track sent message
            self.sent_messages.append({
                'sid': twilio_message.sid,
                'message': message,
                'priority': priority.value,
                'timestamp': datetime.now(),
                'status': 'sent'
            })
            
            logger.info(f"SMS sent successfully: {twilio_message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def get_message_status(self, message_sid: str) -> str:
        """Get status of sent message."""
        try:
            message = self.client.messages(message_sid).fetch()
            return message.status
        except Exception as e:
            logger.error(f"Failed to get message status: {e}")
            return "unknown"


class AlertEngine:
    """Core alert engine that monitors levels and triggers notifications."""
    
    def __init__(self, sms_service: SMSNotificationService):
        """Initialize alert engine."""
        self.sms_service = sms_service
        
        # Storage
        self.structural_levels: Dict[str, List[StructuralLevel]] = {}  # {symbol: [levels]}
        self.alert_rules: Dict[str, AlertRule] = {}  # {rule_id: rule}
        self.alert_history: List[Alert] = []
        self.current_prices: Dict[str, float] = {}  # {symbol: price}
        
        # State
        self.is_running = False
        self.monitoring_task = None
        
        # Statistics
        self.stats = {
            'alerts_sent': 0,
            'alerts_suppressed': 0,
            'levels_monitored': 0,
            'start_time': datetime.now()
        }
        
        logger.info("Alert engine initialized")
    
    def add_structural_level(self, level: StructuralLevel):
        """Add a structural level to monitor."""
        if level.symbol not in self.structural_levels:
            self.structural_levels[level.symbol] = []
        
        self.structural_levels[level.symbol].append(level)
        self.stats['levels_monitored'] = sum(len(levels) for levels in self.structural_levels.values())
        
        logger.info(f"Added {level.level_type} level for {level.symbol} at {level.price} "
                   f"(Priority: {level.priority.value})")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.rule_id} for {rule.symbol}")
    
    def update_price(self, symbol: str, price: float):
        """Update current price for a symbol."""
        self.current_prices[symbol] = price
        
        # Check alerts when price updates
        if self.is_running:
            asyncio.create_task(self._check_alerts_for_symbol(symbol))
    
    async def start_monitoring(self):
        """Start the alert monitoring loop."""
        if self.is_running:
            logger.warning("Alert monitoring already running")
            return
        
        self.is_running = True
        logger.info("Starting alert monitoring...")
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop alert monitoring."""
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Alert monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        try:
            while self.is_running:
                # Check all symbols for alerts
                for symbol in self.current_prices.keys():
                    await self._check_alerts_for_symbol(symbol)
                
                # Sleep for 1 second between checks
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
    
    async def _check_alerts_for_symbol(self, symbol: str):
        """Check alerts for a specific symbol."""
        if symbol not in self.current_prices:
            return
        
        current_price = self.current_prices[symbol]
        
        # Check structural level alerts
        if symbol in self.structural_levels:
            for level in self.structural_levels[symbol]:
                if not level.is_active:
                    continue
                
                await self._check_level_alert(symbol, current_price, level)
        
        # Check custom alert rules
        for rule in self.alert_rules.values():
            if rule.symbol == symbol and rule.is_active:
                await self._check_rule_alert(symbol, current_price, rule)
    
    async def _check_level_alert(self, symbol: str, current_price: float, level: StructuralLevel):
        """Check if price is near a structural level."""
        distance = abs(current_price - level.price)
        
        # Check if within alert distance
        if distance <= level.alert_distance:
            # Check cooldown
            if self._is_in_cooldown(level.last_alert_time, level.alert_cooldown_minutes):
                return
            
            # Create alert
            direction = "above" if current_price > level.price else "below"
            message = self._format_level_alert(symbol, current_price, level, direction, distance)
            
            alert = Alert(
                alert_id=f"{symbol}_{level.level_type}_{int(level.price)}_{int(datetime.now().timestamp())}",
                symbol=symbol,
                alert_type=AlertType.APPROACHING_LEVEL,
                priority=level.priority,
                message=message,
                price=current_price,
                level_price=level.price
            )
            
            # Send alert
            if await self._send_alert(alert):
                level.last_alert_time = datetime.now()
    
    async def _check_rule_alert(self, symbol: str, current_price: float, rule: AlertRule):
        """Check custom alert rule."""
        # Check cooldown
        if self._is_in_cooldown(rule.last_triggered, rule.cooldown_minutes):
            return
        
        # Check rule conditions (simplified for now)
        triggered = False
        message = ""
        
        if rule.alert_type == AlertType.CUSTOM:
            # Custom logic based on conditions
            if 'price_above' in rule.conditions:
                if current_price > rule.conditions['price_above']:
                    triggered = True
                    message = f"{symbol} broke above {rule.conditions['price_above']}: {current_price}"
            
            elif 'price_below' in rule.conditions:
                if current_price < rule.conditions['price_below']:
                    triggered = True
                    message = f"{symbol} broke below {rule.conditions['price_below']}: {current_price}"
        
        if triggered:
            alert = Alert(
                alert_id=f"{rule.rule_id}_{int(datetime.now().timestamp())}",
                symbol=symbol,
                alert_type=rule.alert_type,
                priority=rule.priority,
                message=message,
                price=current_price
            )
            
            if await self._send_alert(alert):
                rule.last_triggered = datetime.now()
    
    def _format_level_alert(self, symbol: str, price: float, level: StructuralLevel, direction: str, distance: float) -> str:
        """Format structural level alert message."""
        return (f"{symbol} @ {price:.2f} - {level.level_type.upper()} {level.price:.2f} "
               f"({direction}, {distance:.1f}pts away) [{level.timeframe}]")
    
    def _is_in_cooldown(self, last_time: Optional[datetime], cooldown_minutes: int) -> bool:
        """Check if alert is in cooldown period."""
        if last_time is None:
            return False
        
        return datetime.now() - last_time < timedelta(minutes=cooldown_minutes)
    
    async def _send_alert(self, alert: Alert) -> bool:
        """Send an alert via SMS."""
        try:
            success = await self.sms_service.send_sms(alert.message, alert.priority)
            
            if success:
                self.alert_history.append(alert)
                self.stats['alerts_sent'] += 1
                logger.info(f"Alert sent: {alert.message}")
            else:
                self.stats['alerts_suppressed'] += 1
                logger.warning(f"Alert failed to send: {alert.message}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            self.stats['alerts_suppressed'] += 1
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert engine statistics."""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_minutes': int(uptime.total_seconds() / 60),
            'levels_by_symbol': {symbol: len(levels) for symbol, levels in self.structural_levels.items()},
            'active_rules': len([r for r in self.alert_rules.values() if r.is_active]),
            'recent_alerts': len([a for a in self.alert_history if a.timestamp > datetime.now() - timedelta(hours=1)])
        }


# Factory functions for easy setup

def create_sms_service_from_env() -> SMSNotificationService:
    """Create SMS service from environment variables."""
    return SMSNotificationService()


def create_personal_alert_engine() -> AlertEngine:
    """Create alert engine with SMS for personal use."""
    sms_service = create_sms_service_from_env()
    return AlertEngine(sms_service)


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Create alert engine
        engine = create_personal_alert_engine()
        
        # Add some example structural levels
        es_support = StructuralLevel(
            symbol="ES",
            price=4450.0,
            level_type="support",
            priority=AlertPriority.HIGH,
            timeframe="1h",
            strength=0.8,
            alert_distance=3.0,
            created_at=datetime.now()
        )
        
        nq_resistance = StructuralLevel(
            symbol="NQ",
            price=15800.0,
            level_type="resistance", 
            priority=AlertPriority.MEDIUM,
            timeframe="4h",
            strength=0.7,
            alert_distance=5.0,
            created_at=datetime.now()
        )
        
        engine.add_structural_level(es_support)
        engine.add_structural_level(nq_resistance)
        
        # Add custom alert rule
        breakout_rule = AlertRule(
            rule_id="es_breakout_4460",
            symbol="ES",
            alert_type=AlertType.CUSTOM,
            priority=AlertPriority.CRITICAL,
            conditions={'price_above': 4460.0}
        )
        
        engine.add_alert_rule(breakout_rule)
        
        # Start monitoring
        await engine.start_monitoring()
        
        # Simulate price updates
        print("Starting price simulation...")
        try:
            # Simulate ES approaching support
            for price in [4455.0, 4453.0, 4451.0, 4449.0]:
                engine.update_price("ES", price)
                await asyncio.sleep(2)
            
            # Simulate NQ approaching resistance
            for price in [15795.0, 15798.0, 15801.0]:
                engine.update_price("NQ", price)
                await asyncio.sleep(2)
            
            # Simulate ES breakout
            engine.update_price("ES", 4461.0)
            await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            print("Interrupted by user")
        
        finally:
            await engine.stop_monitoring()
            print("Alert engine stopped")
            print(f"Statistics: {engine.get_statistics()}")
    
    # Run if Twilio is available
    if TWILIO_AVAILABLE:
        asyncio.run(main())
    else:
        print("Install Twilio to test SMS functionality: pip install twilio")