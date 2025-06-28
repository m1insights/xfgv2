# xFGv2 - Advanced Structural Level Analysis & Trading Notifications 📈

**Real-time structural level detection and SMS alert system for ES/NQ futures trading.**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 🎯 Features

### Core Functionality
- **Real-time Market Data**: Live ES/NQ price feeds via Rithmic API
- **Structural Level Detection**: Advanced support/resistance analysis
- **SMS Notifications**: Instant alerts when price approaches key levels
- **Priority Classification**: High/Medium/Low level importance
- **Web Dashboard**: Real-time monitoring interface

### Trading Intelligence
- **CSV File Monitoring**: Automatic import of new structural levels
- **Multi-timeframe Analysis**: 1m, 5m, 1h, 4h, daily levels
- **Volume Confirmation**: Level strength validation
- **Historical Performance**: Track level accuracy over time

### Notification System
- **Global SMS Alerts**: Stay informed anywhere in the world
- **Smart Filtering**: Cooldown periods prevent spam
- **Priority-based**: Critical alerts get immediate attention
- **Cost Control**: Daily limits and market hours filtering

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Rithmic API (for live market data)
export RITHMIC_USERNAME="your_username"
export RITHMIC_PASSWORD="your_password" 
export RITHMIC_SYSTEM_NAME="Rithmic Test"
export RITHMIC_URI="wss://rituz00100.rithmic.com:443"

# Twilio SMS (for notifications)
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_FROM_PHONE="+1234567890"
export TWILIO_TO_PHONE="+1987654321"

# Database (PostgreSQL)
export DATABASE_URL="postgresql://user:pass@host:port/db"
```

### 2. Local Development
```bash
git clone https://github.com/yourusername/xfgv2.git
cd xfgv2
pip install -r requirements.txt
python web_app_levels_v2.py
```

### 3. Test SMS Alerts
```bash
cd examples
python sms_alert_example.py
```

## 📱 SMS Alert Examples

```
ES @ 4452.50 - SUPPORT 4450.00 (below, 2.5pts away) [1h]
🚨 CRITICAL: ES broke above 4485.00: 4487.25  
⚠️ HIGH: NQ volume spike at resistance 15820.00
```

## 📁 Project Structure

```
xfgv2/
├── src/
│   ├── structural_levels_v2.py      # Core levels manager
│   └── csv_file_monitor.py          # CSV file monitoring
├── templates/
│   ├── levels_v2.html               # Main web interface
│   └── login_simple.html            # Login page
├── scripts/
│   ├── xfgv2_db_setup.py           # Database setup
│   ├── deploy_xfgv2_render.py      # Render deployment
│   └── show_scanned_levels.py      # Level reference tool
├── examples/
│   └── xfgv2_usage_example.py      # Usage examples
├── docs/
│   └── LEVEL_SCANNING_REFERENCE_UPDATED.md  # Complete documentation
├── web_app_levels_v2.py             # Full Flask app (with DB)
├── web_app_demo.py                  # Demo Flask app (no DB)
├── requirements_xfgv2.txt           # Dependencies
└── README.md                        # This file
```

## 🌟 Key Features

### **Live Market Data Integration**
- **Rithmic Connection**: Real-time ES/NQ price feeds
- **Level Monitoring**: Live price vs structural levels
- **Touch Detection**: Automatic level interaction tracking
- **Async Architecture**: High-performance data processing

### **Automated CSV Processing**
- **File Monitoring**: Automatically detects MotiveWave CSV exports
- **Symbol Detection**: Auto-detects ES/NQ from filename
- **Time Validation**: Only processes data ≥9:30 AM EST (when ONH/ONL final)
- **File Archiving**: Organizes processed files automatically

### **Priority-Based Level System**
- **⭐ ALL-STAR**: 32 highest priority levels (10 CSV + 6 manual per symbol)
- **📊 STANDARD**: Regular trading levels for context
- **📋 REFERENCE**: Extended targets and analysis levels

### **Web Interface**
- **Real-time Dashboard**: Live status for ES and NQ symbols
- **Manual Entry**: Daily pivot level input with validation
- **Responsive Design**: Works on desktop and mobile
- **Authentication**: Secure login system

### **Database Integration**
- **PostgreSQL**: Production-ready database storage
- **SQLite**: Local development option
- **Performance**: Optimized queries with indexing
- **Audit Trail**: Tracks level entry and modifications

## 📊 Level Types Scanned

### **CSV Levels (34 per symbol)**
**⭐ ALL-STAR (10):**
- Week Open, Previous Month VAH/VAL, Previous Week VAH/VAL, Overnight High/Low, Balance Area High/Mid/Low

**📊 STANDARD (7):**
- Month Open, Previous Month levels, Previous Week levels, Daily levels

**📋 REFERENCE (11):**
- Initial Balance extensions (+/-200%, +/-150%, +/-100%, +/-50%, etc.)

### **Manual Levels (6 per symbol)**
**⭐ ALL-STAR (6):**
- Pivot, Pivot High/Low, Pivot Balance Area High/Low, Weekly Pivot

## 🔄 Daily Workflow

1. **After 9:30 AM EST**: Export ES/NQ CSV files from MotiveWave
2. **Automatic Import**: System processes files within 5 minutes
3. **Manual Entry**: Input daily pivot levels via web interface
4. **Trading Ready**: Both symbols show "Complete" status

## 🛠️ Development

### **Local Testing**
```bash
# Run demo interface (no database)
python web_app_demo.py

# Run with SQLite (local development)
DATABASE_URL=sqlite:///xfgv2_local.db python web_app_levels_v2.py
```

### **Database Management**
```bash
# Create tables
python scripts/xfgv2_db_setup.py create

# Check status
python scripts/xfgv2_db_setup.py check

# View level reference
python scripts/show_scanned_levels.py
```

## 🌐 Deployment

### **Render.com**
```bash
# Create deployment config
python scripts/deploy_xfgv2_render.py --create-config

# Health check
python scripts/deploy_xfgv2_render.py --health-check
```

## 📈 API Endpoints

- `GET /api/v2/levels/{symbol}/{date}` - Get levels for symbol/date
- `POST /api/v2/manual-levels` - Add manual pivot levels
- `GET /api/v2/completeness/{symbol}` - Check completion status
- `POST /api/v2/csv-import` - Trigger manual CSV import
- `GET /api/v2/nearby-levels` - Find levels near price

## 🔍 Monitoring

- **Web Dashboard**: Real-time status monitoring
- **File Processing**: Automatic archiving and error handling
- **Level Validation**: Hierarchy checks and price validation
- **Audit Logging**: Complete activity tracking

## 📚 Documentation

- [SMS Setup Guide](docs/SMS_NOTIFICATION_SETUP.md)
- [Rithmic Integration](docs/RITHMIC_EXACT_COPY.md)
- [iOS App Roadmap](docs/iOS_App_Implementation_Plan.md)
- [Level Reference](docs/LEVEL_SCANNING_REFERENCE_UPDATED.md)

## 🔒 Security

- Environment variables for all credentials
- No hardcoded API keys
- Rate limiting on endpoints
- Secure WebSocket connections (WSS)

## 💰 Cost Breakdown

### SMS Costs (Twilio)
- $0.0075 per message
- ~50 alerts/day = $11.25/month
- Built-in cost controls

### Infrastructure
- Render: Free tier available
- PostgreSQL: Free tier sufficient
- Rithmic: Market data subscription required

## 🚨 Disclaimer

This software is for educational and informational purposes only. Trading futures involves substantial risk of loss. Use at your own risk.

---

**Ready to stay ahead of the market? Set up your alerts and never miss a key level again! 📱📈**