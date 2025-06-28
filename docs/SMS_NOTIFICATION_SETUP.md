# xFGv2 SMS Notification System Setup Guide

## 🎯 Overview

The xFGv2 SMS notification system sends you instant text message alerts when price approaches your prioritized structural levels. Perfect for staying informed about market opportunities wherever you are in the world.

## 📋 Prerequisites

### 1. Twilio Account Setup
1. Go to [Twilio Console](https://console.twilio.com/)
2. Sign up for a free account (includes $15 credit)
3. Get a phone number (required for sending SMS)
4. Note your Account SID and Auth Token

### 2. Install Dependencies
```bash
cd xfgv2
pip install twilio
```

## ⚙️ Configuration

### 1. Set Environment Variables
```bash
# Twilio credentials
export TWILIO_ACCOUNT_SID="your_account_sid_here"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_FROM_PHONE="+1234567890"  # Your Twilio number
export TWILIO_TO_PHONE="+1987654321"    # Your personal number

# Rithmic credentials (for live data)
export RITHMIC_USERNAME="your_username"
export RITHMIC_PASSWORD="your_password"
export RITHMIC_SYSTEM_NAME="Rithmic Test"
export RITHMIC_URI="wss://rituz00100.rithmic.com:443"
```

### 2. Test SMS Setup
```bash
cd xfgv2/examples
python sms_alert_example.py
# Choose option 1 to test SMS
```

## 🚀 Usage Examples

### Basic Setup
```python
from src.notification_system_v2 import (
    create_personal_alert_engine, StructuralLevel, AlertPriority
)

# Create alert engine
engine = create_personal_alert_engine()

# Add structural levels
es_support = StructuralLevel(
    symbol="ES",
    price=4450.0,
    level_type="support",
    priority=AlertPriority.HIGH,
    timeframe="1h",
    strength=0.9,
    alert_distance=3.0  # Alert when within 3 points
)

engine.add_structural_level(es_support)

# Start monitoring
await engine.start_monitoring()
```

### Live Trading Integration
```python
# Connect to live market data
from src.rithmic_client_exact import create_rithmic_client_exact_from_env

rithmic_client = create_rithmic_client_exact_from_env()

# Add price update callback
def update_alerts(data):
    if data['type'] == 'trade':
        engine.update_price(data['symbol'], data['price'])

rithmic_client.add_market_data_callback('ES', update_alerts)

# Connect and monitor
await rithmic_client.connect()
await rithmic_client.authenticate()
await rithmic_client.subscribe_market_data('ES', 'CME')
```

## 📱 Alert Types

### 1. Structural Level Alerts
- **Approaching Level**: Price within specified distance
- **Level Break**: Price breaks through level
- **Volume Spike**: High volume at level

### 2. Custom Rules
- **Breakout Alerts**: Price above/below specific levels
- **Time-based**: Only during market hours
- **Priority Filtering**: High-priority symbols only

## 🎛️ Alert Configuration

### Priority Levels
- **CRITICAL**: 🚨 Immediate attention (major breakouts)
- **HIGH**: ⚠️ Important levels (primary S/R)
- **MEDIUM**: Standard structural levels
- **LOW**: Minor levels or confirmations

### Distance Settings
```python
# Alert when price is within distance of level
level.alert_distance = 2.0  # 2 points for ES
level.alert_distance = 5.0  # 5 points for NQ
```

### Cooldown Prevention
```python
# Prevent spam - minimum time between same alerts
level.alert_cooldown_minutes = 15  # 15 minutes default
```

## 🔧 Advanced Features

### Market Hours Filtering
```python
# Only send alerts during market hours
engine.market_hours_only = True
engine.market_open_hour = 14   # 9:30 AM EST = 14:30 UTC
engine.market_close_hour = 21  # 4:00 PM EST = 21:00 UTC
```

### Daily Limits
```python
# Prevent excessive SMS costs
engine.max_daily_alerts = 50
```

### Symbol Prioritization
```python
# High-priority symbols get reduced distance thresholds
high_priority_symbols = ['ES', 'NQ']
engine.priority_distance_multiplier = 0.8  # 20% closer alerts
```

## 📊 Message Format Examples

### Structural Level Alert
```
ES @ 4452.50 - SUPPORT 4450.00 (below, 2.5pts away) [1h]
```

### Breakout Alert  
```
🚨 CRITICAL: ES broke above 4485.00: 4487.25
```

### Volume Spike Alert
```
⚠️ HIGH: NQ volume spike at resistance 15820.00 (2.3x avg)
```

## 🧪 Testing & Validation

### 1. Test SMS Service
```bash
python examples/sms_alert_example.py
# Choose option 1
```

### 2. Simulation Mode
```bash
python examples/sms_alert_example.py  
# Choose option 3
```

### 3. Live Demo
```bash
python examples/sms_alert_example.py
# Choose option 2 (requires Rithmic credentials)
```

## 💰 Cost Considerations

### Twilio Pricing (US)
- SMS: $0.0075 per message
- 50 alerts/day = ~$11.25/month
- International rates vary

### Cost Control Features
- Daily alert limits
- Cooldown periods
- Priority filtering
- Market hours only

## 🔒 Security Best Practices

1. **Environment Variables**: Never hardcode credentials
2. **Rate Limiting**: Built-in cooldowns prevent spam
3. **Validation**: All inputs validated before processing
4. **Error Handling**: Graceful failures without credential exposure

## 🚨 Troubleshooting

### Common Issues

**SMS Not Sending**
```bash
# Check credentials
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN

# Test directly
python -c "
from src.notification_system_v2 import create_sms_service_from_env
import asyncio
sms = create_sms_service_from_env()
asyncio.run(sms.send_sms('Test message'))
"
```

**No Price Updates**
- Check Rithmic credentials
- Verify market hours (futures trade nearly 24/7)
- Check network connectivity

**Too Many Alerts**
```python
# Increase cooldown period
level.alert_cooldown_minutes = 30

# Increase alert distance
level.alert_distance = 5.0

# Add daily limits
engine.max_daily_alerts = 20
```

## 📈 Performance Monitoring

### Statistics Tracking
```python
stats = engine.get_statistics()
print(f"Alerts sent: {stats['alerts_sent']}")
print(f"Levels monitored: {stats['levels_monitored']}")
print(f"Uptime: {stats['uptime_minutes']} minutes")
```

### Health Checks
- Connection status monitoring
- Alert delivery confirmation
- Performance metrics logging

## 🔄 Integration with xFGv2

The SMS system integrates seamlessly with your existing xFGv2 structural levels:

1. **Automated Level Detection**: Import from CSV analysis
2. **Priority Assignment**: Based on level strength/timeframe
3. **Dynamic Updates**: Levels adjust as market structure evolves
4. **Historical Tracking**: Alert performance analytics

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all environment variables are set
3. Test SMS service independently
4. Check Twilio console for delivery status

---

**Ready to get started?**
```bash
cd xfgv2/examples
python sms_alert_example.py
```