"""
Structural Levels Manager V2
Enhanced version with PostgreSQL database integration and MotiveWave CSV import.
"""

import logging
import os
import csv
import json
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import csv
PANDAS_AVAILABLE = True  # Using csv module instead
from dataclasses import dataclass
from pathlib import Path
import pytz

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, JSON, Text, Date, Time, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()
EST = pytz.timezone('America/New_York')


class LevelType(Enum):
    """Types of structural levels."""
    
    # MGI levels from MotiveWave CSV (available after 9:30am)
    MGI_WK_OP = "mgi_wk_op"              # Week Open ⭐ ALL-STAR
    MGI_MTH_OP = "mgi_mth_op"            # Month Open
    MGI_PM_HI = "mgi_pm_hi"              # Previous Month High
    MGI_PM_MD = "mgi_pm_md"              # Previous Month Mid
    MGI_PM_LO = "mgi_pm_lo"              # Previous Month Low
    MGI_PM_CL = "mgi_pm_cl"              # Previous Month Close
    MGI_PM_VAH = "mgi_pm_vah"            # Previous Month VAH ⭐ ALL-STAR
    MGI_PM_VAL = "mgi_pm_val"            # Previous Month VAL ⭐ ALL-STAR
    MGI_PW_HI = "mgi_pw_hi"              # Previous Week High
    MGI_PW_MD = "mgi_pw_md"              # Previous Week Mid
    MGI_PW_LO = "mgi_pw_lo"              # Previous Week Low
    MGI_PW_CL = "mgi_pw_cl"              # Previous Week Close
    MGI_PW_VAH = "mgi_pw_vah"            # Previous Week VAH ⭐ ALL-STAR
    MGI_PW_VAL = "mgi_pw_val"            # Previous Week VAL ⭐ ALL-STAR
    MGI_RTHO = "mgi_rtho"                # RTH Open
    MGI_PDH = "mgi_pdh"                  # Previous Day High
    MGI_PDM = "mgi_pdm"                  # Previous Day Mid
    MGI_PDL = "mgi_pdl"                  # Previous Day Low
    MGI_PRTH_CLOSE = "mgi_prth_close"    # Previous RTH Close
    MGI_ONH = "mgi_onh"                  # Overnight High ⭐ ALL-STAR
    MGI_ONL = "mgi_onl"                  # Overnight Low ⭐ ALL-STAR
    MGI_IB_PLUS_200 = "mgi_ib_plus_200"  # Initial Balance +200%
    MGI_IB_PLUS_150 = "mgi_ib_plus_150"  # Initial Balance +150%
    MGI_IB_PLUS_100 = "mgi_ib_plus_100"  # Initial Balance +100%
    MGI_IB_PLUS_50 = "mgi_ib_plus_50"    # Initial Balance +50%
    MGI_IBH = "mgi_ibh"                  # Initial Balance High
    MGI_IBM = "mgi_ibm"                  # Initial Balance Mid
    MGI_IBL = "mgi_ibl"                  # Initial Balance Low
    MGI_IB_MINUS_50 = "mgi_ib_minus_50"  # Initial Balance -50%
    MGI_IB_MINUS_100 = "mgi_ib_minus_100" # Initial Balance -100%
    MGI_IB_MINUS_150 = "mgi_ib_minus_150" # Initial Balance -150%
    MGI_IB_MINUS_200 = "mgi_ib_minus_200" # Initial Balance -200%
    
    # Balance Area levels (from CSV, different from pivot BA)
    BALANCE_AREA_HIGH = "balance_area_high"
    BALANCE_AREA_MID = "balance_area_mid"
    BALANCE_AREA_LOW = "balance_area_low"
    
    # Manual pivot levels (entered daily at 9:30am) - ALL ⭐ ALL-STAR
    PIVOT = "pivot"                      # ⭐ ALL-STAR
    PIVOT_HIGH = "pivot_high"            # ⭐ ALL-STAR
    PIVOT_LOW = "pivot_low"              # ⭐ ALL-STAR
    PIVOT_BA_HIGH = "pivot_ba_high"      # ⭐ ALL-STAR
    PIVOT_BA_LOW = "pivot_ba_low"        # ⭐ ALL-STAR
    
    # Weekly levels (manual)
    WEEKLY_PIVOT = "weekly_pivot"        # ⭐ ALL-STAR


class LevelPriority(Enum):
    """Level priority classification."""
    ALL_STAR = "all_star"      # Highest priority - most reliable levels
    STANDARD = "standard"      # Standard priority
    REFERENCE = "reference"    # Reference only - lower priority


class LevelSource(Enum):
    """Source of the level data."""
    MOTIVEWAVE_CSV = "motivewave_csv"
    MANUAL_INPUT = "manual_input"
    CALCULATED = "calculated"


@dataclass
class LevelValidation:
    """Level validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class StructuralLevelsTable(Base):
    """Database table for structural levels."""
    __tablename__ = 'structural_levels_v2'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic level info
    symbol = Column(String(10), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    level_type = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    
    # Metadata
    source = Column(String(20), nullable=False)  # CSV, MANUAL, CALCULATED
    timeframe = Column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY
    priority = Column(String(20), default='standard')  # ALL_STAR, STANDARD, REFERENCE
    description = Column(Text)
    
    # Tracking data
    touches = Column(Integer, default=0)
    last_touch_time = Column(DateTime)
    first_touch_time = Column(DateTime)
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validation_errors = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    imported_by = Column(String(50))
    
    # Performance tracking
    hit_count = Column(Integer, default=0)  # Number of times price reacted at this level
    reaction_strength = Column(Float, default=0.0)  # Average reaction strength
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'trading_date'),
        Index('idx_symbol_date_type', 'symbol', 'trading_date', 'level_type'),
        Index('idx_symbol_date_priority', 'symbol', 'trading_date', 'priority'),
        Index('idx_date_source', 'trading_date', 'source'),
    )


class MotiveWaveCSVImporter:
    """Handles importing MotiveWave CSV exports with MGI columns."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
        # Map CSV column names to our level types with priority classification
        self.column_mapping = {
            # ⭐ ALL-STAR levels (highest priority)
            'MGI Wk-Op': ('mgi_wk_op', LevelPriority.ALL_STAR),
            'MGI PM-VAH': ('mgi_pm_vah', LevelPriority.ALL_STAR),
            'MGI PM-VAL': ('mgi_pm_val', LevelPriority.ALL_STAR),
            'MGI PW-VAH': ('mgi_pw_vah', LevelPriority.ALL_STAR),
            'MGI PW-VAL': ('mgi_pw_val', LevelPriority.ALL_STAR),
            'MGI: ONH': ('mgi_onh', LevelPriority.ALL_STAR),
            'MGI: ONL': ('mgi_onl', LevelPriority.ALL_STAR),
            
            # Standard priority levels
            'MGI MTH-Op': ('mgi_mth_op', LevelPriority.STANDARD),
            'MGI PM-Hi': ('mgi_pm_hi', LevelPriority.STANDARD),
            'MGI PM-Md': ('mgi_pm_md', LevelPriority.STANDARD),
            'MGI PM-Lo': ('mgi_pm_lo', LevelPriority.STANDARD),
            'MGI PM-Cl': ('mgi_pm_cl', LevelPriority.STANDARD),
            'MGI PW-Hi': ('mgi_pw_hi', LevelPriority.STANDARD),
            'MGI PW-Md': ('mgi_pw_md', LevelPriority.STANDARD),
            'MGI PW-Lo': ('mgi_pw_lo', LevelPriority.STANDARD),
            'MGI PW-Cl': ('mgi_pw_cl', LevelPriority.STANDARD),
            'MGI: RTHO': ('mgi_rtho', LevelPriority.STANDARD),
            'MGI: PDH': ('mgi_pdh', LevelPriority.STANDARD),
            'MGI: PDM': ('mgi_pdm', LevelPriority.STANDARD),
            'MGI: PDL': ('mgi_pdl', LevelPriority.STANDARD),
            'MGI: PRTH Close': ('mgi_prth_close', LevelPriority.STANDARD),
            'Balance Area High': ('balance_area_high', LevelPriority.ALL_STAR),
            'Balance Area Mid': ('balance_area_mid', LevelPriority.ALL_STAR),
            'Balance Area Low': ('balance_area_low', LevelPriority.ALL_STAR),
            
            # Reference priority levels
            'MGI: IB+200%': ('mgi_ib_plus_200', LevelPriority.REFERENCE),
            'MGI: IB+150%': ('mgi_ib_plus_150', LevelPriority.REFERENCE),
            'MGI: IB+100%': ('mgi_ib_plus_100', LevelPriority.REFERENCE),
            'MGI: IB+50%': ('mgi_ib_plus_50', LevelPriority.REFERENCE),
            'MGI: IBH': ('mgi_ibh', LevelPriority.REFERENCE),
            'MGI: IBM': ('mgi_ibm', LevelPriority.REFERENCE),
            'MGI: IBL': ('mgi_ibl', LevelPriority.REFERENCE),
            'MGI: IB-50%': ('mgi_ib_minus_50', LevelPriority.REFERENCE),
            'MGI: IB-100%': ('mgi_ib_minus_100', LevelPriority.REFERENCE),
            'MGI: IB-150%': ('mgi_ib_minus_150', LevelPriority.REFERENCE),
            'MGI: IB-200%': ('mgi_ib_minus_200', LevelPriority.REFERENCE),
        }
        
        # Manual levels are ALL-STAR by default
        self.manual_all_star_levels = {
            'pivot', 'pivot_high', 'pivot_low', 'pivot_ba_high', 'pivot_ba_low', 'weekly_pivot'
        }
        
    def parse_csv(self, csv_file_path: str, symbol: str = 'ES') -> Dict[str, Any]:
        """
        Parse MotiveWave CSV export with MGI columns.
        
        Expected CSV format has columns like:
        Date/Time, Open, High, Low, Close, Volume, Range, MGI Wk-Op, MGI MTH-Op, etc.
        
        We scan rows to find today's date with time >= 9:30am EST.
        """
        # CSV parsing always available with built-in csv module
        
        try:
            # Read CSV file
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                # Detect dialect
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                
                reader = csv.DictReader(csvfile, dialect=dialect)
                rows = list(reader)
            
            if not rows:
                raise ValueError("CSV file is empty")
            
            # Check if Date/Time column exists
            datetime_col = None
            for col in ['Date/Time', 'DateTime', 'Time', 'Date']:
                if col in rows[0].keys():
                    datetime_col = col
                    break
            
            if not datetime_col:
                raise ValueError("No Date/Time column found in CSV")
            
            # Get today's date
            today = date.today()
            
            # Filter for today's data and parse datetime
            today_rows = []
            for row in rows:
                try:
                    # Parse datetime string
                    dt_str = row[datetime_col]
                    if dt_str:
                        dt = datetime.strptime(dt_str, '%d/%m/%Y %H:%M:%S')
                        if dt.date() == today:
                            row['_parsed_datetime'] = dt
                            today_rows.append(row)
                except (ValueError, TypeError):
                    continue
            
            if not today_rows:
                return {
                    'success': False,
                    'error': f"No data found for today ({today})",
                    'file_path': csv_file_path
                }
            
            # Filter for times >= 9:30 AM EST
            market_open_time = time(9, 30)
            filtered_rows = []
            for row in today_rows:
                if row['_parsed_datetime'].time() >= market_open_time:
                    filtered_rows.append(row)
            
            if not filtered_rows:
                return {
                    'success': False,
                    'error': f"No data found for today after 9:30 AM",
                    'file_path': csv_file_path
                }
            
            # Get the first row that meets our criteria (earliest time >= 9:30)
            target_row = min(filtered_rows, key=lambda x: x['_parsed_datetime'])
            
            # Extract levels from MGI columns and Balance Area columns
            levels_data = []
            trading_date = target_row['_parsed_datetime'].date()
            
            for csv_col, (level_type, priority) in self.column_mapping.items():
                if csv_col in target_row:
                    try:
                        value = target_row[csv_col]
                        
                        # Skip empty/null values
                        if not value or value == '' or value == '0' or value == 0:
                            continue
                        
                        price = float(value)
                        
                        # Skip obviously invalid prices
                        if symbol == 'ES' and (price < 3000 or price > 8000):
                            logger.warning(f"Skipping invalid {symbol} price for {level_type}: {price}")
                            continue
                        elif symbol == 'NQ' and (price < 10000 or price > 30000):
                            logger.warning(f"Skipping invalid {symbol} price for {level_type}: {price}")
                            continue
                        
                        # Priority indicator for description
                        priority_symbol = "⭐ " if priority == LevelPriority.ALL_STAR else ""
                        
                        level_data = {
                            'level_type': level_type,
                            'price': price,
                            'symbol': symbol,
                            'trading_date': trading_date,
                            'source': LevelSource.MOTIVEWAVE_CSV.value,
                            'timeframe': 'DAILY',
                            'priority': priority.value,
                            'description': f"{priority_symbol}MGI {csv_col} from MotiveWave",
                            'import_time': target_row[datetime_col]
                        }
                        levels_data.append(level_data)
                        
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing {csv_col} value '{target_row[csv_col]}': {e}")
                        continue
            
            return {
                'success': True,
                'levels_count': len(levels_data),
                'levels_data': levels_data,
                'file_path': csv_file_path,
                'import_time': target_row[datetime_col].isoformat(),
                'row_index': target_row.name
            }
            
        except Exception as e:
            logger.error(f"Error parsing CSV {csv_file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': csv_file_path
            }
    
    def import_csv_levels(self, csv_file_path: str, symbol: str = 'ES', overwrite: bool = False) -> Dict[str, Any]:
        """
        Import levels from MotiveWave CSV.
        
        Args:
            csv_file_path: Path to CSV file
            symbol: Trading symbol (ES, NQ, etc.)
            overwrite: Whether to overwrite existing levels for the same date
            
        Returns:
            Import result dictionary
        """
        try:
            # Parse CSV for specific symbol
            parse_result = self.parse_csv(csv_file_path, symbol=symbol)
            if not parse_result['success']:
                return parse_result
            
            levels_data = parse_result['levels_data']
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for level_data in levels_data:
                try:
                    # Check if level already exists
                    existing = self.db_session.query(StructuralLevelsTable).filter_by(
                        symbol=level_data['symbol'],
                        trading_date=level_data['trading_date'],
                        level_type=level_data['level_type']
                    ).first()
                    
                    if existing and not overwrite:
                        skipped_count += 1
                        continue
                    
                    if existing and overwrite:
                        # Update existing
                        existing.price = level_data['price']
                        existing.priority = level_data.get('priority', 'standard')
                        existing.updated_at = datetime.utcnow()
                        existing.imported_by = 'csv_import_mgi'
                        existing.description = level_data.get('description', existing.description)
                    else:
                        # Create new
                        new_level = StructuralLevelsTable(
                            symbol=level_data['symbol'],
                            trading_date=level_data['trading_date'],
                            level_type=level_data['level_type'],
                            price=level_data['price'],
                            source=level_data['source'],
                            timeframe=level_data['timeframe'],
                            priority=level_data.get('priority', 'standard'),
                            description=level_data.get('description', f"MGI {level_data['level_type']} from MotiveWave"),
                            imported_by='csv_import_mgi'
                        )
                        self.db_session.add(new_level)
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Error importing {level_data}: {e}")
                    logger.error(f"Error importing level {level_data}: {e}")
            
            # Commit changes
            self.db_session.commit()
            
            return {
                'success': True,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors,
                'file_path': csv_file_path,
                'symbol': symbol,
                'import_time': parse_result.get('import_time'),
                'row_index': parse_result.get('row_index')
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error importing CSV levels: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': csv_file_path,
                'symbol': symbol
            }


class StructuralLevelsManagerV2:
    """Enhanced structural levels manager with database integration."""
    
    def __init__(self, database_url: str, watch_folder: Optional[str] = None):
        """
        Initialize the levels manager.
        
        Args:
            database_url: PostgreSQL database URL
            watch_folder: Folder to watch for CSV files
        """
        self.database_url = database_url
        self.watch_folder = watch_folder
        
        # Setup database
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize CSV importer
        self._csv_importer = None
        
        logger.info("StructuralLevelsManagerV2 initialized")
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def get_csv_importer(self) -> MotiveWaveCSVImporter:
        """Get CSV importer with current session."""
        if not self._csv_importer:
            session = self.get_session()
            self._csv_importer = MotiveWaveCSVImporter(session)
        return self._csv_importer
    
    def add_manual_levels(self, symbol: str, trading_date: date, 
                         levels: Dict[str, float], user: str = "manual") -> Dict[str, Any]:
        """
        Add manual pivot levels (entered at 9:30am daily).
        
        Args:
            symbol: Trading symbol (e.g., 'ES')
            trading_date: Trading date
            levels: Dictionary of level_type -> price
            user: User who entered the levels
            
        Returns:
            Result dictionary
        """
        try:
            with self.get_session() as session:
                imported_count = 0
                errors = []
                
                # Validate manual level types
                allowed_manual_types = {
                    'pivot', 'pivot_high', 'pivot_low', 
                    'pivot_ba_high', 'pivot_ba_low', 'weekly_pivot'
                }
                
                for level_type, price in levels.items():
                    if level_type not in allowed_manual_types:
                        errors.append(f"Invalid manual level type: {level_type}")
                        continue
                    
                    try:
                        # Check if level exists
                        existing = session.query(StructuralLevelsTable).filter_by(
                            symbol=symbol,
                            trading_date=trading_date,
                            level_type=level_type
                        ).first()
                        
                        if existing:
                            # Update existing
                            existing.price = price
                            existing.priority = 'all_star'  # Manual levels are always ALL-STAR
                            existing.updated_at = datetime.utcnow()
                            existing.imported_by = user
                        else:
                            # Create new
                            timeframe = 'WEEKLY' if level_type == 'weekly_pivot' else 'DAILY'
                            new_level = StructuralLevelsTable(
                                symbol=symbol,
                                trading_date=trading_date,
                                level_type=level_type,
                                price=price,
                                source=LevelSource.MANUAL_INPUT.value,
                                timeframe=timeframe,
                                priority='all_star',  # Manual levels are always ALL-STAR
                                description=f"⭐ Manual {level_type} level",
                                imported_by=user
                            )
                            session.add(new_level)
                        
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Error adding {level_type}: {e}")
                
                session.commit()
                
                # Validate level hierarchy
                validation = self.validate_level_hierarchy(symbol, trading_date)
                
                return {
                    'success': True,
                    'imported_count': imported_count,
                    'errors': errors,
                    'validation': validation
                }
                
        except Exception as e:
            logger.error(f"Error adding manual levels: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_level_hierarchy(self, symbol: str, trading_date: date) -> LevelValidation:
        """
        Validate that levels follow proper hierarchy.
        
        Args:
            symbol: Trading symbol
            trading_date: Trading date
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        try:
            with self.get_session() as session:
                # Get all levels for the date
                levels = session.query(StructuralLevelsTable).filter_by(
                    symbol=symbol,
                    trading_date=trading_date
                ).all()
                
                level_prices = {level.level_type: level.price for level in levels}
                
                # Validate pivot hierarchy: pivot_ba_high > pivot > pivot_ba_low
                if all(key in level_prices for key in ['pivot_ba_high', 'pivot', 'pivot_ba_low']):
                    if not (level_prices['pivot_ba_high'] > level_prices['pivot'] > level_prices['pivot_ba_low']):
                        errors.append("Pivot hierarchy invalid: BA High > Pivot > BA Low")
                
                # Validate overnight range
                if all(key in level_prices for key in ['overnight_high', 'overnight_low']):
                    if level_prices['overnight_high'] <= level_prices['overnight_low']:
                        errors.append("Overnight High must be > Overnight Low")
                
                # Validate value area
                if all(key in level_prices for key in ['vah', 'val']):
                    if level_prices['vah'] <= level_prices['val']:
                        errors.append("VAH must be > VAL")
                
                # Check for reasonable price ranges (ES-specific)
                if symbol == 'ES':
                    for level_type, price in level_prices.items():
                        if price < 3000 or price > 8000:
                            warnings.append(f"{level_type} price {price} seems unreasonable for ES")
                
                return LevelValidation(
                    is_valid=len(errors) == 0,
                    errors=errors,
                    warnings=warnings
                )
                
        except Exception as e:
            logger.error(f"Error validating levels: {e}")
            return LevelValidation(
                is_valid=False,
                errors=[f"Validation error: {e}"],
                warnings=[]
            )
    
    def get_levels_for_date(self, symbol: str, trading_date: date) -> Dict[str, float]:
        """
        Get all levels for a specific trading date.
        
        Args:
            symbol: Trading symbol
            trading_date: Trading date
            
        Returns:
            Dictionary of level_type -> price
        """
        try:
            with self.get_session() as session:
                levels = session.query(StructuralLevelsTable).filter_by(
                    symbol=symbol,
                    trading_date=trading_date
                ).all()
                
                return {level.level_type: level.price for level in levels}
                
        except Exception as e:
            logger.error(f"Error getting levels for date: {e}")
            return {}
    
    def get_nearby_levels(self, symbol: str, price: float, 
                         range_points: float = 5.0, trading_date: Optional[date] = None) -> List[Dict]:
        """
        Get levels near a specific price.
        
        Args:
            symbol: Trading symbol
            price: Reference price
            range_points: Range in points
            trading_date: Specific date (default: today)
            
        Returns:
            List of nearby levels with distance
        """
        if not trading_date:
            trading_date = date.today()
        
        try:
            with self.get_session() as session:
                levels = session.query(StructuralLevelsTable).filter_by(
                    symbol=symbol,
                    trading_date=trading_date
                ).all()
                
                nearby = []
                for level in levels:
                    distance = abs(level.price - price)
                    if distance <= range_points:
                        nearby.append({
                            'level_type': level.level_type,
                            'price': level.price,
                            'distance': distance,
                            'source': level.source,
                            'touches': level.touches
                        })
                
                # Sort by distance
                nearby.sort(key=lambda x: x['distance'])
                return nearby
                
        except Exception as e:
            logger.error(f"Error getting nearby levels: {e}")
            return []
    
    def record_level_touch(self, symbol: str, level_type: str, 
                          touch_time: datetime, trading_date: Optional[date] = None) -> bool:
        """
        Record when price touches a level.
        
        Args:
            symbol: Trading symbol
            level_type: Type of level touched
            touch_time: When the touch occurred
            trading_date: Trading date (default: today)
            
        Returns:
            Success status
        """
        if not trading_date:
            trading_date = date.today()
        
        try:
            with self.get_session() as session:
                level = session.query(StructuralLevelsTable).filter_by(
                    symbol=symbol,
                    trading_date=trading_date,
                    level_type=level_type
                ).first()
                
                if level:
                    level.touches += 1
                    level.last_touch_time = touch_time
                    if not level.first_touch_time:
                        level.first_touch_time = touch_time
                    level.updated_at = datetime.utcnow()
                    
                    session.commit()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error recording level touch: {e}")
            return False
    
    def get_all_star_levels(self, symbol: str, trading_date: Optional[date] = None) -> List[Dict]:
        """
        Get all ALL-STAR priority levels for a symbol.
        
        Args:
            symbol: Trading symbol
            trading_date: Trading date (default: today)
            
        Returns:
            List of ALL-STAR levels
        """
        if not trading_date:
            trading_date = date.today()
        
        try:
            with self.get_session() as session:
                levels = session.query(StructuralLevelsTable).filter_by(
                    symbol=symbol,
                    trading_date=trading_date,
                    priority='all_star'
                ).order_by(StructuralLevelsTable.price).all()
                
                return [{
                    'level_type': level.level_type,
                    'price': level.price,
                    'source': level.source,
                    'description': level.description,
                    'touches': level.touches,
                    'priority': level.priority
                } for level in levels]
                
        except Exception as e:
            logger.error(f"Error getting ALL-STAR levels: {e}")
            return []
    
    def get_levels_by_priority(self, symbol: str, priority: str, 
                              trading_date: Optional[date] = None) -> List[Dict]:
        """
        Get levels by priority classification.
        
        Args:
            symbol: Trading symbol
            priority: Priority level (all_star, standard, reference)
            trading_date: Trading date (default: today)
            
        Returns:
            List of levels for the specified priority
        """
        if not trading_date:
            trading_date = date.today()
        
        try:
            with self.get_session() as session:
                levels = session.query(StructuralLevelsTable).filter_by(
                    symbol=symbol,
                    trading_date=trading_date,
                    priority=priority
                ).order_by(StructuralLevelsTable.price).all()
                
                return [{
                    'level_type': level.level_type,
                    'price': level.price,
                    'source': level.source,
                    'description': level.description,
                    'touches': level.touches,
                    'priority': level.priority,
                    'timeframe': level.timeframe
                } for level in levels]
                
        except Exception as e:
            logger.error(f"Error getting {priority} levels: {e}")
            return []
    
    def scan_and_import_csv_files(self) -> List[Dict[str, Any]]:
        """
        Scan watch folder for new CSV files and import them.
        
        Returns:
            List of import results
        """
        if not self.watch_folder or not os.path.exists(self.watch_folder):
            return []
        
        results = []
        csv_files = list(Path(self.watch_folder).glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                # Check if file is new (modified in last 24 hours)
                file_mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
                if datetime.now() - file_mtime > timedelta(hours=24):
                    continue
                
                # Import the file
                with self.get_session() as session:
                    importer = MotiveWaveCSVImporter(session)
                    result = importer.import_csv_levels(str(csv_file))
                    results.append(result)
                    
                    # Move processed file to processed folder
                    if result['success']:
                        processed_folder = Path(self.watch_folder) / "processed"
                        processed_folder.mkdir(exist_ok=True)
                        processed_file = processed_folder / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{csv_file.name}"
                        csv_file.rename(processed_file)
                        
            except Exception as e:
                logger.error(f"Error processing CSV file {csv_file}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'file_path': str(csv_file)
                })
        
        return results
    
    def get_daily_completeness_status(self, symbol: str, trading_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Check completeness of daily levels.
        
        Args:
            symbol: Trading symbol
            trading_date: Trading date (default: today)
            
        Returns:
            Completeness status
        """
        if not trading_date:
            trading_date = date.today()
        
        try:
            with self.get_session() as session:
                levels = session.query(StructuralLevelsTable).filter_by(
                    symbol=symbol,
                    trading_date=trading_date
                ).all()
                
                existing_types = {level.level_type for level in levels}
                
                # Required MGI levels (from MotiveWave CSV after 9:30am) - focusing on ALL-STAR levels
                required_mgi = {
                    'mgi_onh',      # Overnight High ⭐ ALL-STAR
                    'mgi_onl',      # Overnight Low ⭐ ALL-STAR
                    'mgi_pm_vah',   # Previous Month VAH ⭐ ALL-STAR
                    'mgi_pm_val',   # Previous Month VAL ⭐ ALL-STAR
                    'mgi_pw_vah',   # Previous Week VAH ⭐ ALL-STAR
                    'mgi_pw_val',   # Previous Week VAL ⭐ ALL-STAR
                    'mgi_wk_op',    # Week Open ⭐ ALL-STAR
                    'balance_area_high',  # Balance Area High
                    'balance_area_low',   # Balance Area Low
                }
                
                # Required manual levels (entered at 9:30am)
                required_manual = {
                    'pivot', 'pivot_high', 'pivot_low', 'pivot_ba_high', 'pivot_ba_low'
                }
                
                mgi_complete = required_mgi.issubset(existing_types)
                manual_complete = required_manual.issubset(existing_types)
                
                # Count MGI vs manual levels
                mgi_levels = [l for l in levels if l.source == LevelSource.MOTIVEWAVE_CSV.value]
                manual_levels = [l for l in levels if l.source == LevelSource.MANUAL_INPUT.value]
                
                return {
                    'symbol': symbol,
                    'trading_date': trading_date.isoformat(),
                    'csv_complete': mgi_complete,  # Still called csv_complete for compatibility
                    'manual_complete': manual_complete,
                    'overall_complete': mgi_complete and manual_complete,
                    'missing_csv': list(required_mgi - existing_types),
                    'missing_manual': list(required_manual - existing_types),
                    'total_levels': len(levels),
                    'mgi_levels_count': len(mgi_levels),
                    'manual_levels_count': len(manual_levels),
                    'required_mgi': list(required_mgi),
                    'required_manual': list(required_manual)
                }
                
        except Exception as e:
            logger.error(f"Error checking completeness: {e}")
            return {
                'symbol': symbol,
                'trading_date': trading_date.isoformat() if trading_date else None,
                'csv_complete': False,
                'manual_complete': False,
                'overall_complete': False,
                'error': str(e)
            }


# Utility functions for easy integration
def create_levels_manager(database_url: str, watch_folder: Optional[str] = None) -> StructuralLevelsManagerV2:
    """Create and return a levels manager instance."""
    return StructuralLevelsManagerV2(database_url, watch_folder)


def import_motivewave_csv(database_url: str, csv_file_path: str, overwrite: bool = False) -> Dict[str, Any]:
    """Quick function to import a MotiveWave CSV file."""
    manager = StructuralLevelsManagerV2(database_url)
    with manager.get_session() as session:
        importer = MotiveWaveCSVImporter(session)
        return importer.import_csv_levels(csv_file_path, overwrite)


def add_daily_manual_levels(database_url: str, symbol: str, levels: Dict[str, float], 
                           trading_date: Optional[date] = None) -> Dict[str, Any]:
    """Quick function to add daily manual levels."""
    if not trading_date:
        trading_date = date.today()
    
    manager = StructuralLevelsManagerV2(database_url)
    return manager.add_manual_levels(symbol, trading_date, levels)


if __name__ == "__main__":
    # Example usage
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost/xfgv2')
    WATCH_FOLDER = os.environ.get('CSV_WATCH_FOLDER', '/path/to/csv/folder')
    
    # Create manager
    manager = StructuralLevelsManagerV2(DATABASE_URL, WATCH_FOLDER)
    
    # Example: Add manual levels for today
    manual_levels = {
        'pivot': 5825.75,
        'pivot_high': 5850.25,
        'pivot_low': 5800.50,
        'pivot_ba_high': 5875.00,
        'pivot_ba_low': 5775.25
    }
    
    result = manager.add_manual_levels('ES', date.today(), manual_levels)
    print(f"Manual levels result: {result}")
    
    # Example: Check completeness
    status = manager.get_daily_completeness_status('ES')
    print(f"Completeness status: {status}")