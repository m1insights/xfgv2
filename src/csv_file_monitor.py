"""
CSV File Monitor for MotiveWave Exports
Automatically monitors a folder for new CSV files and imports them.
Designed to run on Render with scheduled checks.
"""

import logging
import os
import time
import schedule
from datetime import datetime, date, time as dt_time
from pathlib import Path
from typing import List, Dict, Any
import pytz
from dataclasses import dataclass

from .structural_levels_v2 import StructuralLevelsManagerV2

logger = logging.getLogger(__name__)

EST = pytz.timezone('America/New_York')


@dataclass
class MonitorConfig:
    """Configuration for the CSV file monitor."""
    database_url: str
    watch_folder: str
    processed_folder: str = "processed"
    archived_folder: str = "archived"
    error_folder: str = "errors"
    check_interval_minutes: int = 5
    max_file_age_hours: int = 24
    allowed_symbols: List[str] = None
    
    def __post_init__(self):
        if self.allowed_symbols is None:
            self.allowed_symbols = ['ES', 'NQ']


class CSVFileMonitor:
    """Monitors folder for MotiveWave CSV exports and processes them automatically."""
    
    def __init__(self, config: MonitorConfig):
        self.config = config
        self.levels_manager = StructuralLevelsManagerV2(config.database_url)
        self.is_running = False
        
        # Create necessary folders
        self._create_folders()
        
        logger.info(f"CSV File Monitor initialized - watching: {config.watch_folder}")
    
    def _create_folders(self):
        """Create necessary folders if they don't exist."""
        folders = [
            self.config.watch_folder,
            os.path.join(self.config.watch_folder, self.config.processed_folder),
            os.path.join(self.config.watch_folder, self.config.archived_folder),
            os.path.join(self.config.watch_folder, self.config.error_folder)
        ]
        
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
    
    def _is_trading_day(self) -> bool:
        """Check if today is a trading day (weekday)."""
        now_est = datetime.now(EST)
        return now_est.weekday() < 5  # Monday = 0, Friday = 4
    
    def _is_market_hours(self) -> bool:
        """Check if we're within market hours (9:00 AM - 4:00 PM EST)."""
        now_est = datetime.now(EST)
        current_time = now_est.time()
        market_start = dt_time(9, 0)
        market_end = dt_time(16, 0)
        
        return market_start <= current_time <= market_end
    
    def _get_new_csv_files(self) -> List[Path]:
        """Get list of new CSV files to process."""
        watch_path = Path(self.config.watch_folder)
        csv_files = []
        
        if not watch_path.exists():
            logger.warning(f"Watch folder does not exist: {self.config.watch_folder}")
            return []
        
        for csv_file in watch_path.glob("*.csv"):
            try:
                # Skip files in subfolders
                if csv_file.parent != watch_path:
                    continue
                
                # Check file age
                file_mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
                age_hours = (datetime.now() - file_mtime).total_seconds() / 3600
                
                if age_hours <= self.config.max_file_age_hours:
                    csv_files.append(csv_file)
                else:
                    logger.debug(f"Skipping old file: {csv_file.name} (age: {age_hours:.1f} hours)")
                    
            except Exception as e:
                logger.error(f"Error checking file {csv_file}: {e}")
        
        return sorted(csv_files, key=lambda x: x.stat().st_mtime)
    
    def _validate_csv_content(self, csv_file: Path) -> Dict[str, Any]:
        """Validate MotiveWave CSV file content before processing."""
        try:
            import pandas as pd
            
            # Read first few rows to validate structure
            df = pd.read_csv(csv_file, nrows=5)
            
            # Check for Date/Time column
            datetime_col = None
            for col in ['Date/Time', 'DateTime', 'Time', 'Date']:
                if col in df.columns:
                    datetime_col = col
                    break
            
            if not datetime_col:
                return {
                    'valid': False,
                    'error': "No Date/Time column found"
                }
            
            # Check for at least some MGI columns
            mgi_columns = [col for col in df.columns if col.startswith('MGI')]
            if len(mgi_columns) < 5:
                return {
                    'valid': False,
                    'error': f"Insufficient MGI columns found: {len(mgi_columns)}"
                }
            
            # Check for Balance Area columns
            balance_area_columns = [col for col in df.columns if 'Balance Area' in col]
            if len(balance_area_columns) < 2:
                return {
                    'valid': False,
                    'error': "Missing Balance Area columns"
                }
            
            # Try to parse datetime
            try:
                pd.to_datetime(df[datetime_col].iloc[0], format='%d/%m/%Y %H:%M:%S')
            except Exception as e:
                return {
                    'valid': False,
                    'error': f"Invalid datetime format: {e}"
                }
            
            return {
                'valid': True,
                'mgi_columns_found': len(mgi_columns),
                'balance_area_columns_found': len(balance_area_columns)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Error reading CSV: {e}"
            }
    
    def _move_file(self, source_file: Path, destination_folder: str, 
                   add_timestamp: bool = True) -> Path:
        """Move file to destination folder with optional timestamp."""
        dest_folder = Path(self.config.watch_folder) / destination_folder
        dest_folder.mkdir(exist_ok=True)
        
        if add_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_filename = f"{timestamp}_{source_file.name}"
        else:
            dest_filename = source_file.name
        
        dest_path = dest_folder / dest_filename
        
        # Handle filename conflicts
        counter = 1
        while dest_path.exists():
            name_parts = dest_filename.rsplit('.', 1)
            if len(name_parts) == 2:
                dest_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                dest_filename = f"{dest_filename}_{counter}"
            dest_path = dest_folder / dest_filename
            counter += 1
        
        source_file.rename(dest_path)
        return dest_path
    
    def _detect_symbol_from_filename(self, csv_file: Path) -> str:
        """Detect symbol from CSV filename."""
        filename = csv_file.name.upper()
        
        # Check for symbol in filename
        for symbol in self.config.allowed_symbols:
            if symbol in filename:
                return symbol
        
        # Default to ES if no symbol detected
        logger.warning(f"Could not detect symbol from filename {csv_file.name}, defaulting to ES")
        return 'ES'
    
    def process_single_file(self, csv_file: Path) -> Dict[str, Any]:
        """Process a single CSV file for one symbol."""
        logger.info(f"Processing CSV file: {csv_file.name}")
        
        try:
            # Validate file content
            validation = self._validate_csv_content(csv_file)
            if not validation['valid']:
                logger.error(f"Invalid CSV file {csv_file.name}: {validation['error']}")
                
                # Move to error folder
                error_path = self._move_file(csv_file, self.config.error_folder)
                
                return {
                    'success': False,
                    'file_name': csv_file.name,
                    'error': validation['error'],
                    'moved_to': str(error_path)
                }
            
            # Detect symbol from filename (ES_levels.csv, NQ_levels.csv, etc.)
            detected_symbol = self._detect_symbol_from_filename(csv_file)
            
            # Import levels for the detected symbol
            with self.levels_manager.get_session() as session:
                from .structural_levels_v2 import MotiveWaveCSVImporter
                importer = MotiveWaveCSVImporter(session)
                
                # Import with overwrite for same-day files
                result = importer.import_csv_levels(str(csv_file), symbol=detected_symbol, overwrite=True)
                
                if result['success']:
                    logger.info(f"Successfully imported {result['imported_count']} {detected_symbol} levels from {csv_file.name}")
                    
                    # Archive the successfully processed file
                    archived_path = self._move_file(csv_file, self.config.archived_folder)
                    
                    result.update({
                        'file_name': csv_file.name,
                        'detected_symbol': detected_symbol,
                        'moved_to': str(archived_path),
                        'status': 'archived',
                        'mgi_columns_found': validation.get('mgi_columns_found', 0)
                    })
                    
                    # Log import summary
                    self._log_import_summary(result)
                    
                else:
                    logger.error(f"Failed to import {detected_symbol} levels from {csv_file.name}: {result.get('error', 'Unknown error')}")
                    
                    # Move to error folder
                    error_path = self._move_file(csv_file, self.config.error_folder)
                    result.update({
                        'file_name': csv_file.name,
                        'detected_symbol': detected_symbol,
                        'moved_to': str(error_path),
                        'status': 'error'
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error processing file {csv_file.name}: {e}")
            
            # Move to error folder
            try:
                error_path = self._move_file(csv_file, self.config.error_folder)
                moved_to = str(error_path)
            except Exception as move_error:
                logger.error(f"Error moving file to error folder: {move_error}")
                moved_to = "failed_to_move"
            
            return {
                'success': False,
                'file_name': csv_file.name,
                'error': str(e),
                'moved_to': moved_to
            }
    
    def _log_import_summary(self, result: Dict[str, Any]):
        """Log a summary of the import operation."""
        if result.get('success'):
            # Single symbol result (updated format)
            symbol = result.get('detected_symbol', result.get('symbol', 'Unknown'))
            logger.info(f"Import Summary - File: {result['file_name']}, "
                       f"Symbol: {symbol}, "
                       f"Imported: {result.get('imported_count', 0)}, "
                       f"Skipped: {result.get('skipped_count', 0)}, "
                       f"MGI Columns: {result.get('mgi_columns_found', 0)}")
            
            if result.get('errors'):
                logger.warning(f"Import had {len(result['errors'])} errors: {result['errors']}")
    
    def scan_and_process(self) -> List[Dict[str, Any]]:
        """Scan for new files and process them."""
        # Only process during trading days and hours (with some buffer)
        if not self._is_trading_day():
            logger.debug("Not a trading day, skipping scan")
            return []
        
        logger.info("Scanning for new CSV files...")
        
        new_files = self._get_new_csv_files()
        if not new_files:
            logger.debug("No new CSV files found")
            return []
        
        results = []
        for csv_file in new_files:
            result = self.process_single_file(csv_file)
            results.append(result)
        
        return results
    
    def start_monitoring(self):
        """Start the monitoring process with scheduled checks."""
        self.is_running = True
        
        # Schedule regular scans
        schedule.every(self.config.check_interval_minutes).minutes.do(self.scan_and_process)
        
        # Schedule specific times for daily scans (after market open)
        schedule.every().day.at("09:35").do(self._morning_scan)  # 5 minutes after market open
        schedule.every().day.at("12:00").do(self._midday_scan)   # Midday check
        
        logger.info(f"CSV File Monitor started - checking every {self.config.check_interval_minutes} minutes")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled tasks
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.stop_monitoring()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _morning_scan(self):
        """Special morning scan after market open."""
        if self._is_trading_day():
            logger.info("Running morning CSV scan...")
            results = self.scan_and_process()
            
            # Check completeness for today
            for symbol in self.config.allowed_symbols:
                status = self.levels_manager.get_daily_completeness_status(symbol)
                logger.info(f"{symbol} levels status: {status}")
    
    def _midday_scan(self):
        """Midday scan for any missed files."""
        if self._is_trading_day() and self._is_market_hours():
            logger.info("Running midday CSV scan...")
            self.scan_and_process()
    
    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.is_running = False
        logger.info("CSV File Monitor stopped")
    
    def manual_process_folder(self) -> Dict[str, Any]:
        """Manually process all files in the watch folder."""
        logger.info("Manual processing of all CSV files in watch folder...")
        
        all_files = list(Path(self.config.watch_folder).glob("*.csv"))
        if not all_files:
            return {
                'processed_count': 0,
                'message': 'No CSV files found in watch folder'
            }
        
        results = []
        for csv_file in all_files:
            result = self.process_single_file(csv_file)
            results.append(result)
        
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        return {
            'processed_count': len(results),
            'successful_count': len(successful),
            'failed_count': len(failed),
            'results': results
        }


def create_monitor_from_env() -> CSVFileMonitor:
    """Create a CSV monitor from environment variables."""
    config = MonitorConfig(
        database_url=os.environ.get('DATABASE_URL', ''),
        watch_folder=os.environ.get('CSV_WATCH_FOLDER', '/tmp/csv_watch'),
        check_interval_minutes=int(os.environ.get('CSV_CHECK_INTERVAL', '5')),
        max_file_age_hours=int(os.environ.get('CSV_MAX_AGE_HOURS', '24')),
        allowed_symbols=os.environ.get('ALLOWED_SYMBOLS', 'ES,NQ').split(',')
    )
    
    return CSVFileMonitor(config)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start monitor
    monitor = create_monitor_from_env()
    
    try:
        # Run manual scan first
        manual_result = monitor.manual_process_folder()
        print(f"Manual scan result: {manual_result}")
        
        # Start monitoring
        monitor.start_monitoring()
        
    except Exception as e:
        logger.error(f"Error starting monitor: {e}")
        print(f"Error: {e}")