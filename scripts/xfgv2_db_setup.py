"""
xFGv2 Database Setup and Management Script
Creates and manages the PostgreSQL database for xFGv2.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, date
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from structural_levels_v2 import Base, StructuralLevelsTable, LevelType, LevelSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XFGv2DatabaseManager:
    """Manages xFGv2 database operations."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        if database_url.startswith('postgres://'):
            self.database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(self.database_url)
        logger.info(f"Database manager initialized for: {self.database_url[:30]}...")
    
    def create_database(self):
        """Create all database tables."""
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False
    
    def drop_database(self):
        """Drop all database tables."""
        try:
            logger.warning("Dropping all database tables...")
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
            return True
        except Exception as e:
            logger.error(f"Error dropping database: {e}")
            return False
    
    def reset_database(self):
        """Drop and recreate all tables."""
        logger.info("Resetting database...")
        if self.drop_database() and self.create_database():
            logger.info("Database reset successfully")
            return True
        return False
    
    def check_connection(self):
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_table_info(self):
        """Get information about database tables."""
        try:
            with self.engine.connect() as conn:
                # Check if tables exist
                tables_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE '%structural_levels%'
                """)
                
                tables = conn.execute(tables_query).fetchall()
                
                info = {
                    'tables': [row[0] for row in tables],
                    'total_tables': len(tables)
                }
                
                # Get row counts if tables exist
                if 'structural_levels_v2' in info['tables']:
                    count_query = text("SELECT COUNT(*) FROM structural_levels_v2")
                    count = conn.execute(count_query).scalar()
                    info['structural_levels_count'] = count
                
                return info
                
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {}
    
    def add_sample_data(self):
        """Add sample structural levels data."""
        from sqlalchemy.orm import sessionmaker
        from datetime import date
        
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            
            # Sample ES levels for today
            today = date.today()
            sample_levels = [
                # CSV imported levels
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='overnight_high',
                    price=5850.25,
                    source=LevelSource.MOTIVEWAVE_CSV.value,
                    timeframe='DAILY',
                    description='Sample overnight high from MotiveWave'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='overnight_low',
                    price=5825.50,
                    source=LevelSource.MOTIVEWAVE_CSV.value,
                    timeframe='DAILY',
                    description='Sample overnight low from MotiveWave'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='vwap',
                    price=5837.75,
                    source=LevelSource.MOTIVEWAVE_CSV.value,
                    timeframe='DAILY',
                    description='Sample VWAP from MotiveWave'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='vah',
                    price=5845.00,
                    source=LevelSource.MOTIVEWAVE_CSV.value,
                    timeframe='DAILY',
                    description='Sample VAH from MotiveWave'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='val',
                    price=5830.50,
                    source=LevelSource.MOTIVEWAVE_CSV.value,
                    timeframe='DAILY',
                    description='Sample VAL from MotiveWave'
                ),
                
                # Manual pivot levels
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='pivot',
                    price=5838.00,
                    source=LevelSource.MANUAL_INPUT.value,
                    timeframe='DAILY',
                    description='Sample manual pivot level'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='pivot_high',
                    price=5855.25,
                    source=LevelSource.MANUAL_INPUT.value,
                    timeframe='DAILY',
                    description='Sample manual pivot high'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='pivot_low',
                    price=5820.75,
                    source=LevelSource.MANUAL_INPUT.value,
                    timeframe='DAILY',
                    description='Sample manual pivot low'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='pivot_ba_high',
                    price=5870.00,
                    source=LevelSource.MANUAL_INPUT.value,
                    timeframe='DAILY',
                    description='Sample manual pivot balance area high'
                ),
                StructuralLevelsTable(
                    symbol='ES',
                    trading_date=today,
                    level_type='pivot_ba_low',
                    price=5805.50,
                    source=LevelSource.MANUAL_INPUT.value,
                    timeframe='DAILY',
                    description='Sample manual pivot balance area low'
                ),
            ]
            
            # Add NQ sample data too
            nq_levels = [
                StructuralLevelsTable(
                    symbol='NQ',
                    trading_date=today,
                    level_type='overnight_high',
                    price=20150.25,
                    source=LevelSource.MOTIVEWAVE_CSV.value,
                    timeframe='DAILY',
                    description='Sample NQ overnight high'
                ),
                StructuralLevelsTable(
                    symbol='NQ',
                    trading_date=today,
                    level_type='pivot',
                    price=20100.00,
                    source=LevelSource.MANUAL_INPUT.value,
                    timeframe='DAILY',
                    description='Sample NQ manual pivot'
                ),
            ]
            
            # Add all sample data
            for level in sample_levels + nq_levels:
                session.add(level)
            
            session.commit()
            session.close()
            
            logger.info(f"Added {len(sample_levels + nq_levels)} sample levels")
            return True
            
        except Exception as e:
            logger.error(f"Error adding sample data: {e}")
            return False
    
    def backup_database(self, backup_file: str):
        """Create a backup of the database."""
        try:
            import subprocess
            
            # Extract connection details from URL
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', backup_file,
                '--no-password'
            ]
            
            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"Database backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def restore_database(self, backup_file: str):
        """Restore database from backup."""
        try:
            import subprocess
            
            # Extract connection details from URL
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            # Build psql command
            cmd = [
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', backup_file,
                '--no-password'
            ]
            
            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"Database restored from: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='xFGv2 Database Management')
    parser.add_argument('--database-url', 
                       default=os.environ.get('DATABASE_URL', ''),
                       help='PostgreSQL database URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create database tables')
    
    # Drop command
    drop_parser = subparsers.add_parser('drop', help='Drop database tables')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset database (drop and create)')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check database connection')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show database information')
    
    # Sample data command
    sample_parser = subparsers.add_parser('sample', help='Add sample data')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup database')
    backup_parser.add_argument('--file', required=True, help='Backup file path')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database')
    restore_parser.add_argument('--file', required=True, help='Backup file path')
    
    args = parser.parse_args()
    
    if not args.database_url:
        logger.error("Database URL is required. Set DATABASE_URL environment variable or use --database-url")
        sys.exit(1)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create database manager
    db_manager = XFGv2DatabaseManager(args.database_url)
    
    # Execute command
    if args.command == 'create':
        success = db_manager.create_database()
    elif args.command == 'drop':
        success = db_manager.drop_database()
    elif args.command == 'reset':
        success = db_manager.reset_database()
    elif args.command == 'check':
        success = db_manager.check_connection()
    elif args.command == 'info':
        info = db_manager.get_table_info()
        print(f"Database Info: {info}")
        success = True
    elif args.command == 'sample':
        success = db_manager.add_sample_data()
    elif args.command == 'backup':
        success = db_manager.backup_database(args.file)
    elif args.command == 'restore':
        success = db_manager.restore_database(args.file)
    else:
        logger.error(f"Unknown command: {args.command}")
        success = False
    
    if success:
        logger.info(f"Command '{args.command}' completed successfully")
        sys.exit(0)
    else:
        logger.error(f"Command '{args.command}' failed")
        sys.exit(1)


if __name__ == '__main__':
    main()