"""
xFGv2 Structural Levels Usage Examples
Demonstrates how to use the new structural levels system.
"""

import os
import sys
from pathlib import Path
from datetime import date, datetime
import asyncio

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from structural_levels_v2 import StructuralLevelsManagerV2, import_motivewave_csv, add_daily_manual_levels
from csv_file_monitor import CSVFileMonitor, MonitorConfig


async def example_basic_usage():
    """Basic usage example."""
    print("=== xFGv2 Basic Usage Example ===")
    
    # Setup (you'd get this from environment variables in production)
    DATABASE_URL = "postgresql://user:pass@localhost/xfgv2"  # Replace with your DB URL
    
    # Create levels manager
    manager = StructuralLevelsManagerV2(DATABASE_URL)
    
    # Example 1: Add manual pivot levels (what you'd do at 9:30am daily)
    print("\n1. Adding manual pivot levels...")
    manual_levels = {
        'pivot': 5825.75,
        'pivot_high': 5850.25,
        'pivot_low': 5800.50,
        'pivot_ba_high': 5875.00,
        'pivot_ba_low': 5775.25,
        'weekly_pivot': 5800.00
    }
    
    result = manager.add_manual_levels('ES', date.today(), manual_levels, user="trader1")
    print(f"Manual levels result: {result}")
    
    # Example 2: Check completeness status
    print("\n2. Checking completeness status...")
    status = manager.get_daily_completeness_status('ES')
    print(f"ES Status: {status}")
    
    # Example 3: Get all levels for today
    print("\n3. Getting all levels for today...")
    levels = manager.get_levels_for_date('ES', date.today())
    print("Current ES levels:")
    for level_type, price in levels.items():
        print(f"  {level_type}: {price}")
    
    # Example 4: Find nearby levels
    print("\n4. Finding levels near current price...")
    current_price = 5830.00
    nearby = manager.get_nearby_levels('ES', current_price, range_points=10.0)
    print(f"Levels within 10 points of {current_price}:")
    for level in nearby:
        print(f"  {level['level_type']}: {level['price']} (distance: {level['distance']:.2f})")
    
    # Example 5: Validate level hierarchy
    print("\n5. Validating level hierarchy...")
    validation = manager.validate_level_hierarchy('ES', date.today())
    print(f"Validation result: Valid={validation.is_valid}")
    if validation.errors:
        print(f"Errors: {validation.errors}")
    if validation.warnings:
        print(f"Warnings: {validation.warnings}")


def example_csv_import():
    """Example of importing MotiveWave CSV."""
    print("\n=== CSV Import Example ===")
    
    DATABASE_URL = "postgresql://user:pass@localhost/xfgv2"
    
    # Create sample CSV file
    sample_csv_content = """Level_Type,Price,Symbol,Date
overnight_high,5850.25,ES,2024-01-15
overnight_low,5825.50,ES,2024-01-15
vwap,5837.75,ES,2024-01-15
vah,5845.00,ES,2024-01-15
val,5830.50,ES,2024-01-15
poc,5836.25,ES,2024-01-15
"""
    
    # Write sample CSV
    csv_file = "/tmp/sample_levels.csv"
    with open(csv_file, 'w') as f:
        f.write(sample_csv_content)
    
    print(f"Created sample CSV: {csv_file}")
    
    # Import the CSV
    result = import_motivewave_csv(DATABASE_URL, csv_file, overwrite=True)
    print(f"CSV import result: {result}")
    
    # Clean up
    os.remove(csv_file)


def example_file_monitoring():
    """Example of setting up file monitoring."""
    print("\n=== File Monitoring Example ===")
    
    # Create monitor configuration
    config = MonitorConfig(
        database_url="postgresql://user:pass@localhost/xfgv2",
        watch_folder="/tmp/csv_watch",
        check_interval_minutes=1,  # Check every minute for demo
        allowed_symbols=['ES', 'NQ']
    )
    
    # Create monitor
    monitor = CSVFileMonitor(config)
    
    # Create sample CSV in watch folder
    os.makedirs(config.watch_folder, exist_ok=True)
    sample_csv = f"{config.watch_folder}/demo_levels.csv"
    
    csv_content = """Level_Type,Price,Symbol,Date
overnight_high,20150.25,NQ,2024-01-15
overnight_low,20100.50,NQ,2024-01-15
vwap,20125.75,NQ,2024-01-15
"""
    
    with open(sample_csv, 'w') as f:
        f.write(csv_content)
    
    print(f"Created sample CSV in watch folder: {sample_csv}")
    
    # Process manually (instead of starting the monitoring loop)
    result = monitor.manual_process_folder()
    print(f"Manual processing result: {result}")


def example_web_api_simulation():
    """Simulate web API usage."""
    print("\n=== Web API Simulation ===")
    
    DATABASE_URL = "postgresql://user:pass@localhost/xfgv2"
    manager = StructuralLevelsManagerV2(DATABASE_URL)
    
    # Simulate API call to add manual levels
    api_request = {
        'symbol': 'ES',
        'trading_date': date.today().isoformat(),
        'levels': {
            'pivot': 5825.75,
            'pivot_high': 5850.25,
            'pivot_low': 5800.50
        }
    }
    
    print(f"Simulating API request: {api_request}")
    
    # Process the request
    result = manager.add_manual_levels(
        symbol=api_request['symbol'],
        trading_date=date.fromisoformat(api_request['trading_date']),
        levels=api_request['levels'],
        user='api_user'
    )
    
    print(f"API response: {result}")
    
    # Simulate API call to get completeness status
    status = manager.get_daily_completeness_status(
        api_request['symbol'],
        date.fromisoformat(api_request['trading_date'])
    )
    
    print(f"Completeness status: {status}")


def example_daily_workflow():
    """Example of typical daily workflow."""
    print("\n=== Daily Workflow Example ===")
    
    DATABASE_URL = "postgresql://user:pass@localhost/xfgv2"
    manager = StructuralLevelsManagerV2(DATABASE_URL)
    
    # Step 1: Morning - Import overnight levels from MotiveWave CSV
    print("Step 1: Import overnight/session levels from MotiveWave...")
    
    # This would be automated via file monitoring
    # For demo, we'll simulate it
    csv_content = """Level_Type,Price,Symbol,Date
overnight_high,5850.25,ES,2024-01-15
overnight_low,5825.50,ES,2024-01-15
previous_day_high,5848.75,ES,2024-01-15
previous_day_low,5820.25,ES,2024-01-15
previous_day_close,5835.50,ES,2024-01-15
vwap,5837.75,ES,2024-01-15
vah,5845.00,ES,2024-01-15
val,5830.50,ES,2024-01-15
poc,5836.25,ES,2024-01-15
"""
    
    csv_file = "/tmp/morning_levels.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    csv_result = import_motivewave_csv(DATABASE_URL, csv_file, overwrite=True)
    print(f"CSV import: {csv_result['imported_count']} levels imported")
    
    # Step 2: 9:30am - Add manual pivot levels
    print("\nStep 2: Add manual pivot levels at market open...")
    
    pivot_levels = {
        'pivot': 5838.00,
        'pivot_high': 5855.25,
        'pivot_low': 5820.75,
        'pivot_ba_high': 5870.00,
        'pivot_ba_low': 5805.50,
        'weekly_pivot': 5830.00
    }
    
    manual_result = manager.add_manual_levels('ES', date.today(), pivot_levels, user="trader_morning")
    print(f"Manual levels: {manual_result['imported_count']} levels added")
    
    # Step 3: Validate everything is ready
    print("\nStep 3: Validate setup is complete...")
    
    validation = manager.validate_level_hierarchy('ES', date.today())
    status = manager.get_daily_completeness_status('ES', date.today())
    
    print(f"Validation: {'✓ PASS' if validation.is_valid else '✗ FAIL'}")
    print(f"Trading Ready: {'✓ YES' if status['overall_complete'] else '✗ NO'}")
    
    if status['overall_complete']:
        print("🚀 System is ready for trading!")
    else:
        print(f"Missing: CSV={status['missing_csv']}, Manual={status['missing_manual']}")
    
    # Step 4: During trading - check nearby levels
    print("\nStep 4: During trading - monitor price levels...")
    
    current_price = 5842.50
    nearby_levels = manager.get_nearby_levels('ES', current_price, range_points=5.0)
    
    print(f"Price {current_price} - Nearby levels:")
    for level in nearby_levels[:3]:  # Show top 3 closest
        print(f"  {level['level_type']}: {level['price']} ({level['distance']:.2f} pts away)")
    
    # Cleanup
    os.remove(csv_file)


async def main():
    """Run all examples."""
    print("xFGv2 Structural Levels - Usage Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await example_basic_usage()
        example_csv_import()
        example_file_monitoring()
        example_web_api_simulation()
        example_daily_workflow()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nNext steps:")
        print("1. Set up your PostgreSQL database")
        print("2. Configure environment variables (DATABASE_URL, CSV_WATCH_FOLDER)")
        print("3. Deploy to Render using the deployment script")
        print("4. Access the web interface to manage levels")
        
    except Exception as e:
        print(f"\nExample failed: {e}")
        print("Make sure you have:")
        print("- PostgreSQL database running")
        print("- Correct DATABASE_URL")
        print("- Required Python packages installed")


if __name__ == '__main__':
    asyncio.run(main())