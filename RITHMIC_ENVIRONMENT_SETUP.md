# Rithmic Environment Variables for xFGv2

## 🔧 **Required Environment Variables**

These are the **exact environment variable names** that were working in your old system and are now supported in xFGv2:

### **Core Credentials**
```bash
export RITHMIC_USERNAME="your_rithmic_username"
export RITHMIC_PASSWORD="your_rithmic_password"
```

### **Connection Settings**
```bash
export RITHMIC_SYSTEM_NAME="Rithmic Test"
export RITHMIC_URI="wss://rituz00100.rithmic.com:443"
export RITHMIC_ENVIRONMENT="test"
```

### **Optional Settings**
```bash
export RITHMIC_SYMBOLS="ES,NQ"  # Default: ES,NQ
export DATABASE_URL="postgresql://user:pass@host/xfgv2"  # For level integration
```

---

## 🚀 **Complete Setup Example**

### **For Test Environment:**
```bash
# Copy these values from your working old system
export RITHMIC_USERNAME="your_actual_username"
export RITHMIC_PASSWORD="your_actual_password"
export RITHMIC_SYSTEM_NAME="Rithmic Test"
export RITHMIC_URI="wss://rituz00100.rithmic.com:443"
export RITHMIC_ENVIRONMENT="test"
export RITHMIC_SYMBOLS="ES,NQ"

# For xFGv2 levels integration
export DATABASE_URL="postgresql://user:pass@localhost/xfgv2"
```

### **For Production Environment:**
```bash
export RITHMIC_USERNAME="your_actual_username"
export RITHMIC_PASSWORD="your_actual_password"
export RITHMIC_SYSTEM_NAME="Rithmic 01"
export RITHMIC_URI="wss://rithmic01.rithmic.com:443"
export RITHMIC_ENVIRONMENT="prod"
export RITHMIC_SYMBOLS="ES,NQ"
export DATABASE_URL="postgresql://user:pass@localhost/xfgv2"
```

---

## 📋 **Environment Setup Script**

Create a file `setup_rithmic_env.sh`:

```bash
#!/bin/bash
# Rithmic Environment Setup for xFGv2

# IMPORTANT: Replace these with your actual working values
export RITHMIC_USERNAME="YOUR_ACTUAL_USERNAME"
export RITHMIC_PASSWORD="YOUR_ACTUAL_PASSWORD"
export RITHMIC_SYSTEM_NAME="Rithmic Test"
export RITHMIC_URI="wss://rituz00100.rithmic.com:443"
export RITHMIC_ENVIRONMENT="test"
export RITHMIC_SYMBOLS="ES,NQ"

# xFGv2 Database (update with your actual database URL)
export DATABASE_URL="postgresql://user:pass@localhost/xfgv2"

echo "✅ Rithmic environment variables set for xFGv2"
echo "🔗 URI: $RITHMIC_URI"
echo "👤 User: $RITHMIC_USERNAME"
echo "🏛️  System: $RITHMIC_SYSTEM_NAME"
echo "📊 Symbols: $RITHMIC_SYMBOLS"
```

**Usage:**
```bash
source setup_rithmic_env.sh
python examples/rithmic_live_data_example.py
```

---

## 🔍 **Verification**

### **Check Environment Variables:**
```bash
echo "Username: $RITHMIC_USERNAME"
echo "URI: $RITHMIC_URI"
echo "System: $RITHMIC_SYSTEM_NAME"
echo "Environment: $RITHMIC_ENVIRONMENT"
```

### **Test Connection:**
```bash
cd xfgv2
python examples/rithmic_live_data_example.py
```

---

## 📝 **Configuration Priority**

The xFGv2 system uses this priority order:

1. **Environment Variables** (highest priority)
2. **Configuration File** (`config_template_v2.ini`)
3. **Default Values** (lowest priority)

---

## ⚠️ **Important Notes**

1. **Use Your Working Values**: Copy the exact values that were working in your old system
2. **Test Environment First**: Always test with `RITHMIC_ENVIRONMENT="test"` before production
3. **Secure Storage**: Never commit credentials to version control
4. **URI Format**: Must include `wss://` protocol and `:443` port
5. **System Name**: Must match your approved Rithmic system name

---

## 🎯 **Quick Test**

Run this to verify your environment is set up correctly:

```python
import os
from src.rithmic_client_v2 import create_rithmic_client_from_env

try:
    client = create_rithmic_client_from_env()
    print("✅ Environment variables configured correctly")
    print(f"📡 Will connect to: {client.config.uri}")
    print(f"👤 Username: {client.config.username}")
    print(f"🏛️  System: {client.config.system_name}")
except ValueError as e:
    print(f"❌ Environment setup error: {e}")
```

Use the **exact same environment variables** that were working in your old system for guaranteed compatibility! 🎉