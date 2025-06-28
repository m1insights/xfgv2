#!/usr/bin/env python3
"""
Display all levels that are scanned from MotiveWave CSV files.
Use this to verify what the system is looking for in your CSV exports.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

def show_csv_levels():
    """Display all CSV levels that are scanned."""
    from structural_levels_v2 import MotiveWaveCSVImporter
    
    # Create importer to access column mapping
    importer = MotiveWaveCSVImporter(None)
    
    print("=" * 80)
    print("xFGv2 MOTIVEWAVE CSV LEVEL SCANNER")
    print("=" * 80)
    print()
    
    print("The system scans your MotiveWave CSV export for these specific columns:")
    print()
    
    # Group columns by category
    categories = {
        "Week/Month Levels": [
            ('MGI Wk-Op', 'mgi_wk_op', 'Week Open'),
            ('MGI MTH-Op', 'mgi_mth_op', 'Month Open'),
        ],
        "Previous Session Levels": [
            ('MGI PM-Hi', 'mgi_pm_hi', 'Previous Session High'),
            ('MGI PM-Md', 'mgi_pm_md', 'Previous Session Mid'),
            ('MGI PM-Lo', 'mgi_pm_lo', 'Previous Session Low'),
            ('MGI PM-Cl', 'mgi_pm_cl', 'Previous Session Close'),
            ('MGI PM-VAH', 'mgi_pm_vah', 'Previous Session VAH'),
            ('MGI PM-VAL', 'mgi_pm_val', 'Previous Session VAL'),
        ],
        "Previous Week Levels": [
            ('MGI PW-Hi', 'mgi_pw_hi', 'Previous Week High'),
            ('MGI PW-Md', 'mgi_pw_md', 'Previous Week Mid'),
            ('MGI PW-Lo', 'mgi_pw_lo', 'Previous Week Low'),
            ('MGI PW-Cl', 'mgi_pw_cl', 'Previous Week Close'),
            ('MGI PW-VAH', 'mgi_pw_vah', 'Previous Week VAH'),
            ('MGI PW-VAL', 'mgi_pw_val', 'Previous Week VAL'),
        ],
        "VWAP Levels": [
            ('MGI mVWAP', 'mgi_mvwap', 'Monthly VWAP'),
            ('MGI WVWAP', 'mgi_wvwap', 'Weekly VWAP'),
            ('MGI: VWAP RTH', 'mgi_vwap_rth', 'RTH VWAP'),
        ],
        "Daily Reference Levels": [
            ('MGI: RTHO', 'mgi_rtho', 'RTH Open'),
            ('MGI: PDH', 'mgi_pdh', 'Previous Day High'),
            ('MGI: PDM', 'mgi_pdm', 'Previous Day Mid'),
            ('MGI: PDL', 'mgi_pdl', 'Previous Day Low'),
            ('MGI: PRTH Close', 'mgi_prth_close', 'Previous RTH Close'),
        ],
        "Overnight Levels ⭐ (Critical)": [
            ('MGI: ONH', 'mgi_onh', 'Overnight High'),
            ('MGI: ONL', 'mgi_onl', 'Overnight Low'),
            ('MGI: HGAP', 'mgi_hgap', 'Gap Level'),
        ],
        "Initial Balance Levels": [
            ('MGI: IB+200%', 'mgi_ib_plus_200', 'Initial Balance +200%'),
            ('MGI: IB+150%', 'mgi_ib_plus_150', 'Initial Balance +150%'),
            ('MGI: IB+100%', 'mgi_ib_plus_100', 'Initial Balance +100%'),
            ('MGI: IB+50%', 'mgi_ib_plus_50', 'Initial Balance +50%'),
            ('MGI: IBH', 'mgi_ibh', 'Initial Balance High'),
            ('MGI: IBM', 'mgi_ibm', 'Initial Balance Mid'),
            ('MGI: IBL', 'mgi_ibl', 'Initial Balance Low'),
            ('MGI: IB-50%', 'mgi_ib_minus_50', 'Initial Balance -50%'),
            ('MGI: IB-100%', 'mgi_ib_minus_100', 'Initial Balance -100%'),
            ('MGI: IB-150%', 'mgi_ib_minus_150', 'Initial Balance -150%'),
            ('MGI: IB-200%', 'mgi_ib_minus_200', 'Initial Balance -200%'),
        ],
        "Balance Area Levels": [
            ('Balance Area High', 'balance_area_high', 'Balance Area High'),
            ('Balance Area Mid', 'balance_area_mid', 'Balance Area Mid'),
            ('Balance Area Low', 'balance_area_low', 'Balance Area Low'),
        ]
    }
    
    total_levels = 0
    
    for category, levels in categories.items():
        print(f"📊 {category}")
        print("-" * 60)
        
        for csv_col, level_type, description in levels:
            # Check if this column is in our mapping
            if csv_col in importer.column_mapping:
                status = "✅ SCANNED"
                total_levels += 1
            else:
                status = "❌ NOT FOUND"
            
            print(f"  {csv_col:<25} → {level_type:<20} ({description}) {status}")
        
        print()
    
    print("=" * 80)
    print(f"TOTAL LEVELS SCANNED: {total_levels}")
    print("=" * 80)
    print()


def show_manual_levels():
    """Display manual levels that need to be entered."""
    print("✋ MANUAL LEVELS (Web Interface Entry Required)")
    print("=" * 80)
    print()
    
    manual_levels = [
        ("Daily Pivot Levels", [
            ('pivot', 'Daily Pivot Point', 'Example: 5825.75'),
            ('pivot_high', 'Daily Pivot High (R1)', 'Example: 5850.25'),
            ('pivot_low', 'Daily Pivot Low (S1)', 'Example: 5800.50'),
            ('pivot_ba_high', 'Pivot Balance Area High', 'Example: 5875.00'),
            ('pivot_ba_low', 'Pivot Balance Area Low', 'Example: 5775.25'),
        ]),
        ("Weekly Levels (Mondays Only)", [
            ('weekly_pivot', 'Weekly Pivot Point', 'Example: 5800.00'),
        ])
    ]
    
    for category, levels in manual_levels:
        print(f"📝 {category}")
        print("-" * 60)
        
        for level_type, description, example in levels:
            print(f"  {level_type:<20} → {description:<30} ({example})")
        
        print()


def show_processing_rules():
    """Display processing rules and requirements."""
    print("⏰ PROCESSING RULES")
    print("=" * 80)
    print()
    
    rules = [
        ("File Naming", [
            "ES CSV: Any filename containing 'ES' (e.g., ES_levels.csv)",
            "NQ CSV: Any filename containing 'NQ' (e.g., NQ_levels.csv)",
            "Default: If no symbol detected, defaults to ES"
        ]),
        ("Time Requirements", [
            "CSV data must have timestamps 9:30 AM EST or later",
            "This ensures Overnight High/Low are finalized",
            "Pre-market only data will be rejected"
        ]),
        ("Date Validation", [
            "Only processes rows matching today's date",
            "Uses first valid row found (earliest time ≥ 9:30 AM)",
            "Date format: dd/mm/yyyy HH:MM:SS"
        ]),
        ("Price Validation", [
            "ES: Prices must be between 3000-8000",
            "NQ: Prices must be between 10000-30000",
            "Invalid prices are skipped with warnings"
        ]),
        ("Required for Trading", [
            "MGI: mgi_onh, mgi_onl, mgi_pm_vah, mgi_pm_val, mgi_vwap_rth",
            "Balance: balance_area_high, balance_area_low",
            "Manual: pivot, pivot_high, pivot_low, pivot_ba_high, pivot_ba_low"
        ])
    ]
    
    for category, items in rules:
        print(f"📋 {category}")
        print("-" * 60)
        for item in items:
            print(f"  • {item}")
        print()


def show_workflow():
    """Display the daily workflow."""
    print("🔄 DAILY WORKFLOW")
    print("=" * 80)
    print()
    
    steps = [
        ("Step 1: Export from MotiveWave (after 9:30 AM)", [
            "Export ES data to ES_levels.csv",
            "Export NQ data to NQ_levels.csv", 
            "Save both files to your CSV watch folder"
        ]),
        ("Step 2: Automatic Processing", [
            "System scans files every 5 minutes",
            "Imports all MGI and Balance Area levels",
            "Files moved to processed/ folder after success"
        ]),
        ("Step 3: Manual Entry (Web Interface)", [
            "Access web interface at your deployment URL",
            "Enter daily pivot levels for ES and NQ",
            "System validates level hierarchy",
            "Ready to trade when both symbols show 'Complete'"
        ])
    ]
    
    for step_name, details in steps:
        print(f"📝 {step_name}")
        print("-" * 60)
        for detail in details:
            print(f"  • {detail}")
        print()


def main():
    """Main function to display all information."""
    print()
    
    # Show CSV levels being scanned
    show_csv_levels()
    
    # Show manual levels required
    show_manual_levels()
    
    # Show processing rules
    show_processing_rules()
    
    # Show daily workflow
    show_workflow()
    
    print("💡 TIP: Save this output and compare with your MotiveWave CSV export")
    print("to ensure all required columns are present!")
    print()


if __name__ == '__main__':
    main()