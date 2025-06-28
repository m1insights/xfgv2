# xFGv2 Level Scanning Reference - UPDATED

This document lists all the levels that are scanned from your MotiveWave CSV export with priority classifications and file archiving workflow.

## 📊 CSV Levels Scanned (Automatic Import)

The system scans your MotiveWave CSV file for these specific column names and imports them with priority levels:

### **⭐ ALL-STAR Levels (Highest Priority - Most Reliable)**
| CSV Column Name | Level Type | Description |
|---|---|---|
| `MGI Wk-Op` | `mgi_wk_op` | Week Open |
| `MGI PM-VAH` | `mgi_pm_vah` | **Previous Month VAH** |
| `MGI PM-VAL` | `mgi_pm_val` | **Previous Month VAL** |
| `MGI PW-VAH` | `mgi_pw_vah` | Previous Week VAH |
| `MGI PW-VAL` | `mgi_pw_val` | Previous Week VAL |
| `MGI: ONH` | `mgi_onh` | **Overnight High** (Available after 9:30 AM) |
| `MGI: ONL` | `mgi_onl` | **Overnight Low** (Available after 9:30 AM) |

### **📊 Standard Priority Levels**
| CSV Column Name | Level Type | Description |
|---|---|---|
| `MGI MTH-Op` | `mgi_mth_op` | Month Open |
| `MGI PM-Hi` | `mgi_pm_hi` | **Previous Month High** |
| `MGI PM-Md` | `mgi_pm_md` | **Previous Month Mid** |
| `MGI PM-Lo` | `mgi_pm_lo` | **Previous Month Low** |
| `MGI PM-Cl` | `mgi_pm_cl` | **Previous Month Close** |
| `MGI PW-Hi` | `mgi_pw_hi` | Previous Week High |
| `MGI PW-Md` | `mgi_pw_md` | Previous Week Mid |
| `MGI PW-Lo` | `mgi_pw_lo` | Previous Week Low |
| `MGI PW-Cl` | `mgi_pw_cl` | Previous Week Close |
| `MGI: RTHO` | `mgi_rtho` | RTH Open |
| `MGI: PDH` | `mgi_pdh` | Previous Day High |
| `MGI: PDM` | `mgi_pdm` | Previous Day Mid |
| `MGI: PDL` | `mgi_pdl` | Previous Day Low |
| `MGI: PRTH Close` | `mgi_prth_close` | Previous RTH Close |
| `Balance Area High` | `balance_area_high` | Balance Area High |
| `Balance Area Mid` | `balance_area_mid` | Balance Area Mid |
| `Balance Area Low` | `balance_area_low` | Balance Area Low |

### **📋 Reference Priority Levels (Lower Priority)**
| CSV Column Name | Level Type | Description |
|---|---|---|
| `MGI: IB+200%` | `mgi_ib_plus_200` | Initial Balance +200% |
| `MGI: IB+150%` | `mgi_ib_plus_150` | Initial Balance +150% |
| `MGI: IB+100%` | `mgi_ib_plus_100` | Initial Balance +100% |
| `MGI: IB+50%` | `mgi_ib_plus_50` | Initial Balance +50% |
| `MGI: IBH` | `mgi_ibh` | Initial Balance High |
| `MGI: IBM` | `mgi_ibm` | Initial Balance Mid |
| `MGI: IBL` | `mgi_ibl` | Initial Balance Low |
| `MGI: IB-50%` | `mgi_ib_minus_50` | Initial Balance -50% |
| `MGI: IB-100%` | `mgi_ib_minus_100` | Initial Balance -100% |
| `MGI: IB-150%` | `mgi_ib_minus_150` | Initial Balance -150% |
| `MGI: IB-200%` | `mgi_ib_minus_200` | Initial Balance -200% |

## 🚫 CSV Columns NOT Imported

These columns are **REMOVED** from the import system:
- ~~`MGI mVWAP`~~ (Monthly VWAP - not needed)
- ~~`MGI WVWAP`~~ (Weekly VWAP - not needed)
- ~~`MGI: VWAP RTH`~~ (RTH VWAP - not needed)
- ~~`MGI: HGAP`~~ (Gap level - not needed)
- All POC columns (MGI PM-POC, MGI PW-POC)
- Standard OHLC columns
- All DeltaMap, Dominator, EAD, DOM.R columns

## ⭐ Manual Pivot Levels (ALL ALL-STAR Priority)

These levels must be entered manually via the web interface at 9:30 AM daily:

### **Daily Pivot Levels (⭐ ALL-STAR)**
| Level Type | Description | Example |
|---|---|---|
| `pivot` | Daily Pivot Point | 5825.75 |
| `pivot_high` | Daily Pivot High (R1) | 5850.25 |
| `pivot_low` | Daily Pivot Low (S1) | 5800.50 |
| `pivot_ba_high` | Pivot Balance Area High | 5875.00 |
| `pivot_ba_low` | Pivot Balance Area Low | 5775.25 |

### **Weekly Pivot Level (⭐ ALL-STAR, Mondays only)**
| Level Type | Description | Example |
|---|---|---|
| `weekly_pivot` | Weekly Pivot Point | 5800.00 |

## 📁 File Processing Workflow

### **Step 1: CSV Export from MotiveWave**
- Export **ES data** to any filename containing "ES" (e.g., `ES_levels_20240615.csv`)
- Export **NQ data** to any filename containing "NQ" (e.g., `NQ_levels_20240615.csv`)
- Save both files to your designated CSV watch folder on Render

### **Step 2: Automatic Detection & Processing**
- System detects new CSV files every 5 minutes
- Auto-detects symbol from filename (ES or NQ)
- Validates CSV structure and MGI columns
- Processes only data with timestamps ≥ 9:30 AM EST

### **Step 3: Level Import & Prioritization**
- Imports all mapped MGI levels with priority classification
- ⭐ ALL-STAR levels given highest priority in trading system
- Standard and Reference levels imported for completeness

### **Step 4: File Archiving**
- ✅ **Successful imports**: Files moved to `archived/` folder with timestamp
- ❌ **Failed imports**: Files moved to `errors/` folder with error details
- Original files are automatically organized and stored

### **Step 5: Manual Entry**
- Access web interface to enter daily pivot levels
- All manual levels automatically marked as ⭐ ALL-STAR priority
- System validates level hierarchy before saving

## 📊 Priority System in Trading

### **⭐ ALL-STAR Levels (7 CSV + 6 Manual = 13 total)**
**CSV ALL-STAR (7):**
- Week Open (`mgi_wk_op`)
- Previous Month VAH/VAL (`mgi_pm_vah`, `mgi_pm_val`) 
- Previous Week VAH/VAL (`mgi_pw_vah`, `mgi_pw_val`)
- Overnight High/Low (`mgi_onh`, `mgi_onl`)

**Manual ALL-STAR (6):**
- All pivot levels (`pivot`, `pivot_high`, `pivot_low`, `pivot_ba_high`, `pivot_ba_low`, `weekly_pivot`)

### **Trading System Usage**
- ⭐ ALL-STAR levels get **highest priority** in signal assessment
- Trading algorithms focus primarily on ALL-STAR level interactions
- Standard levels used for market context and confluence
- Reference levels used for extended targets and analysis

## ✅ Required Levels for Trading

### **MGI Levels (CSV Import)**
Minimum required for "CSV Complete" status:
- `mgi_onh`, `mgi_onl` (⭐ ALL-STAR Overnight levels)
- `mgi_pm_vah`, `mgi_pm_val` (⭐ ALL-STAR Previous Month levels)
- `mgi_pw_vah`, `mgi_pw_val` (⭐ ALL-STAR Previous Week levels)
- `mgi_wk_op` (⭐ ALL-STAR Week Open)
- `balance_area_high`, `balance_area_low` (Standard levels)

### **Manual Levels (Web Interface)**
Required for "Manual Complete" status:
- All 5 daily pivot levels (⭐ ALL-STAR)

## 🔄 Daily Workflow

### **After Market Open (9:30 AM EST)**

1. **Export from MotiveWave**:
   ```
   📄 ES_levels_20240615.csv → CSV watch folder
   📄 NQ_levels_20240615.csv → CSV watch folder
   ```

2. **Automatic Processing** (within 5 minutes):
   ```
   🔍 System detects new files
   📊 Imports ~24 levels per symbol with priorities
   📁 Archives files: ES_levels_20240615.csv → archived/20240615_093045_ES_levels_20240615.csv
   ```

3. **Manual Entry** (Web Interface):
   ```
   🖥️ Access web interface
   ⭐ Enter 5 pivot levels for ES (ALL-STAR priority)
   ⭐ Enter 5 pivot levels for NQ (ALL-STAR priority)
   ✅ Validate and submit
   ```

4. **Trading Ready**:
   ```
   ✅ ES: 13 ALL-STAR levels ready
   ✅ NQ: 13 ALL-STAR levels ready
   🚀 System ready for trading signals
   ```

## 🎯 Level Count Summary

**Per Symbol (ES or NQ):**
- 7 ⭐ ALL-STAR levels from CSV
- 6 ⭐ ALL-STAR levels from manual entry
- 10 Standard levels from CSV
- 11 Reference levels from CSV
- **Total: 34 levels per symbol**

**Both Symbols Combined:**
- **26 ⭐ ALL-STAR levels** (highest priority)
- 20 Standard levels
- 22 Reference levels
- **Total: 68 levels for complete trading setup**

## 🔍 API Access for Trading Systems

### **Get ALL-STAR Levels Only**
```python
# Get only the highest priority levels for trading
all_star_levels = manager.get_all_star_levels('ES')
print(f"Found {len(all_star_levels)} ALL-STAR ES levels")
```

### **Get Levels by Priority**
```python
# Get levels by specific priority
all_star = manager.get_levels_by_priority('ES', 'all_star')
standard = manager.get_levels_by_priority('ES', 'standard') 
reference = manager.get_levels_by_priority('ES', 'reference')
```

## 📋 File Organization

Your CSV watch folder structure:
```
/csv_watch_folder/
├── ES_levels_20240615.csv          # ← New files go here
├── NQ_levels_20240615.csv          # ← New files go here
├── archived/                       # ← Successfully processed files
│   ├── 20240615_093045_ES_levels_20240615.csv
│   └── 20240615_093045_NQ_levels_20240615.csv
└── errors/                         # ← Failed files with error info
    └── 20240615_094500_bad_file.csv
```

This updated system ensures your most reliable ALL-STAR levels get priority in trading decisions while maintaining a complete picture of market structure through standard and reference levels!