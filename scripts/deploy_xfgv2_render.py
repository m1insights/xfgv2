"""
xFGv2 Deployment Script for Render
Sets up the CSV monitoring service and web interface on Render.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from csv_file_monitor import create_monitor_from_env
from structural_levels_v2 import StructuralLevelsManagerV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RenderDeploymentManager:
    """Manages deployment tasks for Render environment."""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL', '')
        self.csv_watch_folder = os.environ.get('CSV_WATCH_FOLDER', '/tmp/csv_watch')
        self.service_type = os.environ.get('RENDER_SERVICE_TYPE', 'web')
        
        # Ensure database URL is PostgreSQL format
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
    
    def setup_environment(self):
        """Set up the deployment environment."""
        logger.info("Setting up xFGv2 deployment environment...")
        
        # Create necessary directories
        directories = [
            self.csv_watch_folder,
            os.path.join(self.csv_watch_folder, 'processed'),
            os.path.join(self.csv_watch_folder, 'errors'),
            '/tmp/logs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Check database connection
        if self.database_url:
            try:
                levels_manager = StructuralLevelsManagerV2(self.database_url)
                with levels_manager.get_session() as session:
                    # Test connection
                    session.execute("SELECT 1")
                logger.info("Database connection verified")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
        else:
            logger.warning("No database URL configured")
        
        logger.info("Environment setup completed")
    
    def initialize_database(self):
        """Initialize database tables if needed."""
        logger.info("Initializing database...")
        
        try:
            from structural_levels_v2 import Base
            from sqlalchemy import create_engine
            
            engine = create_engine(self.database_url)
            Base.metadata.create_all(engine)
            logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def start_csv_monitor_service(self):
        """Start the CSV file monitoring service."""
        logger.info("Starting CSV file monitoring service...")
        
        try:
            monitor = create_monitor_from_env()
            
            # Run initial scan
            logger.info("Running initial CSV scan...")
            results = monitor.scan_and_process()
            if results:
                logger.info(f"Initial scan processed {len(results)} files")
            
            # Start monitoring loop
            logger.info("Starting monitoring loop...")
            monitor.start_monitoring()
            
        except Exception as e:
            logger.error(f"CSV monitor service failed: {e}")
            raise
    
    def start_web_service(self):
        """Start the web interface service."""
        logger.info("Starting web interface service...")
        
        try:
            # Import the web app
            from web_app_levels_v2 import app
            
            # Get port from environment
            port = int(os.environ.get('PORT', 5002))
            
            # Run the Flask app
            app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                threaded=True
            )
            
        except Exception as e:
            logger.error(f"Web service failed: {e}")
            raise
    
    def run_health_check(self):
        """Run health check for the deployment."""
        logger.info("Running deployment health check...")
        
        checks = []
        
        # Check database
        try:
            levels_manager = StructuralLevelsManagerV2(self.database_url)
            with levels_manager.get_session() as session:
                session.execute("SELECT 1")
            checks.append(("Database", True, "Connected"))
        except Exception as e:
            checks.append(("Database", False, str(e)))
        
        # Check CSV folder
        try:
            csv_folder_exists = os.path.exists(self.csv_watch_folder)
            checks.append(("CSV Folder", csv_folder_exists, self.csv_watch_folder))
        except Exception as e:
            checks.append(("CSV Folder", False, str(e)))
        
        # Check environment variables
        required_vars = ['DATABASE_URL']
        for var in required_vars:
            value = os.environ.get(var)
            checks.append((f"Env: {var}", bool(value), "Set" if value else "Missing"))
        
        # Print results
        logger.info("Health Check Results:")
        all_passed = True
        for check_name, passed, details in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"  {status} {check_name}: {details}")
            if not passed:
                all_passed = False
        
        if all_passed:
            logger.info("All health checks passed!")
        else:
            logger.error("Some health checks failed!")
            
        return all_passed
    
    def deploy(self):
        """Run the full deployment process."""
        logger.info("Starting xFGv2 deployment on Render...")
        
        try:
            # Setup environment
            self.setup_environment()
            
            # Initialize database
            self.initialize_database()
            
            # Run health check
            if not self.run_health_check():
                logger.error("Health check failed, aborting deployment")
                return False
            
            # Determine service type and start appropriate service
            if self.service_type == 'web':
                logger.info("Starting as web service...")
                self.start_web_service()
            elif self.service_type == 'worker':
                logger.info("Starting as background worker service...")
                self.start_csv_monitor_service()
            else:
                logger.info("Starting as combined service...")
                # For combined service, we'd need to run both in separate threads
                import threading
                
                # Start CSV monitor in background thread
                monitor_thread = threading.Thread(
                    target=self.start_csv_monitor_service,
                    daemon=True
                )
                monitor_thread.start()
                
                # Start web service in main thread
                self.start_web_service()
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False


def create_render_yaml():
    """Create render.yaml configuration file."""
    render_config = """# Render deployment configuration for xFGv2
services:
  # Web service for levels management interface
  - type: web
    name: xfgv2-web
    env: python
    plan: starter
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python scripts/deploy_xfgv2_render.py"
    envVars:
      - key: RENDER_SERVICE_TYPE
        value: web
      - key: CSV_WATCH_FOLDER
        value: /tmp/csv_watch
      - key: PYTHON_VERSION
        value: 3.11.0
    
  # Background worker for CSV monitoring
  - type: worker
    name: xfgv2-monitor
    env: python
    plan: starter
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python scripts/deploy_xfgv2_render.py"
    envVars:
      - key: RENDER_SERVICE_TYPE
        value: worker
      - key: CSV_WATCH_FOLDER
        value: /tmp/csv_watch
      - key: CSV_CHECK_INTERVAL
        value: 5
      - key: PYTHON_VERSION
        value: 3.11.0

databases:
  - name: xfgv2-db
    databaseName: xfgv2
    user: xfgv2_user
    plan: starter

envVarGroups:
  - name: xfgv2-config
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: WEB_USERNAME
        value: admin
      - key: WEB_PASSWORD
        generateValue: true
      - key: ALLOWED_SYMBOLS
        value: ES,NQ
"""
    
    with open('render.yaml', 'w') as f:
        f.write(render_config)
    
    logger.info("Created render.yaml configuration file")


def main():
    """Main deployment entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='xFGv2 Render Deployment')
    parser.add_argument('--create-config', action='store_true',
                       help='Create render.yaml configuration file')
    parser.add_argument('--health-check', action='store_true',
                       help='Run health check only')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_render_yaml()
        return
    
    # Create deployment manager
    deployment = RenderDeploymentManager()
    
    if args.health_check:
        success = deployment.run_health_check()
        sys.exit(0 if success else 1)
    
    # Run full deployment
    success = deployment.deploy()
    
    if success:
        logger.info("xFGv2 deployment completed successfully!")
    else:
        logger.error("xFGv2 deployment failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()