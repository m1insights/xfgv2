# xFGv2 File Organization

All xFGv2 files have been moved to the dedicated `xfgv2/` folder for better organization.

## 📁 New Structure

```
xFG/
└── xfgv2/                           # ← All v2 files here
    ├── README.md                     # Main project documentation
    ├── README_xFGv2.md              # Detailed system guide
    ├── requirements_xfgv2.txt        # Python dependencies
    ├── .env                          # Environment configuration
    │
    ├── src/                          # Core system components
    │   ├── __init__.py
    │   ├── structural_levels_v2.py   # Main levels manager
    │   └── csv_file_monitor.py       # File monitoring service
    │
    ├── templates/                    # Web interface templates
    │   ├── levels_v2.html            # Main dashboard
    │   └── login_simple.html         # Login page
    │
    ├── scripts/                      # Management scripts
    │   ├── xfgv2_db_setup.py        # Database management
    │   ├── deploy_xfgv2_render.py   # Render deployment
    │   └── show_scanned_levels.py   # Level reference tool
    │
    ├── examples/                     # Usage examples
    │   └── xfgv2_usage_example.py   # API usage examples
    │
    ├── docs/                         # Documentation
    │   └── LEVEL_SCANNING_REFERENCE_UPDATED.md
    │
    ├── web_app_levels_v2.py          # Full web app (with database)
    └── web_app_demo.py               # Demo web app (no database)
```

## 🔄 How to Use

### **From xfgv2 folder:**
```bash
cd xfgv2

# Demo interface (no database)
python web_app_demo.py

# Full system (with database)
python web_app_levels_v2.py

# Database setup
python scripts/xfgv2_db_setup.py

# Show level reference
python scripts/show_scanned_levels.py
```

## ✅ Benefits of New Organization

1. **Clear Separation**: All v2 files isolated from v1 system
2. **Self-Contained**: Complete system in one folder
3. **Easy Deployment**: Can deploy entire xfgv2 folder
4. **Version Control**: Clear distinction between versions
5. **Development**: Easier to work on v2 without affecting v1

## 🚀 Current Status

- ✅ All v2 files moved to `xfgv2/` folder
- ✅ Import paths updated and working
- ✅ Demo server running from new location
- ✅ Complete project structure organized
- ✅ Documentation updated

## 🌐 Live Demo

**Currently running:** http://127.0.0.1:5002  
**Credentials:** admin / password  
**Location:** `/xfgv2/web_app_demo.py`